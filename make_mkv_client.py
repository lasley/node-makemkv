#!/usr/env/python
##   Client for make_mkv.py
#         
#    GUI
#    
#    @author     David Lasley, dave -at- dlasley -dot- net
#    @package    remote-makemkv
#    @version    $Id$
import socket
import socks
import time
import threading
import json
import sys
import logging
from rename import rename
from PyQt4 import QtGui, QtCore
from pprint import pprint

class make_mkv_client(object):
    ##  Main class
    HOST = '192.168.69.67'
    PORT = 8888
    RECV_CHUNKS = 4096 
    OUT_PATH = '/media/Motherload/7-ripp/'
    DISC_INFO_TABLE_COLS = {
        'Size'  :   "track_info['Disk Size']",
        'Length':   "track_info['Duration']",
        'Chptrs':   "track_info['Chapter Count']",
        'Aud'   :   "track_info['cnts']['Audio']",
        'Sub'   :   "track_info['cnts']['Subtitles']",
        'Vid'   :   "track_info['cnts']['Video']",
    }
    SIZE_MULT = dict(KB=2**10, MB=2**20, GB=2**30)
    DRIVE_NAME_MAPS = {
        '/dev/sr0'  :   '1st',
        '/dev/sr1'  :   '3rd',
        '/dev/sr2'  :   '2nd',
        '/dev/sr3'  :   '4th',
        '/dev/sr4'  :   '5th',
    }
    def __init__(self, proxy_host=None, proxy_port=8080):
        ##  Init
        ##  @param  Str proxy_host  SOCKS proxy hsot
        ##  @param  Int proxy_port  SOCKS proxy port
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
        self.ui_map = {}
        self.init_ui()
        sys.exit(self.app.exec_())
        
    def __del__(self):
        ##  Close Socket
        self.socket.close()
    
    def init_ui(self):
        ##  Init The GUI
        self.app = QtGui.QApplication(sys.argv)
        icon = QtGui.QIcon('./mkv_icon_all.png')
        self.gui = make_mkv_client_gui(icon=icon)
        self.gui.setStyleSheet('')
        def click_all_buttons():
            for x in self.rip_button_map.values(): x.clicked.emit(True)
        layout = QtGui.QHBoxLayout()
        self.systray = makemkv_systray(self.gui,icon)
        self.output_dir = QtGui.QLineEdit(self.OUT_PATH)
        qgrid = QtGui.QGridLayout()
        out_label = QtGui.QLabel('Output Dir:')
        out_label.setAlignment(QtCore.Qt.AlignRight)
        qgrid.addWidget(out_label,1,0,1,1)
        qgrid.addWidget(self.output_dir,1,1,1,3)
        self.refresh_all_button = self.gui.button('Refresh Drive(s)', self.thread_finish, self._scan_drives)
        self.refresh_all_button.setObjectName('btn_refresh_drives')
        self.ui_map['refresh_all'] = self.refresh_all_button
        qgrid.addWidget(self.refresh_all_button,2,0,1,2)
        self.ui_map['rip_all'] = self.gui.button('Rip Selected', self.thread_finish, click_all_buttons)
        qgrid.addWidget(self.ui_map['rip_all'],2,2,1,2)
        disc_layout = QtGui.QHBoxLayout()
        disc_layout.setObjectName('lout_all_discs')
        qgrid.addLayout(disc_layout,3,0,5,4)
        self.ui_map['all_discs'] = disc_layout
        self.gui.main_layout.addLayout(qgrid)
    
    def thread_finish(self, input_list):
        ##  Generic Thread End-Point
        #   @param  List    input_list  Thread output
        print 'Thread finished start'
        layout_els = (QtGui.QGridLayout, QtGui.QHBoxLayout,QtGui.QVBoxLayout)
        thread_func = input_list.pop(0)
        if thread_func.__name__ == 'scan_thread':
            layout = self.gui.main_layout.findChild(object,'lout_all_discs')
            make_mkv_client_gui.clear_layout(layout)
            add_el = thread_func(*input_list)
            layout.addLayout(add_el)
        elif thread_func.__name__ == 'disc_info_thread':
            thread_func(*input_list)
        elif thread_func.__name__ == 'rip_thread':
            add_el = thread_func(*input_list)
            drive_id = add_el[1]
            add_el = add_el[0]
            layout = layout = self.ui_map[drive_id]['disc_layout']
            #make_mkv_client_gui.clear_layout(layout,enable=True)
            layout.addWidget(make_mkv_client_gui.group_box('Rip Output', [add_el]))
        else:
            add_el = thread_func(*input_list)
    
    def _reset_button_refresh(self):
        ##  Reset the global refresh button if neccessita
        #   Also throws tray_message to alert of disc operation completes
        not_currently_scanning = self.scan_operations==0
        self.refresh_all_button.setEnabled( not_currently_scanning )
        if not_currently_scanning:
            self.systray.tray_message('Operations Complete!','All Current Disc Operations Have Completed.')
    
    def _scan_drives(self):
        ##  Wrapper function for scanning the drives
        #   @return List    [Scan_thread_function, scan_server_command]
        self.scan_operations+=1
        self._reset_button_refresh()
        def scan_thread(drives):
            ##  Once the command has completed, this manipulates the GUI
            #   @param  Dict    drives  Drives [sys location (/dev/sr#)] => Movie Name
            #   @return QtGui.QHBoxLayout   Layout of disc info w/ checks
            self.refresh_buttons = {}
            layout = QtGui.QHBoxLayout()
            for drive_id, movie in drives.iteritems():
                try:
                    drive_name = self.DRIVE_NAME_MAPS[drive_id]
                except KeyError:
                    drive_name = drive_id
                self.ui_map[drive_id] = {}
                self.ui_map[drive_id]['get_info'] = self.gui.button('Disc Info', self.thread_finish, self._disc_info, drive_id)
                self.ui_map[drive_id]['get_info'].setObjectName('btn_disc_info:%s'%drive_id)
                self.ui_map[drive_id]['disc_box'] = self.gui.group_box('%s - %s'%(drive_name,movie))
                self.ui_map[drive_id]['disc_box'].setObjectName('disc_box:%s'%drive_id)
                self.ui_map[drive_id]['disc_box'].setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
                self.ui_map[drive_id]['disc_layout'] = QtGui.QVBoxLayout()
                self.ui_map[drive_id]['disc_box'].setLayout(self.ui_map[drive_id]['disc_layout'])
                self.ui_map[drive_id]['disc_layout'].addWidget(self.ui_map[drive_id]['get_info'],1)
                layout.addWidget(self.ui_map[drive_id]['disc_box'])
                self.ui_map[drive_id]['get_info'].clicked.emit(True)
            self.scan_operations-=1
            self._reset_button_refresh()
            return layout
        drives = self._send_cmd('scan_drives')
        return [scan_thread,drives]
    
    def _rip(self,drive_id,rip_info):
        ##  Wrapper function for ripping tracks
        #   @param  Str     drive_id    Drive id (sys location /dev/sr#)
        #   @param  Lambda  rip_info    Lamba function to get the checked boxes..ghetto, I know
        #   @return List    [rip_thread_complete_function, rip_server_command, movie_name_override_text, drive_id]
        def rip_thread(rip_information):
            ##  Ripping thread complete function
            #   @todo document this
            drive_id = rip_information['disc_id']
            del rip_information['disc_id']
            output = []
            for track_id,bol_success in rip_information.iteritems():
                output.append('Track %s: %s' % (track_id, repr(bol_success)))
            self.scan_operations-=1
            self.ui_map[drive_id]['get_info'].setEnabled(True)
            self._reset_button_refresh()
            return [QtGui.QLabel('Drive ID: %s\n%s' % (drive_id, '\n'.join(output))), drive_id]
        if len(rip_info()[1]) > 0:
            self.scan_operations+=1
            self._reset_button_refresh()
            self.ui_map[drive_id]['get_info'].setEnabled(False)
            layout = self.ui_map[drive_id]['disc_layout']
            make_mkv_client_gui.clear_layout(layout,0,True)
            return [rip_thread, self._send_cmd('rip|%s|%s|%s' % (rip_info()[0], drive_id, ','.join(rip_info()[1])))]    
    
    def _disc_info(self,drive_id):
        ##  Wrapper function for getting disc info
        #   @param  Int         drive_id    Drive ID to get
        #   @todo   Document this
        self.scan_operations+=1
        self._reset_button_refresh()
        self.ui_map[drive_id]['get_info'].setEnabled(False)
        def disc_info_thread(self,disc_info):
            self.scan_operations-=1
            drive_id = disc_info['disc_id']
            self.ui_map[drive_id]['get_info'].setEnabled(True)
            self._reset_button_refresh()
            def loop_checks(drive_id):
                checked_tracks = []
                for track_id,check_box in self.ui_map[drive_id]['check_map'].iteritems():
                    if check_box.checkState(0):
                        checked_tracks.append(track_id)
                    out_path = '%s/%s' % (self.output_dir.text(), self.ui_map[drive_id]['new_name'].text())
                return [out_path,checked_tracks]
            def _lambda_loop(drive_id):
                return lambda: loop_checks(drive_id)
            try:
                drive_name = self.DRIVE_NAME_MAPS[drive_id]
            except KeyError:
                drive_name = drive_id
            #self.disc_info_map[drive_id].setTitle(u'%s:%s' % (drive_name, disc_info['disc']['Name']))
            layout = self.ui_map[drive_id]['disc_layout']
            make_mkv_client_gui.clear_layout(layout,0)
            check_map = {}
            sanitized = {}
            if len(disc_info['tracks']) > 0:
                for i in ('Volume Name','Tree Info','Name'):
                    try:
                        sanitize = rename.full_sanitize(disc_info['disc'][i])
                        for key,val in sanitize[1].iteritems():
                            sanitized[key] = val
                        sanitized['sanitized'] = sanitize[0]
                    except KeyError:    #<  name type didn't exist for some reason..
                        pass
                self.ui_map[drive_id]['new_name'] = QtGui.QLineEdit(rename.format_season(sanitized))
                layout.addWidget(self.ui_map[drive_id]['new_name'])
                self.ui_map[drive_id]['disc_info'] = QtGui.QTreeWidget()
                self.ui_map[drive_id]['disc_info'].setColumnCount(2)
                self.ui_map[drive_id]['disc_info'].setHeaderLabels(['Type','Value'])
                #self.ui_map[drive_id]['disc_info'].setMinimumSize(320,500)
                #self.ui_map[drive_id]['disc_info'].setMaximumSize(8000,8000)
                self.ui_map[drive_id]['disc_info'].setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
                layout.addWidget(self.ui_map[drive_id]['disc_info'])
                self.ui_map[drive_id]['rip_btn'] = self.gui.button('Rip', self.thread_finish, self._rip, drive_id, _lambda_loop(drive_id))
                layout.addWidget(self.ui_map[drive_id]['rip_btn'])
                self.rip_button_map[drive_id] = self.ui_map[drive_id]['rip_btn']
                self.ui_map[drive_id]['check_map'] = {}
                row_num = 0
                sort_lines = []
                for track_id, track_info in disc_info['tracks'].iteritems():
                    sort_lines.append('%s:%s' % (track_id,track_info['Disk Size']))
                sort_lines.sort(key=make_mkv_client.get_size) #<  Sort by size
                for sorted_track in reversed(sort_lines):
                    track_id = sorted_track.rsplit(':',1)[0]
                    track_info = disc_info['tracks'][track_id]
                    try:
                        ch_cnt = track_info['Chapter Count']
                        self.ui_map[drive_id]['check_map'][track_id] = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['disc_info'])
                        self.ui_map[drive_id]['check_map'][track_id].setText(0,'Track %s' % track_id)
                        self.ui_map[drive_id]['check_map'][track_id].setExpanded(True)
                        child = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                        child.setText(0, 'Size')
                        child.setText(1, track_info['Disk Size'])
                        child = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                        child.setText(0, 'Chptrs')
                        child.setText(1, track_info['Chapter Count'])
                        for typ,cnt in track_info['cnts'].iteritems():
                            child = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                            child.setText(0, typ)
                            child.setText(1, str(cnt))
                        #self.ui_map[drive_id]['check_map'][track_id].setText(1,'\r\n'.join(main_track_txt))
                        self.ui_map[drive_id]['check_map'][track_id].setCheckState(0, QtCore.Qt.Unchecked )
                        out_file = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                        out_file.setText(0,'Out File')
                        out_file.setText(1,track_info['Output Filename'])
                        for key,val in track_info['track_parts'].iteritems():
                            child = QtGui.QTreeWidgetItem(out_file)
                            child.setText(0,key)
                            if type(val) == dict:
                                #child.setText(1,repr(val))
                                for _key,_val in val.iteritems():
                                    _child = QtGui.QTreeWidgetItem(child)
                                    _child.setText(0,_key)
                                    _child.setText(1,repr(_val))
                            else:
                                child.setText(1,repr(val))
                        #check_map[track_id] = QtGui.QCheckBox('Track ID:%s\n\tCnts: %s\n\tSize: %s\tChapter Cnt: %s\tDuration:%s' % (track_id, track_info['cnts'], track_info['Disk Size'], ch_cnt, track_info['Duration']))
                        #check_map[track_id].setObjectName = '%s:%s' % (drive_id, track_id)
                        #layout.addWidget(check_map[track_id])
                    except KeyError:
                        pass    #<  ignore ? chapters
                self.ui_map[drive_id]['disc_info'].resizeColumnToContents(0)
                self.ui_map[drive_id]['disc_info'].resizeColumnToContents(1)
            return layout
        disc_info = self._send_cmd('disc_info|%s' % (drive_id))
        return [disc_info_thread, self, disc_info]
    
    @staticmethod
    def get_size(size_str):
        ##  Sort by size
        fn, size = size_str.rsplit(':',1)
        value, unit = size.split(' ')
        multiplier = make_mkv_client.SIZE_MULT[unit]
        return float(value)*multiplier
    
    def _send_cmd(self,cmd):
        ##  Send command to remote server, wait for reply
        #   @param  Str cmd Command to send
        #   @return Obj JSON decoded server reply
        try:
            self.socket.send( bytearray(cmd + u'[>#!>]', 'utf-8') )
            print 'Sent "%s"' % cmd
            data = self._socket_recv()
            try:
                return json.loads(data)
            except ValueError as e:
                raise ValueError('%s Caused by data:\n\n%s' % (e,data))
        except socket.error:
            raise Exception('Host Went Away!')
        
    def _socket_recv(self):
        ##  Listen to conn for data
        #   @return Str Rcvd data
        data_chunk, recvd_data = '',[self.socket_buffer]
        self.socket_buffer = ''
        self.locked.acquire()
        while 1:
            print 'Receiving Data...'
            data_chunk = self.socket.recv(self.RECV_CHUNKS)
            print 'PROCESSING: "%s"' % data_chunk
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
        
