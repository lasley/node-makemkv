#!/usr/env/python
##  Socket server for makemkvcon
#         
#   makemkvcon server
#    
#   @author     David Lasley, dave -at- dlasley -dot- net
#   @website    http://code.google.com/p/remote-makemkv/
#   @package    remote-makemkv
#   @version    $Id$
#
#   @requires-binary   makemkvcon, mkisofs

import os
import subprocess
import threading
import datetime
import time
import re
import socket
import json
import shutil

#   Detect root, error if not
if os.getuid() != 0:
    raise Exception('Must run as root!')


class socket_server(threading.Thread):
    RECV_CHUNKS = 4096
    def __init__(self, port, arg_list):
        ##  Init
        #   @param  Int     port        Port to run on
        #   @param  Dict    arg_list    Socket arg list
        super(socket_server, self).__init__()
        self.args = arg_list
        self.port = port
        self.sockets = []
        self.send_queue = {}
        self.current_sends = []
        self.lock = threading.Lock()
        
    def __del__(self):
        ##  Kill active sockets
        for socket in self.sockets:
            socket.shutdown()
            socket.close()
            
    def now(self):
        ##  Now
        return datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")
    
    def run(self):
        ##  Main daemon
        host = ''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
        s.bind((host, self.port))
        self.sockets.append(s)
        conn, addr = self._sock_listen(s)
        rcvd_data = []
        full_cmds = []
        while 1:
            try:
                #print 'Receiving Data...'
                data_chunk = conn.recv(self.RECV_CHUNKS).decode('utf-8')
                #print 'PROCESSING: "%s"' % data_chunk
                if '[>#!>]' in data_chunk:
                    if data_chunk[-6:] == '[>#!>]': #<  End of command
                        split_chunks = data_chunk.split('[>#!>]')
                        rcvd_data.append(split_chunks.pop(0))
                        rcvd_data = [''.join(rcvd_data)]
                        if split_chunks[0] == '' and len(split_chunks) == 1:
                            split_chunks = []
                        full_cmds = full_cmds + rcvd_data + split_chunks
                        rcvd_data = []
                        split_chunks = []
                        #break
                    else:   #< At least the end of the other command?
                        split_chunks = data_chunk.split('[>#!>]')
                        rcvd_data.append(split_chunks.pop(0))
                        rcvd_data = [''.join(rcvd_data)]
                        full_cmds = full_cmds + rcvd_data + split_chunks[:-1]
                        rcvd_data = split_chunks[-1]
                        split_chunks = []
                        #break
                else:   #<  Partial cmd
                    rcvd_data.append(data_chunk)   
            except socket.error:    #<  Lost addr
                conn, addr = self._sock_listen(s)
                continue
            if not data_chunk:    #<  Lost addr
                conn, addr = self._sock_listen(s)
            else:
                print 'Full Commands Rcvd! "%s"' % repr(full_cmds)
                #for command in re.findall('(.*?)',data):
                for input_cmd in full_cmds:
                    args = input_cmd.split('|')
                    cmd = args.pop(0)
                    if cmd != '':
                        t = threading.Thread(target=self._eval_cmd,name=str(datetime.datetime.now),args=(cmd,conn,args))
                        t.daemon = True
                        t.start()
                full_cmds = []
    
    def _eval_cmd(self,cmd,conn,args=[]):
        ##  Eval incoming commands against self.args, sends response to conn
        #   @param  Str     cmd     Command to run
        #   @param  Obj     conn    socket connection to send data on
        #   @param  List    args    List of args for cmd
        try:
            if len(args)>0:
                cmd_return = eval('%s(self, "%s")' % (self.args[cmd], '","'.join(args)) )
            else:
                cmd_return = eval('%s(self)' % (self.args[cmd]) )
            self._cmd_q('%s[>#!>]'%json.dumps(cmd_return),conn)
        except KeyError:
            self._cmd_q('%s[>#!>]'%json.dumps(cmd_return),conn)
    
    def _cmd_q(self,send_str,conn):
        ##  Queue and send commands to conn
        #   @param  Str send_str    Send this
        #   @param  Obj conn        To this
        try:
            self.send_queue[conn].append(send_str)
        except KeyError:
            self.send_queue[conn] = [send_str]
        if conn not in self.current_sends:
            self.current_sends.append(conn) #<  Set Sending flag
            self.lock.acquire()
            try:
                while 1:
                    total_sent, loop_cnt = 0, 0
                    msg = self.send_queue[conn].pop(0)
                    #print 'Sending Msg'
                    #while total_sent < len(msg):
                    #    sent = conn.send(msg[total_sent:])
                    #    if sent == 0:
                    #        raise RuntimeError("Lost Socket")
                    #    total_sent += sent
                    #    loop_cnt += 1
                    conn.sendall(msg)
                    #print msg
                    print 'Sent Data!'
                    #time.sleep(2)
            except IndexError:
                self.current_sends.pop(self.current_sends.index(conn)) #<   Remove Sending Flag
                self.lock.release()
              
    def _sock_listen(self,s):
        ##  Socklisten
        s.listen(1)
        return s.accept()


