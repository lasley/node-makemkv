#!/usr/bin/env python
##  GUI classes for make_mkv_client
#   @author     David Lasley, dave -at- dlasley -dot- net
#   @website    http://code.google.com/p/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id$
#
#   @requires-python-packages   pyqt4, socksipy-branch
import select
import socket
import socks
import threading
import datetime
import json
import sys
import os
dirname = os.path.dirname(__file__)
sys.path.append(os.path.join(dirname, "../.."))
from remote_makemkv import HOST,PORT,PROXY_HOST,PROXY_PORT,logging

                
#   Base Class, probably not going to be directly referencing this..
class custom_socket(threading.Thread):
    END_DELIM = u'[>#!>]'
    RECV_CHUNKS = 4096
    def __init__(self, add_args={}):
        super(custom_socket, self).__init__()
        self.args = {   #<  Arg:[function,*Args]
            'exit'  :   exit,
            'error' :   self.error,
            'handshake':self.handshake,
            'hello' :   self.hello,
        }
        self.args.update(add_args)
        self.send_queue = {}
        self.current_sends = []
        self.locked = threading.Lock()

    def error(self, error_info):
        raise RuntimeError(error_info['msg'])

    def handshake(self, info):
        self.send_str(json.dumps({'cmd':'hello','msg':'Handshaking...'}))
    
    def hello(self, info):
        logging.debug('Handshake received.')
        
    def _eval_cmd(self,cmd=None,args=[]):
        ##  Eval incoming commands against self.args, sends response to conn
        #   @param  Str     cmd     Command to run
        #   @param  socket  conn    socket connection to send data on
        #   @param  List    args    List of args for cmd
        logging.debug('Eval Command %s' % repr([cmd,args]))
        try:
            if cmd is None:
                self.args[args['cmd']]( args )
            else:
                self.send_str( json.dumps(self.args[cmd]( *args  ) ) )
        except KeyError:
            error_msg = json.dumps({
                'cmd' : 'error',
                'msg' : 'Not a valid command. Commands are: %s[>#!>]'%(', '.join(self.args.keys()))
            })
            self.send_str(  error_msg )
    
    def recv(self, _socket, qt=False):
        rcvd_data = []
        full_cmds = []
        no_data = 0 
        while no_data < 5:
            logging.debug( 'Receiving Data...')
            try:
                data_chunk = _socket.recv(self.RECV_CHUNKS).decode('utf-8')
                if not data_chunk:    #<  Lost addr
                    logging.debug('No data..%s' %repr(data_chunk))
                    no_data += 1
                elif self.END_DELIM in data_chunk:
                    if data_chunk[-6:] == self.END_DELIM: #<  End of command
                        split_chunks = data_chunk.split(self.END_DELIM)
                        rcvd_data.append(split_chunks.pop(0))
                        rcvd_data = [''.join(rcvd_data)]
                        if split_chunks[0] == '' and len(split_chunks) == 1:
                            split_chunks = []
                        full_cmds = full_cmds + rcvd_data + split_chunks
                        rcvd_data = []
                        split_chunks = []
                        no_data = 0
                        break
                    else:   #< At least the end of the other command?
                        split_chunks = data_chunk.split(self.END_DELIM)
                        rcvd_data.append(split_chunks.pop(0))
                        rcvd_data = [''.join(rcvd_data)]
                        full_cmds = full_cmds + rcvd_data + split_chunks[:-1]
                        rcvd_data = split_chunks[-1]
                        split_chunks = []
                        no_data = 0
                        #break
                else:   #<  Partial cmd
                    no_data = 0
                    rcvd_data.append(data_chunk)   
            except socket.error as e:    #<  Lost addr
                logging.debug('Lost Connection: %s' % repr(e))
                return False
        else:
            return_var = False
        logging.debug( 'Full Cmds Rcvd! "%s"' % repr(full_cmds) ) 
        #for command in re.findall('(.*?)',data):
        for input_cmd in full_cmds:
            if input_cmd != '':
                return_var = True
                try:
                    args = json.loads(input_cmd)
                    cmd = None
                except ValueError:
                    args = input_cmd.split('|')
                    cmd = args.pop(0)
                if qt:
                    logging.debug('In QT Thread')
                    self._eval_cmd(cmd,args)
                else:
                    logging.debug('Threading')
                    t = threading.Thread(target=self._eval_cmd,name=str(datetime.datetime.now),args=(cmd,args))
                    t.daemon = True
                    t.start()
        #full_cmds = []
        return return_var
    
    def send_str(self,send_str=None):
        for conn in self.clients.values():
            if send_str:    #<  Otherwise just clearing queues..
                try:
                    self.send_queue[conn].append('%s%s'%(send_str,self.END_DELIM))
                except KeyError:
                    self.send_queue[conn] = ['%s%s'%(send_str,self.END_DELIM)] 
            if conn not in self.current_sends:
                self.current_sends.append(conn) #<  Set Sending flag
                self.locked.acquire()
                try:
                    while 1:
                        total_sent = 0
                        msg = self.send_queue[conn].pop(0)
                        while total_sent < len(msg):
                            sent = conn.send( bytearray(msg[total_sent:], 'utf-8') )
                            if sent == 0:
                                raise RuntimeError("socket connection lost")
                            elif sent < len(self.END_DELIM):
                                total_sent += conn.send( bytearray(self.END_DELIM, 'utf-8') )
                            total_sent += sent
                        logging.debug('Sent %d' % (sent))
                except IndexError:
                    self.current_sends.pop(self.current_sends.index(conn)) #<   Remove Sending Flag
                    self.locked.release()
                    return

