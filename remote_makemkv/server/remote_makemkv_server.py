#!/usr/bin/env python
##  Socket server for makemkvcon
#         
#   makemkvcon server
#    
#   @author     David Lasley, dave -at- dlasley -dot- net
#   @website    http://code.google.com/p/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id: remote_makemkv_server.py 102 2013-02-06 01:27:56Z dave@dlasley.net $
#
#   @requires-binary   makemkvcon, mkisofs
import subprocess
import re
import json
import shutil
import logging
import sys
import os
import md5
dirname = os.path.dirname(__file__)
sys.path.append(os.path.join(dirname, "../.."))
from remote_makemkv import MAKEMKVCON_PATH, HOST, PORT
from remote_makemkv.shared.config_to_dict import config_to_dict
from remote_makemkv.shared.custom_socket import socket_functions

#   Detect root, error if not (ignore on Windows?)
try:
    if os.getuid() != 0:
        raise Exception('Must run as root!')
except AttributeError:
    pass #< Windows

SERVER_SETTINGS = config_to_dict().do(os.path.join(dirname,'settings.ini'))

class make_mkv(object):
    NEWLINE_CHAR = '\n'
    SELECTION_PROFILE = SERVER_SETTINGS['selection_profile']
    ATTRIBUTE_IDS = SERVER_SETTINGS['attibute_ids']
    COL_PATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
    RESERVED_CHAR_MAP = { '/':'-', '\\':'-', '?':' ', '%':' ', '*':' ',
                         ':':'-', '|':'-', '"':' ', '<':' ', '>':' ', }
    def __init__(self, save_path=None, ):
        self.save_to = save_path
        SOCKET_ARGS = {
            "rip"       :   self.rip_track,
            "disc_info" :   self.disc_info,
            "scan_drives":  self.scan_drives,
            'iso'       :   self.to_iso,
            'get_busy'  :   self.get_busy,
        }
        self.server = socket_functions.custom_server(
            HOST, PORT, SOCKET_ARGS,['get_busy',])
        self.busy_devices = {}
        self.server.run()
    
    def get_busy(self, disc_id=None, busy=False, ):
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
    
    def rip_track(self, out_path, disc_id, track_ids, ):
        if self.get_busy(disc_id, True):
            try:
                ripped_tracks = {'disc_id':  disc_id,
                                 'cmd'   :   'rip',}
                
                out_path = self._sanitize_filename(out_path)
                if not os.path.isdir(out_path):
                    os.mkdir(out_path)
                
                for track_id in track_ids.split(','):
                    ripped_tracks[track_id] = '1 titles saved.' in subprocess.check_output(
                        [MAKEMKVCON_PATH, u'-r', u'--noscan', u'mkv', u'--cache=256',
                         u'dev:%s' % disc_id, u'%s' % track_id, out_path ])
                    
                for _file in os.listdir(out_path):
                    track_num = re.findall('t(itle|rack)?([0-9][0-9]?).mkv$', _file)
                    logging.debug(track_num)
                    new_name = os.path.join(out_path, '%s_t%02d.mkv' % (
                        os.path.basename(out_path), int(track_num[-1][-1])))
                    logging.debug('Renaming "%s" to "%s"' % (_file, new_name))
                    os.rename(os.path.join(out_path, _file), new_name)  
            except OSError:
                for track_id in track_ids.split(','):
                    ripped_tracks[track_id] = False
            
            self.get_busy(disc_id)
            return ripped_tracks

    def to_iso(self, out_path, disc_id, ):
        if self.get_busy(disc_id, True):
            
            out_path = self._sanitize_filename(out_path)
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
            return rip_output

    def disc_info(self, disc_id, thread_id=None, ):
        if self.get_busy(disc_id, True):
            info_out = {
                'disc'  :   {},
                'tracks':   {},
                'disc_id':  disc_id,
                'cmd'   :   'disc_info',
            }
            try:
                disc_info = subprocess.check_output([
                    MAKEMKVCON_PATH, '--noscan', '-r',
                    'info', 'dev:%s' % disc_id,
                    ])
            except subprocess.CalledProcessError as e:
                logging.error(e.output)
                raise
            track_id = -1
            for line in disc_info.split(make_mkv.NEWLINE_CHAR):
                split_line = make_mkv.COL_PATTERN.split(line)[1::2]
                if len(split_line) > 1 and split_line[0] != 'TCOUNT':
                    if line[0] == 'C':  #<  Disc Info
                        try:
                            info_out['disc'][make_mkv.ATTRIBUTE_IDS[split_line[0].split(':')[-1]]] = split_line[-1].replace('"','')
                        except KeyError:
                            info_out['disc'][split_line[0].split(':')[-1]] = split_line[-1].replace('"','')
                    else:
                        if line[0] == 'T':
                            track_id = split_line[0].split(':')[-1]
                            try:    #<  If new track_id, dim var
                                track_info = info_out['tracks'][track_id]
                            except KeyError:
                                track_info = info_out['tracks'][track_id] = {'cnts':{'Subtitles':0,'Video':0,'Audio':0}}
                            try:
                                track_info[make_mkv.ATTRIBUTE_IDS[split_line[1]]] = split_line[-1].replace('"','')
                            except Exception:
                                track_info[split_line[1]] = split_line[-1].replace('"','')
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
                            try:
                                track_info[make_mkv.ATTRIBUTE_IDS[split_line[2]]] = split_line[-1].replace('"','')
                            except KeyError:
                                track_info[split_line[2]] = split_line[-1].replace('"','')
            #   Count the track parts
            for track_id,track_info in info_out['tracks'].iteritems():
                for part_id, track_part in track_info['track_parts'].iteritems():
                    try:
                        info_out['tracks'][track_id]['cnts'][track_part['Type']] += 1
                    except KeyError:    #<  Type not avail, should be good to ignore?
                        pass
            self.get_busy(disc_id)
            return info_out
    
    def scan_drives(self, ):
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
        
    def _sanitize_filename(self, file_path, ):
        '''
            Remove reserved characters from file name
            @param  file_path   str File path (will sanitize last part)
            @return str Sanitized
        '''
        file_path = file_path.split(os.path.sep)
        for key,val in self.RESERVED_CHAR_MAP.iteritems():
            file_path[-1] = file_path[-1].replace(key, val)
        return os.path.sep.join(file_path)
    
    
    
if __name__ == '__main__':
    #from pprint import pprint
    #pprint(make_mkv.disc_info(1))
    make_mkv()