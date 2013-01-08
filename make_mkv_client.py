#!/usr/env/python

import socket
import socks
import time
import threading
import json
import sys
import logging
from PyQt4 import QtGui, QtCore
from pprint import pprint

class make_mkv_client(object):
    HOST = '192.168.69.67'
    PORT = 8888
    RECV_CHUNKS = 1024 
    OUT_PATH = '/media/Motherload/1-test_ripping/'
    DISC_INFO_TABLE_COLS = {
        'Size'  :   "track_info['Disk Size']",
        'Length':   "track_info['Duration']",
        'Chptrs':   "track_info['Chapter Count']",
        'Aud'   :   "track_info['cnts']['Audio']",
        'Sub'   :   "track_info['cnts']['Subtitles']",
        'Vid'   :   "track_info['cnts']['Video']",
    }
    SIZE_MULT = dict(KB=2**10, MB=2**20, GB=2**30)
    def __init__(self, proxy_host=None, proxy_port=8080):
        self.app = QtGui.QApplication(sys.argv)
        self.gui = make_mkv_client_gui()
        self.gui.setStyleSheet('')
        self.locked = threading.Lock()
        self.scan_operations = 0
        if proxy_host:
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, proxy_host, proxy_port)
            socket.socket = socks.socksocket
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.settimeout(3)
        try:
            self.socket.connect((self.HOST,self.PORT))
        except socket.error:
            raise Exception('%s:%s is down!' % (self.HOST,self.PORT))
        self.socket.settimeout(None)
        self.socket_buffer = ''
        self.disc_info_map, self.check_map, self.disc_name_map, self.rip_button_map = {}, {}, {}, {}
        self.init_ui()
        sys.exit(self.app.exec_())
        
    def __del__(self):
        self.socket.close()
    
    def init_ui(self):
        def click_all_buttons():
            for x in self.rip_button_map.values(): x.clicked.emit(True)
        layout = QtGui.QHBoxLayout()
        self.refresh_all_button = self.gui.button('Refresh Drives', self.thread_finish, self._scan_drives)
        self.refresh_all_button.setObjectName('btn_refresh_drives')
        self.gui.main_layout.addWidget(self.refresh_all_button)
        disc_layout = QtGui.QHBoxLayout()
        disc_layout.setObjectName('lout_all_discs')
        self.gui.main_layout.addLayout(disc_layout)
        self.gui.main_layout.addWidget(self.gui.button('Rip Selected', self.thread_finish, click_all_buttons))
        #refresh_button.clicked.emit(True)
    
    def thread_finish(self, input_list):
        print 'Thread finished start'
        layout_els = (QtGui.QGridLayout, QtGui.QHBoxLayout,QtGui.QVBoxLayout)
        thread_func = input_list.pop(0)
        #print input_list
        #layout_map = {
        #    'scan_thread'   :   'lout_all_discs',
        #    'rip_thread'    :   'disc_info:%s' % input_list[1]  #drive ID
        #}
        if thread_func.__name__ == 'scan_thread':
            layout = self.gui.main_layout.findChild(object,'lout_all_discs')
            make_mkv_client_gui.clear_layout(layout)
            add_el = thread_func(*input_list)
            layout.addLayout(add_el)
        elif thread_func.__name__ == 'disc_info_thread':
            add_el = thread_func(*input_list)
            #layout = self.gui.main_layout.findChild(object,'disc_info:%s'%input_list[0])
            #make_mkv_client_gui.clear_layout(layout,0)
        elif thread_func.__name__ == 'rip_thread':
            return_vals = thread_func(*input_list)
            layout = self.disc_info_map[return_vals['disc_id']].layout()
            make_mkv_client_gui.clear_layout(layout,0)
            layout.addWidget(QtGui.QLabel(repr(return_vals)))
        else:
            add_el = thread_func(*input_list)
            #layout = self.gui.main_layout
            #if type(add_el) in layout_els:
            #    layout.addLayout(add_el)
            #else:
            #    layout.addWidget(add_el)
        return True
    
    def _reset_button_refresh(self):
        self.refresh_all_button.setEnabled( self.scan_operations==0 ) 
    
    def _scan_drives(self):
        self.scan_operations+=1
        self._reset_button_refresh()
        def scan_thread(drives):
            self.refresh_buttons = {}
            layout = QtGui.QHBoxLayout()
            for drive_id, movie in drives.iteritems():
                self.refresh_buttons[drive_id] = self.gui.button('Disc Info', self.thread_finish, self._disc_info, drive_id)
                self.refresh_buttons[drive_id].setObjectName('btn_disc_info:%s'%drive_id)
                self.refresh_buttons[drive_id].clicked.emit(True)
                self.disc_info_map[drive_id] = self.gui.group_box('%s:%s'%(drive_id,movie), [self.refresh_buttons[drive_id]])
                self.disc_info_map[drive_id].setObjectName('disc_box:%s'%drive_id)
                layout.addWidget(self.disc_info_map[drive_id])
            self.scan_operations-=1
            self._reset_button_refresh()
            return layout
        drives = self._send_cmd('scan_drives')
        return [scan_thread,drives]
    
    def _rip(self,drive_id,rip_info):
        self.scan_operations+=1
        self._reset_button_refresh()
        self.refresh_buttons[drive_id].setEnabled(False)
        def rip_thread(out_path, drive_id, ripped_tracks):
            print 'Derp', out_path, drive_id, ripped_tracks, 'Derp'
            self.scan_operations-=1
            self.refresh_buttons[drive_id].setEnabled(True)
            self._reset_button_refresh()
            return QtGui.QLabel('Ripped Drive ID: %s Tracks: %s To: %s' % (drive_id, repr(ripped_tracks), out_path))
        layout = self.disc_info_map[drive_id].layout()
        make_mkv_client_gui.clear_layout(layout,0)
        print rip_info()
        return [rip_thread, self._send_cmd('rip|%s|%s|%s' % (rip_info()[0], drive_id, ','.join(rip_info()[1]))), rip_info()[0],drive_id]    
    
    def _disc_info(self,drive_id):
        ##  Get disc info from remote server, return or add to q
        #   @param  Int         drive_id    Drive ID to get
        #   @param  Queue.Queue q           Queue if threading
        #   @return Bool/Dict   Bool if q, else dict
        self.scan_operations+=1
        self._reset_button_refresh()
        self.refresh_buttons[drive_id].setEnabled(False)
        def disc_info_thread(self,drive_id,disc_info):
            def loop_checks(drive_id, checks):
                checked_tracks = []
                for track_id,check_box in checks.iteritems():
                    if check_box.checkState():
                        checked_tracks.append(track_id)
                    out_path = '%s%s' % (self.OUT_PATH, self.disc_name_map[drive_id].text())
                return [out_path,checked_tracks]
            def _lambda_loop(drive_id,checks):
                return lambda: loop_checks(drive_id,checks)
            drive_id = disc_info['disc_id']
            self.disc_info_map[drive_id].setTitle(disc_info['disc']['Name'])
            layout = self.disc_info_map[drive_id].layout()
            make_mkv_client_gui.clear_layout(layout,0)
            check_map = {}
            self.disc_name_map[drive_id] = QtGui.QLineEdit(disc_info['disc']['Name'])
            layout.addWidget(self.disc_name_map[drive_id])
            #disc_info_table = QtGui.QTableWidget(len(disc_info['tracks']),len(self.DISC_INFO_TABLE_COLS))
            #disc_info_table.setHorizontalHeaderLabels(['']+self.DISC_INFO_TABLE_COLS.keys())
            #layout.addWidget(disc_info_table)
            row_num = 0
            sort_lines = []
            for track_id, track_info in disc_info['tracks'].iteritems():
                sort_lines.append('%s:%s' % (track_id,track_info['Disk Size']))
            sort_lines.sort(key=make_mkv_client.get_size) #<  Sort by size
            for sorted_track in reversed(sort_lines):
                track_id = sorted_track.rsplit(':',1)[0]
                track_info = disc_info['tracks'][track_id]
            #for track_id, track_info in disc_info['tracks'].iteritems():
                try:
                    ch_cnt = track_info['Chapter Count']
                    #check_map[track_id] = QtGui.QTableWidgetItem()
                    #check_map[track_id].setCheckState(QtCore.Qt.Unchecked)
                    #disc_info_table.setItem(row_num,0,check_map[track_id])
                    #for col_num, col_var in enumerate(self.DISC_INFO_TABLE_COLS.values()):
                    #    col = QtGui.QTableWidgetItem(eval(col_var))
                    #    disc_info_table.setItem(row_num,col_num+1,col)
                    check_map[track_id] = QtGui.QCheckBox('Track ID:%s\n\tCnts: %s\n\tSize: %s\tChapter Cnt: %s\tDuration:%s' % (track_id, track_info['cnts'], track_info['Disk Size'], ch_cnt, track_info['Duration']))
                    check_map[track_id].setObjectName = '%s:%s' % (drive_id, track_id)
                    layout.addWidget(check_map[track_id])
                except KeyError:
                    pass    #<  ignore ? chapters
                    #ch_cnt = '?'
            self.rip_button_map[drive_id] = self.gui.button('Rip', self.thread_finish, self._rip, drive_id, _lambda_loop(drive_id,check_map))
            layout.addWidget(self.rip_button_map[drive_id])
            self.scan_operations-=1
            self.refresh_buttons[drive_id].setEnabled(True)
            self._reset_button_refresh()
            return layout
        disc_info = self._send_cmd('disc_info|%s' % (drive_id))
        return [disc_info_thread, self, drive_id, disc_info]
    
    @staticmethod
    def get_size(line):
        ##  Sort by size method
        fn, size = line.rsplit(':',1)
        value, unit = size.split(' ')
        multiplier = make_mkv_client.SIZE_MULT[unit]
        return float(value)*multiplier
    
    #SOCKET_ARGS = {
    #            "rip"       :   'make_mkv.rip_track(out_path,disc_id,track_id,overwrite=False)',
    #            "disc_info" :   'make_mkv.disc_info(disc_id)',
    #            "scan_drives":  'make_mkv.scan_drives()'
    #        }
    def _send_cmd(self,cmd):
        try:
            self.socket.send( bytearray(cmd + u'[>#!>]', 'utf-8') )
            print 'Sent "%s"' % cmd
            data = self._socket_recv()
            return json.loads(data)
        except socket.error:
            raise Exception('Host Went Away!')
        
    def _socket_recv(self):
        data_chunk, recvd_data = '',[self.socket_buffer]
        self.socket_buffer = ''
        self.locked.acquire()
        while 1:
            #print 'Receiving Data...'
            data_chunk = self.socket.recv(self.RECV_CHUNKS)
            #print 'PROCESSING: "%s"' % data_chunk
            if '[>#!>]' in data_chunk:
                split_chunk = data_chunk.split('[>#!>]')
                data_chunk = split_chunk[0]
                self.socket_buffer = split_chunk[1]
                recvd_data.append(data_chunk)
                break
            recvd_data.append(data_chunk)
        #recvd_data[-1]= recvd_data[-1]
        logging.debug( ''.join(recvd_data) ) 
        #print 'PROCESSED: "%s"' % ''.join(out_list)
        self.locked.release()
        return ''.join(recvd_data)
    
    def _close_server(self):
        self._send_cmd('DIE BITCH!')
    
    def _center_window(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
class worker_thread(QtCore.QThread):
    finished = QtCore.pyqtSignal(list)
    def __init__(self, function, *args, **kwargs):
        super(worker_thread, self).__init__()
        #self.finished.connect(fin_function)
        self.function = function
        self.args = args
        self.kwargs = kwargs
   
    def __del__(self):
        self.wait()
   
    def run(self):
        ret = self.function(*self.args,**self.kwargs)
        self.finished.emit(ret)
        return

#   Main Gui      
class make_mkv_client_gui(QtGui.QWidget):
    def __init__(self, x=100, y=100, w=800, h=800, center=True):
        super(make_mkv_client_gui, self).__init__()
        self.setGeometry(x,y,w,h)
        self.setWindowTitle('Remote MakeMKV Client')
        self.threads = []
        #icon = QtGui.QIcon(os.path.join('c:/','xampp','htdocs','ITL_HTML','trunk','shared_data','images','datait_logo.png'))
        #self.setWindowIcon(icon)
        self.main_layout = QtGui.QVBoxLayout()
        #self.systray = wins_systray(self,icon)
        #self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)
        self.setObjectName('main_window')
        if center: self.center()
        self.show()
    
    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    @staticmethod
    def group_box(title, add_widgets=[], layout_type='v'):
        layout_types = {
            'h' :   QtGui.QHBoxLayout,
            'v' :   QtGui.QVBoxLayout,
            #'g' :   QtGui.QGridLayou,    <@todo implement
        }
        box = QtGui.QGroupBox(title)
        layout = layout_types[layout_type]() if layout_type else box
        for widget in add_widgets:
            layout.addWidget(widget)
        if layout: box.setLayout(layout)
        box.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        return box
    
    def button(self, txt, ret_function, function, *args, **kwargs):
        button = QtGui.QPushButton(txt)
        self.threads.append(worker_thread(function, *args, **kwargs))
        #self.threads[-1].setObjectName(txt)
        #button.thread = self.threads[-1]
        button.clicked.connect( self.threads[-1].start )
        #QtCore.QObject.connect(self.threads[-1],QtCore.SIGNAL('finished()'), retstart)
        self.threads[-1].finished.connect(ret_function)
        #
        #obj_container = QtCore.QObject()
        #self.threads.append(QtCore.QThread())
        #self.threads[-1].setObjectName(txt)
        #obj_container.connect(button,QtCore.SIGNAL('clicked()'), self.threads[-1].start)
        #self.threads[-1].started.connect(handler)
        #obj_container.moveToThread(self.threads[-1])
        #print 'App Thread:%s\nThread:%s' % ( self.thread().objectName(), obj_container.thread().objectName() )
        return button
    
    @staticmethod
    def clear_layout(layout, preserve_el=None):
        ##  Clear a layout recursively
        #   @param  QLayout layout      Layout
        #   @param  Int     preserve_el Element index to preserve
        for i in reversed(range(layout.count())):
            if i != preserve_el:
                item = layout.itemAt(i)
                if isinstance(item, QtGui.QWidgetItem):
                    item.widget().close()
                    # or
                    # item.widget().setParent(None)
                elif isinstance(item, QtGui.QSpacerItem):
                    # meh
                    pass
                else:
                    make_mkv_client_gui.clear_layout(item.layout())
                layout.removeItem(item) 
    
    @staticmethod
    def format_seconds(seconds,date_format='%h:%i'):
        mins = math.floor(seconds/60)
        hours = math.floor(mins/60)
        seconds -= mins * 60
        mins -= hours*60
        format_dict = {
            '%h'    :   hours,
            '%i'    :   mins,
            '%s'    :   seconds,
        }
        for key,item in format_dict.iteritems():
            date_format = date_format.replace(key,'%02d'%item)
        return date_format
    
    
if __name__ == '__main__':
    make_mkv_client('localhost')
    