class make_mkv(object):
    TEMP_DIR = os.path.join('media','Derp','tmp')
    NEWLINE_CHAR = '\n'
    SELECTION_PROFILE = (
        '-sel:all',
        '+sel:audio&(eng)',
        '+sel:mvcvideo',
        '+sel:subtitle',
        '-sel:special',
        '=100:all',
        '-10:favlang',
    )
    ATTRIBUTE_IDS = {
        '0' :   'Unknown',
        '1' :   'Type',
        '2' :   'Name',
        '3' :   'Lng Code',
        '4' :   'Lng Name',
        '5' :   'Codec ID',
        '6' :   'Codec Short',
        '7' :   'Codec Long',
        '8' :   'Chapter Count',
        '9' :   'Duration',
        '10':   'Disk Size',
        '11':   'Disk Size Bytes',
        '12':   'Stream Type Extension',
        '13':   'Bitrate',
        '14':   'Audio Channels Cnt',
        '15':   'Angle Info',
        '16':   'Source File Name',
        '17':   'Audio Sample Rate',
        '18':   'Audio Sample Size',
        '19':   'Video Size',
        '20':   'Video Aspect Ratio',
        '21':   'Video Frame Rate',
        '22':   'Stream Flags',
        '23':   'Date Time',
        '24':   'Original Title ID',
        '25':   'Segments Count',
        '26':   'Segments Map',
        '27':   'Output Filename',
        '28':   'Metadata Lng Code',
        '29':   'Metadata Lng Name',
        '30':   'Tree Info',
        '31':   'Panel Title',
        '32':   'Volume Name',
        '33':   'Order Weight',
        '34':   'Output Format',
        '35':   'Output Format Description',
        '36':   'MaxValue'
    }
    COL_PATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
    def __init__(self, save_path=None):
        self.save_to = save_path
        SOCKET_ARGS = {
            "rip"       :   'make_mkv.rip_track',
            "disc_info" :   'make_mkv.disc_info',
            "scan_drives":  'make_mkv.scan_drives',
            'iso'       :   'make_mkv.to_iso',
        }
        _s = socket_server(8888,SOCKET_ARGS)
        _s.start()
    
    @staticmethod
    def rip_track(socket_parent, out_path,disc_id,track_ids):
        if not os.path.isdir(out_path):
            os.mkdir(out_path)
        ripped_tracks = {'disc_id':  disc_id}
        for track_id in track_ids.split(','):
            ripped_tracks[track_id] = '1 titles saved.' in subprocess.check_output([u'makemkvcon',u'--noscan',u'mkv',u'dev:%s'%disc_id,u'%s'%track_id,out_path])
        return ripped_tracks
    
    @staticmethod
    def to_iso(socket_parent, out_path,disc_id):
        if not os.path.isdir(out_path):
            os.mkdir(out_path)
        rip_output = {
            'disc_id':  disc_id,
            'out_file': u'%s.iso'%out_path
        }
        decrypt_out = subprocess.check_output([u'makemkvcon', u'--noscan', u'backup' ,u'--decrypt', u'disc:%s'%socket_parent.drive_map[disc_id], out_path])   #< to folder, decrypt
        print 'DECRYPT:\n'+decrypt_out+'\n\n'
        iso_out = subprocess.check_output([u'mkisofs', u'-J', u'-r', u'-o', u'-iso-level', u'3', u'-udf', u'-allow-limited-size', rip_output['out_file'], out_path])  #<  Make iso
        print 'ISO:\n'+iso_out+'\n\n'
        shutil.rmtree(out_path) #<  RM disc tree
        return rip_output   #< Exceptions from failures should cause this to not get hit on fail?
    
    @staticmethod
    def disc_info(socket_parent, disc_id,thread_id=None):
        info_out = {
            'disc'  :   {},
            'tracks':   {},
            'disc_id':  disc_id
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
    
    @staticmethod
    def scan_drives(socket_parent):
        ##  Scan drives, return info
        #   @return Dict    Dict keyed by drive index, value is movie name
        drives = {}
        socket_parent.drive_map = {}
        try:
            drive_scan = subprocess.check_output(['makemkvcon','-r','info'])
        except subprocess.CalledProcessError as e:
            drive_scan = e.output
        for line in drive_scan.split(make_mkv.NEWLINE_CHAR):
            if line[:4] == 'DRV:' and '/dev/' in line:  #<  DRV to make sure it's drive output, /dev to make sure that there is a drive
                _info = make_mkv.COL_PATTERN.split(line)
                drive_location = _info[-2].replace('"','')
                drives[drive_location] = _info[-4].replace('"','') if _info[-4] != '""' else None#<  [Drive Index] = Movie Name
                socket_parent.drive_map[drive_location] = _info[1].split(':')[1] #<    Index the drive location to makemkv's drive ID
        return  drives
    
    def get_disc_drives():
        ##  Scan for DVD/BD drives w/o using MakeMkv
        #   @return Dict keyed by drive index (as MakeMkv recognizes them - /dev/sr#)
        drives = {}
    
if __name__ == '__main__':
    #from pprint import pprint
    #pprint(make_mkv.disc_info(1))
    make_mkv()