class custom_server(custom_socket):
    def __init__(self, arg_list={}):
        ##  Init
        #   @param  Int     port        Port to run on
        #   @param  Dict    arg_list    Socket arg list
        super(custom_server, self).__init__(arg_list)
        self.clients = {}
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(0)
        self.server.bind((HOST, PORT))
        logging.debug('Listening on %s:%s' % (HOST,PORT))
        self.server.listen(5)
        
    def __del__(self):
        ##  Kill active sockets
        self.server.close()

    def run(self):
        while 1:
            try:
                client_vals = self.clients.values()
                ready_in,ready_out,ready_except = select.select([self.server]+client_vals, [], [])
            except select.error as e:
                break
            except socket.error as e:
                break
            logging.debug('Break select loop, writing to clients %s' % repr(client_vals))
            for s in ready_in:
                if s == self.server:
                    conn, address = s.accept()
                    logging.debug('Connection...')
                    self.clients[conn.fileno()] = conn
                else:
                    logging.debug('Attempting recv..')
                    #self.recv(s)
                    if not self.recv(s):
                        logging.debug('Deleting %s' % s.fileno())
                        del self.clients[s.fileno()]
                    #    if not self.recv(s):
                    #        logging.debug('Deleting %s' % s.fileno())
                    #        del self.clients[s.fileno()]
                    
        #def send_str(self,send_str=None):
        #    logging.debug('Server send loop')
        #    for client in self.clients.values():
        #        super(custom_server,self).send_str(self,client,send_str)   

class custom_client(custom_socket):
    def __init__(self, args={}):
        ##  Init a socket as self.socket to host on port. Use proxy if needed
        #  
        #   @param  Str proxy_host  Proxy host
        #   @param  Int proxy_port Proxy port
        super(custom_client, self).__init__(args)
        if PROXY_HOST:
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, PROXY_HOST, PROXY_PORT)
            socket.socket = socks.socksocket
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connect()
        
    def connect(self, timeout=None, login_timeout=3):
        self.socket.settimeout(login_timeout)
        try:
            logging.debug('Connecting to %s:%s' % (HOST,PORT))
            self.socket.connect((HOST,PORT))
        except socket.error:
            logging.debug('Failed to establish connection to server.')
            return False
        self.socket.settimeout(timeout)
        self.clients = {self.socket.fileno():self.socket}
        return True
    
    def send_str(self,send_str=None):
        try:
            return super(custom_client, self).send_str(send_str)
        except socket.error:
            self.connect()
            return super(custom_client, self).send_str(send_str)
    
    def recv(self):
        recv_fails = 0
        while recv_fails<2:
            if not super(custom_client,self).recv(self.socket, True):
                recv_fails +=1
                self.connect()
            else:
                recv_fails = 0