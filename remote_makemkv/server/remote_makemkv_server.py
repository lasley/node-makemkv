#!/usr/bin/env python
##  Socket server for makemkvcon
#         
#   makemkvcon server
#    
#   @author     David Lasley, dave -at- dlasley -dot- net
#   @website    http://code.google.com/p/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id$
#
#   @requires-binary   makemkvcon, mkisofs
import subprocess
import re
import json
import shutil
import logging
import sys
import os
dirname = os.path.dirname(__file__)
sys.path.append(os.path.join(dirname, "../.."))
from remote_makemkv import MAKEMKVCON_PATH
from remote_makemkv.shared.config_to_dict import config_to_dict
import remote_makemkv.shared.socket_functions as socket_functions

#   Detect root, error if not (ignore on Windows?)
try:
    if os.getuid() != 0:
        raise Exception('Must run as root!')
except AttributeError:
    pass #< Windows

server_settings = config_to_dict().do(os.path.join(dirname,'settings.ini'))

class make_mkv(object):
    NEWLINE_CHAR = '\n'
    SELECTION_PROFILE = server_settings['selection_profile']
    ATTRIBUTE_IDS = server_settings['attibute_ids']
    COL_PATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
    def __init__(self, save_path=None):
        self.save_to = save_path
        SOCKET_ARGS = {
            "rip"       :   self.rip_track,
            "disc_info" :   self.disc_info,
            "scan_drives":  self.scan_drives,
            'iso'       :   self.to_iso,
            'get_busy'  :   self.get_busy,
        }
        server = socket_functions.custom_server(SOCKET_ARGS,['get_busy',])
        self.busy_devices = {}
        #server.SHORT_TERM_MEMORY = {'all':True}
        server.run()
    
    def get_busy(self,disc_id=None,busy=False):
        if disc_id is None:
            return {
                'cmd'   :   'get_busy',
                'val'   :   self.busy_devices
            }
        else:
            try:
                if busy == self.busy_devices[disc_id]:
                    logging.debug( '%s - %s / %s' % (disc_id, busy, self.busy_devices[disc_id]) ) 
                    return False
            except KeyError:
                pass
            logging.debug('Setting %s to %s' % (disc_id,str(busy)))
            self.busy_devices[disc_id] = busy
            return True
    
    def rip_track(self, out_path,disc_id,track_ids):
        if self.get_busy(disc_id, True):
            if not os.path.isdir(out_path):
                os.mkdir(out_path)
            ripped_tracks = {'disc_id':  disc_id,
                             'cmd'   :   'rip',}
            for track_id in track_ids.split(','):
                ripped_tracks[track_id] = '1 titles saved.' in subprocess.check_output([MAKEMKVCON_PATH,u'--noscan',u'mkv',u'--cache=256',u'dev:%s'%disc_id,u'%s'%track_id,out_path])
            self.get_busy(disc_id)
        #else:
        #    for track_id in track_ids.split(','):
        #        
            return ripped_tracks

    def to_iso(self, out_path,disc_id):
        if self.get_busy(disc_id, True):
            if not os.path.isdir(out_path):
                os.mkdir(out_path)
            rip_output = {
                'disc_id':  disc_id,
                'out_file': u'%s.iso'%out_path,
                'cmd'   :   'iso',
            }
            decrypt_out = subprocess.check_output([MAKEMKVCON_PATH, u'--noscan', u'backup' ,u'--cache=256' ,u'--decrypt', u'disc:%s'%self.drive_map[disc_id], out_path])   #< to folder, decrypt
            print 'DECRYPT:\n'+decrypt_out+'\n\n'
            iso_out = subprocess.check_output([u'mkisofs', u'-J', u'-r',  u'-iso-level', u'3', u'-udf', u'-allow-limited-size', u'-o', rip_output['out_file'], out_path])  #<  Make iso
            print 'ISO:\n'+iso_out+'\n\n'
            shutil.rmtree(out_path) #<  RM disc tree
            self.get_busy(disc_id)
            return rip_output   #< Exceptions from failures should cause this to not get hit on fail?

    def disc_info(self, disc_id,thread_id=None):
        if self.get_busy(disc_id, True):
            info_out = {
                'disc'  :   {},
                'tracks':   {},
                'disc_id':  disc_id,
                'cmd'   :   'disc_info',
            }
            try:
                disc_info = subprocess.check_output([MAKEMKVCON_PATH,'--noscan','-r','info','dev:%s' % disc_id])
            except subprocess.CalledProcessError as e:
                exit(e.output)
            track_id = -1
            for line in disc_info.split(make_mkv.NEWLINE_CHAR):
                split_line = make_mkv.COL_PATTERN.split(line)[1::2]
                if len(split_line) > 1 and split_line[0] != 'TCOUNT':
                    if line[0] == 'C':  #<  Disc Info
                        info_out['disc'][make_mkv.ATTRIBUTE_IDS[split_line[0].split(':')[-1]]] = split_line[-1].replace('"','')
                    else:
                        if line[0] == 'T':
                            track_id = split_line[0].split(':')[-1]
                            try:    #<  If new track_id, dim var
                                track_info = info_out['tracks'][track_id]
                            except KeyError:
                                track_info = info_out['tracks'][track_id] = {'cnts':{'Subtitles':0,'Video':0,'Audio':0}}
                            track_info[make_mkv.ATTRIBUTE_IDS[split_line[1]]] = split_line[-1].replace('"','')
                        if line[0] == 'S':
                            track_part_id = split_line[1]
                            try:    #<  If new track_id, dim var
                                info_out['tracks'][track_id]['track_parts']
                            except KeyError:
                                info_out['tracks'][track_id]['track_parts'] = {}
                            try:    #<  If new track_id, dim var
                                track_info = info_out['tracks'][track_id]['track_parts'][track_part_id]
                            except KeyError:
                                track_info = info_out['tracks'][track_id]['track_parts'][track_part_id] = {}
                            track_info[make_mkv.ATTRIBUTE_IDS[split_line[2]]] = split_line[-1].replace('"','')
            #   Count the track parts
            for track_id,track_info in info_out['tracks'].iteritems():
                for part_id, track_part in track_info['track_parts'].iteritems():
                    try:
                        info_out['tracks'][track_id]['cnts'][track_part['Type']] += 1
                    except KeyError:    #<  Type not avail, should be good to ignore?
                        pass
            self.get_busy(disc_id)
            return info_out
    
    def scan_drives(self):
        ##  Scan drives, return info
        #   @return Dict    Dict keyed by drive index, value is movie name
        if self.get_busy('all', True):
            drives = {'cmd'   :   'scan_drives',}
            self.drive_map = {}
            try:
                drive_scan = subprocess.check_output([MAKEMKVCON_PATH,'-r','info'])
            except subprocess.CalledProcessError as e:
                drive_scan = e.output
            for line in drive_scan.split(make_mkv.NEWLINE_CHAR):
                if line[:4] == 'DRV:' and '/dev/' in line:  #<  DRV to make sure it's drive output, /dev to make sure that there is a drive
                    _info = make_mkv.COL_PATTERN.split(line)
                    drive_location = _info[-2].replace('"','')
                    drives[drive_location] = _info[-4].replace('"','') if _info[-4] != '""' else None#<  [Drive Index] = Movie Name
                    self.drive_map[drive_location] = _info[1].split(':')[1] #<    Index the drive location to makemkv's drive ID
            self.get_busy('all', False)
            return  drives
    
    def get_disc_drives():
        ##  Scan for DVD/BD drives w/o using MakeMkv
        #   @return Dict keyed by drive index (as MakeMkv recognizes them - /dev/sr#)
        drives = {}
    
    
if __name__ == '__main__':
    #from pprint import pprint
    #pprint(make_mkv.disc_info(1))
    make_mkv()