class worker_thread(QtCore.QThread):
    ##  Generic worker thread
    finished = QtCore.pyqtSignal(list)
    def __init__(self, function, *args, **kwargs):
        ##  Init
        #   @param  Function    function    Function to run on start
        #   @param  List        *args       args to pass to function
        #   @param  *Dict       **kwargs    Kerword args to pass to function
        super(worker_thread, self).__init__()
        #self.finished.connect(fin_function)
        self.function = function
        self.args = args
        self.kwargs = kwargs
   
    def __del__(self):
        ##  No exception
        self.wait()
   
    def run(self):
        ##  Thread finished, run function with args
        ret = self.function(*self.args,**self.kwargs)
        if ret is None: ret = []
        self.finished.emit(ret)
  
class make_mkv_client_gui(QtGui.QWidget):
    ##  Gui related functions
    def __init__(self, x=100, y=100, w=1200, h=800, center=True, icon=False):
        ##  Init
        ##  @todo   Document
        super(make_mkv_client_gui, self).__init__()
        self.setGeometry(x,y,w,h)
        self.setWindowTitle('Remote MakeMKV Client')
        self.threads = []
        #icon = QtGui.QIcon(os.path.join('c:/','xampp','htdocs','ITL_HTML','trunk','shared_data','images','datait_logo.png'))
        if icon:
            self.setWindowIcon(icon)
        self.main_layout = QtGui.QVBoxLayout()
        #self.systray = wins_systray(self,icon)
        #self.main_layout.addStretch(1)
        self.setLayout(self.main_layout)
        self.setObjectName('main_window')
        if center: self.center()
        self.show()
    
    def center(self):
        ##  Center window on screen
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    @staticmethod
    def group_box(title, add_widgets=[], layout_type='v'):
        ##  Returns a groupbox
        #   @param  Str     title       Title text
        #   @param  List    add_widgets Init with these widgets
        #   @param  Str     layout_type h or v
        #   @return  QtGui.QGroupBox
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
        #   Create a button, thread it
        #   @param  Str         txt             Button Text
        #   @param  Function    ret_function    Thread complete function
        #   @param  Function    function        Thread start function
        #   @param  List        *args           Args to pass to function
        #   @param  Dict        **kwargs        KW Args to pass to function
        #   @return QtGui.QPushButton
        button = QtGui.QPushButton(txt)
        self.threads.append(worker_thread(function, *args, **kwargs))
        button.clicked.connect( self.threads[-1].start )
        self.threads[-1].finished.connect(ret_function)
        return button
    
    @staticmethod
    def clear_layout(layout, preserve_el=None, disable=False, enable=False):
        ##  Clear a layout recursively
        #   @param  QLayout layout      Layout
        #   @param  Int     preserve_el Element index to preserve
        #   @param  Bool    disable     Disable instead of remove?
        for i in reversed(range(layout.count())):
            if i != preserve_el:
                item = layout.itemAt(i)
                if isinstance(item, QtGui.QWidgetItem):
                    if disable:
                        item.widget().setEnabled(False)
                    elif enable:
                        item.widget().setEnabled(True)
                    else:
                        item.widget().close()
                elif isinstance(item, QtGui.QSpacerItem):
                    pass
                else:
                    make_mkv_client_gui.clear_layout(item.layout(), disable=disable)
                if not disable:
                    layout.removeItem(item) 

class makemkv_systray(QtGui.QSystemTrayIcon):
    ##  Systray Class
    def __init__(self, parent, icon, _show=True):
        ##  Init
        #   @param  QtGui.QWidget   parent  Parent obj
        #   @param  QtGui.QIcon     icon    Icon
        super(makemkv_systray, self).__init__(icon, parent)
        #QtGui.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtGui.QMenu(parent)
        exitAction = menu.addAction("Exit")
        self.setContextMenu(menu)
        if _show:
            self.show()
    def tray_message(self,title,message):
        ##  Show a tray icon message
        #   @param  Str title   Title of message
        #   @param  Str message Message Str 
        self.showMessage(title,message) 
    
##  Do it now!
if __name__ == '__main__':
    make_mkv_client('localhost')
    