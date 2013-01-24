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

import sys
import os
dirname = os.path.dirname(__file__)
sys.path.append(os.path.join(dirname, "../.."))
from new_recv.shared.config_to_dict import config_to_dict
import new_recv.shared.socket_functions as socket_functions

#   Detect root, error if not
if os.getuid() != 0:
    raise Exception('Must run as root!')

server_settings = config_to_dict().do('settings.ini')

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
        }
        server = socket_functions.custom_server(SOCKET_ARGS)
        server.run()
    
    def rip_track(self, out_path,disc_id,track_ids):
        if not os.path.isdir(out_path):
            os.mkdir(out_path)
        ripped_tracks = {'disc_id':  disc_id,
                         'cmd'   :   'rip',}
        for track_id in track_ids.split(','):
            ripped_tracks[track_id] = '1 titles saved.' in subprocess.check_output([u'makemkvcon',u'--noscan',u'mkv',u'dev:%s'%disc_id,u'%s'%track_id,out_path])
        return ripped_tracks

    def to_iso(self, out_path,disc_id):
        if not os.path.isdir(out_path):
            os.mkdir(out_path)
        rip_output = {
            'disc_id':  disc_id,
            'out_file': u'%s.iso'%out_path,
            'cmd'   :   'iso',
        }
        decrypt_out = subprocess.check_output([u'makemkvcon', u'--noscan', u'backup' ,u'--decrypt', u'disc:%s'%self.drive_map[disc_id], out_path])   #< to folder, decrypt
        print 'DECRYPT:\n'+decrypt_out+'\n\n'
        iso_out = subprocess.check_output([u'mkisofs', u'-J', u'-r',  u'-iso-level', u'3', u'-udf', u'-allow-limited-size', u'-o', rip_output['out_file'], out_path])  #<  Make iso
        print 'ISO:\n'+iso_out+'\n\n'
        shutil.rmtree(out_path) #<  RM disc tree
        return rip_output   #< Exceptions from failures should cause this to not get hit on fail?

    def disc_info(self, disc_id,thread_id=None):
        info_out = {
            'disc'  :   {},
            'tracks':   {},
            'disc_id':  disc_id,
            'cmd'   :   'disc_info',
        }
        disc_info = subprocess.check_output(['makemkvcon','--noscan','-r','info','dev:%s' % disc_id])
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
        return info_out
    
    def scan_drives(self):
        ##  Scan drives, return info
        #   @return Dict    Dict keyed by drive index, value is movie name
        drives = {'cmd'   :   'scan_drives',}
        self.drive_map = {}
        try:
            drive_scan = subprocess.check_output(['makemkvcon','-r','info'])
        except subprocess.CalledProcessError as e:
            drive_scan = e.output
        for line in drive_scan.split(make_mkv.NEWLINE_CHAR):
            if line[:4] == 'DRV:' and '/dev/' in line:  #<  DRV to make sure it's drive output, /dev to make sure that there is a drive
                _info = make_mkv.COL_PATTERN.split(line)
                drive_location = _info[-2].replace('"','')
                drives[drive_location] = _info[-4].replace('"','') if _info[-4] != '""' else None#<  [Drive Index] = Movie Name
                self.drive_map[drive_location] = _info[1].split(':')[1] #<    Index the drive location to makemkv's drive ID
        return  drives
    
    def get_disc_drives():
        ##  Scan for DVD/BD drives w/o using MakeMkv
        #   @return Dict keyed by drive index (as MakeMkv recognizes them - /dev/sr#)
        drives = {}
    
if __name__ == '__main__':
    #from pprint import pprint
    #pprint(make_mkv.disc_info(1))
    make_mkv()