#!/usr/bin/env python
##  Client for make_mkv.py
#         
#   GUI
#    
#   @author     David Lasley, dave -at- dlasley -dot- net
#   @website    http://code.google.com/p/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id$
#
#   @requires-python-packages   pyqt4, socksipy-branch
from gui import *
import math

import sys
import os
dirname = os.path.dirname(__file__)
sys.path.append(os.path.join(dirname, "../.."))
import remote_makemkv.shared.socket_functions as socket_functions
from remote_makemkv.video_renaming.rename import rename
from remote_makemkv import OUT_PATH,DRIVE_NAME_MAPS,OUTLIER_MODIFIER,logging

class make_mkv_client(object):
    ##  Main class
    SIZE_MULT = dict(KB=2**10, MB=2**20, GB=2**30)
    def __init__(self, proxy_host=None, proxy_port=8080):
        ##  Init
        ##  @param  Str proxy_host  SOCKS proxy hsot
        ##  @param  Int proxy_port  SOCKS proxy port
        self.rip_button_map = {}
        self.ui_map = {}
        self.scan_operations = 0
        self.init_ui()
        SOCKET_ARGS = {
            "scan_drives"   :   self.scan_drives,
            "disc_info"     :   self.disc_info,
            "rip"           :   self.rip,
            "iso"           :   self.iso,
        }
        self.socket = socket_functions.custom_client(SOCKET_ARGS)
        self.recv_thread = worker_thread(self.socket.recv)
        self.recv_thread.finished.connect(self.thread_finish)
        self.recv_thread.start()
        sys.exit(self.app.exec_())
    
    #   UI Related
    
    def init_ui(self):
        ##  Init The GUI
        self.app = QtGui.QApplication(sys.argv)
        icon = QtGui.QIcon('./mkv_icon_all.png')
        self.gui = make_mkv_client_gui(icon=icon)
        self.gui.setStyleSheet(self.gui.CSS)
        def click_all_buttons():
            for x in self.rip_button_map.values(): x.clicked.emit(True)
        layout = QtGui.QHBoxLayout()
        self.systray = makemkv_systray(self.gui,icon)
        self.output_dir = QtGui.QLineEdit(OUT_PATH)
        qgrid = QtGui.QGridLayout()
        out_label = QtGui.QLabel('Output Dir:')
        out_label.setAlignment(QtCore.Qt.AlignRight)
        qgrid.addWidget(out_label,1,0,1,1)
        qgrid.addWidget(self.output_dir,1,1,1,3)
        self.refresh_all_button = self.gui.button('Refresh Drive(s)', self.thread_finish, self._scan_drives)
        self.refresh_all_button.setObjectName('btn_refresh_drives')
        self.ui_map['refresh_all'] = self.refresh_all_button
        qgrid.addWidget(self.refresh_all_button,2,2,1,2)
        self.ui_map['rip_all'] = self.gui.button('Rip Selected', self.thread_finish, click_all_buttons)
        qgrid.addWidget(self.ui_map['rip_all'],2,0,1,2)
        disc_layout = QtGui.QHBoxLayout()
        disc_layout.setObjectName('lout_all_discs')
        qgrid.addLayout(disc_layout,3,0,5,4)
        credits_label = QtGui.QLabel(u'MakeMKV \u00A9 2008-2013 GuinpinSoft inc - <a href="http://www.makemkv.com/buy">http://www.makemkv.com/buy</a><br>Remote MakeMKV GUI written by David Lasley - <a href="http://code.google.com/p/remote-makemkv/">http://code.google.com/p/remote-makemkv/</a> and licensed under GNU GPL v3.')
        credits_label.setAlignment(QtCore.Qt.AlignCenter)
        credits_label.setTextFormat(QtCore.Qt.RichText)
        credits_label.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
        qgrid.addWidget(credits_label,9,0,1,4)
        self.ui_map['all_discs'] = disc_layout
        self.gui.main_layout.addLayout(qgrid)
    
    def thread_finish(self, thread_return):
        ##  Generic Thread End-Point
        #   @param  List    input_list  Thread output

        #   Scan drives finished
        logging.debug('thread_finish(%s)' % thread_return['cmd'])
        if thread_return['cmd'] == 'scan_drives':
            self.refresh_buttons = {}
            layout = QtGui.QHBoxLayout()
            for drive_id, movie in thread_return['return'].iteritems():
                try:
                    drive_name = DRIVE_NAME_MAPS[drive_id]
                except KeyError:
                    drive_name = drive_id
                self.ui_map[drive_id] = {}
                self.ui_map[drive_id]['get_info'] = self.gui.button('Rescan Drive', self.thread_finish, self._disc_info, drive_id)
                self.ui_map[drive_id]['get_info'].setObjectName('btn_disc_info:%s'%drive_id)
                self.ui_map[drive_id]['get_info'].setToolTip('Scan this disc for track information')
                self.ui_map[drive_id]['get_info'].clicked.emit(True)
                self.ui_map[drive_id]['disc_box'] = self.gui.group_box('%s - %s'%(drive_name,movie))
                self.ui_map[drive_id]['disc_box'].setObjectName('disc_box:%s'%drive_id)
                self.ui_map[drive_id]['disc_box'].setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
                self.ui_map[drive_id]['disc_layout'] = QtGui.QVBoxLayout()
                self.ui_map[drive_id]['disc_box'].setLayout(self.ui_map[drive_id]['disc_layout'])
                self.ui_map[drive_id]['disc_layout'].addWidget(self.ui_map[drive_id]['get_info'],1)
                layout.addWidget(self.ui_map[drive_id]['disc_box'])
            self._reset_button_refresh(add_operation=False)
            main_layout = self.gui.main_layout.findChild(object,'lout_all_discs')
            make_mkv_client_gui.clear_layout(main_layout)
            main_layout.addLayout(layout)
            
        #   Disc Info finish  
        elif thread_return['cmd'] == 'disc_info':
            
            disc_info = thread_return['return']
            drive_id = disc_info['disc_id']
            self._reset_button_refresh(drive_id,False)
        
            def loop_checks(drive_id,modify_checks=False):
                checked_tracks = []
                for track_id,check_box in self.ui_map[drive_id]['check_map'].iteritems():
                    if modify_checks:
                        if self.ui_map[drive_id]['check_all'].checkState() == QtCore.Qt.Checked:
                            check_box.setCheckState(0,QtCore.Qt.Checked)
                        else:
                            check_box.setCheckState(0,QtCore.Qt.Unchecked)
                    else: 
                        if check_box.checkState(0):
                            checked_tracks.append(track_id)
                        out_path = '%s/%s' % (self.output_dir.text(), self.ui_map[drive_id]['new_name'].text())
                if modify_checks:
                    return True
                else:
                    return [out_path,checked_tracks]
            #   @todo - Get rid of this
            def _lambda_loop(drive_id,modify_checks=False):
                return lambda: loop_checks(drive_id,modify_checks)
            #   Get Drive Name
            try:
                drive_name = DRIVE_NAME_MAPS[drive_id]
            except KeyError:
                drive_name = drive_id
                
            layout = self.ui_map[drive_id]['disc_layout']
            make_mkv_client_gui.clear_layout(layout,0)
            try:
                self.ui_map[drive_id]['disc_box'].setTitle(u'%s - %s' % (drive_name, disc_info['disc']['Volume Name']))    #<  If it changed
            except KeyError:
                self.ui_map[drive_id]['disc_box'].setTitle(u'%s - None' % (drive_name))    #<  No Disc
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
                    
                #   New Name Text Area
                self.ui_map[drive_id]['new_name'] = QtGui.QLineEdit(rename.format_season(sanitized))
                self.ui_map[drive_id]['new_name'].setToolTip('Output folder')
                layout.addWidget(self.ui_map[drive_id]['new_name'])
                
                #   Check All
                self.ui_map[drive_id]['check_all'] = QtGui.QCheckBox('Toggle Checks')
                self.ui_map[drive_id]['check_all'].stateChanged.connect( _lambda_loop(drive_id, True) )
                layout.addWidget(self.ui_map[drive_id]['check_all'])
                
                #   Disc Info Tree Widget
                self.ui_map[drive_id]['disc_info'] = QtGui.QTreeWidget()
                self.ui_map[drive_id]['disc_info'].setColumnCount(2)
                self.ui_map[drive_id]['disc_info'].setHeaderLabels(['Type','Value'])
                #self.ui_map[drive_id]['disc_info'].setMinimumSize(320,500)
                #self.ui_map[drive_id]['disc_info'].setMaximumSize(8000,8000)
                self.ui_map[drive_id]['disc_info'].setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
                layout.addWidget(self.ui_map[drive_id]['disc_info'])
                
                #   Rip buttons
                btns = QtGui.QHBoxLayout()
                layout.addLayout(btns)
                self.ui_map[drive_id]['iso_btn'] = self.gui.button('To ISO', self.thread_finish, self._iso, drive_id)
                self.ui_map[drive_id]['iso_btn'].setToolTip('Decrypt all titles on disc and save to an ISO file.')
                btns.addWidget(self.ui_map[drive_id]['iso_btn'])
                self.ui_map[drive_id]['rip_btn'] = self.gui.button('Rip', self.thread_finish, self._rip, drive_id, _lambda_loop(drive_id))
                self.ui_map[drive_id]['rip_btn'].setToolTip('Rip selected titles to hard drive.')
                btns.addWidget(self.ui_map[drive_id]['rip_btn'])
                self.rip_button_map[drive_id] = self.ui_map[drive_id]['rip_btn']

                #   Fill the disc info Tree Widget
                self.ui_map[drive_id]['check_map'] = {}
                row_num = 0
                
                #   Sort Everything
                sort_lines,sizes = [],[]
                for track_id, track_info in disc_info['tracks'].iteritems():
                    sort_lines.append('%s:%s' % (track_id,track_info['Disk Size']))
                    sizes.append(make_mkv_client.get_size(track_info['Disk Size']))
                sort_lines.sort(key=make_mkv_client.get_size) #<  Sort by size
                
                #   Calculate outliers for coloring
                sizes = sorted(sizes)
                ##  Upper quartile
                try:
                    high_mid = ( len( sizes ) - 1 ) * 0.75
                    uq = sizes[ high_mid ]
                except TypeError:   #<  There were an even amount of values
                    ceil = int( math.ceil( high_mid ) )
                    floor = int( math.floor( high_mid ) )
                    uq = ( sizes[ ceil ] + sizes[ floor ] ) / 2
                low_num = uq * OUTLIER_MODIFIER #<   If OUTLIER_MODIFIER lower than the uq, probably not a good file...
                
                #   Fill the disc info Tree Widget
                self.ui_map[drive_id]['check_map'] = {}
                row_num = 0
                for sorted_track in reversed(sort_lines):
                    track_id = sorted_track.rsplit(':',1)[0]
                    track_info = disc_info['tracks'][track_id]
                    try:
                        ch_cnt = track_info['Chapter Count']
                    except KeyError:
                        ch_cnt = '?'
                        
                    self.ui_map[drive_id]['check_map'][track_id] = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['disc_info'])
                    self.ui_map[drive_id]['check_map'][track_id].setText(0,'Title %s' % track_id)
                    self.ui_map[drive_id]['check_map'][track_id].setText(1,track_info['Output Filename'])
                    self.ui_map[drive_id]['check_map'][track_id].setExpanded(True)
                    if make_mkv_client.get_size(track_info['Disk Size']) < low_num:
                        self.ui_map[drive_id]['check_map'][track_id].setBackground(0,self.gui.STYLES['red'])
                        self.ui_map[drive_id]['check_map'][track_id].setCheckState(0, QtCore.Qt.Unchecked )
                    else:
                        self.ui_map[drive_id]['check_map'][track_id].setBackground(0,self.gui.STYLES['green'])
                        self.ui_map[drive_id]['check_map'][track_id].setCheckState(0, QtCore.Qt.Checked )
                    
                    child = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                    child.setText(0, 'Size')
                    child.setText(1, track_info['Disk Size'])
                    child = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                    child.setText(0, 'Chptrs')
                    child.setText(1, ch_cnt)
                    
                    sorted_tracks = {'Audio':{},'Video':{},'Subtitles':{}}
                    for key,val in track_info['track_parts'].iteritems():
                        sorted_tracks[val['Type']][key] = val

                    for typ,cnt in track_info['cnts'].iteritems():
                        child = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                        child.setText(0, typ)
                        child.setText(1, str(cnt))
                        for _key,_val in sorted_tracks[typ].iteritems():
                            _child = QtGui.QTreeWidgetItem(child)
                            _child.setText(0,_key)
                            if type(_val) == dict:
                                try:
                                    _child.setText(1,_val['Name'])
                                except KeyError:
                                    try:
                                        _child.setText(1,_val['Lng Name'])
                                    except KeyError:
                                        _child.setText(1,'N/A')
                                for _key_,_val_ in _val.iteritems():
                                    _child_ = QtGui.QTreeWidgetItem(_child)
                                    _child_.setText(0,_key_)
                                    _child_.setText(1,_val_)
                            else:
                                _child.setText(1,_val)
                                
                self.ui_map[drive_id]['disc_info'].resizeColumnToContents(0)
                self.ui_map[drive_id]['disc_info'].resizeColumnToContents(1)
                
        #   Iso/Rip Finish
        elif thread_return['cmd'] == 'rip' or thread_return['cmd'] == 'iso':
            
            drive_id = thread_return['return']['disc_id']
            layout = self.ui_map[drive_id]['disc_layout']
            make_mkv_client_gui.clear_layout(layout,enable=True)
            del thread_return['return']['disc_id']
            #output = []
            for track_id,bol_success in thread_return['return'].iteritems():
                track_name = self.ui_map[drive_id]['check_map'][track_id].text(1)
                if bol_success:
                    self.ui_map[drive_id]['check_map'][track_id].setBackground(0,self.gui.STYLES['green'])
                    self.ui_map[drive_id]['check_map'][track_id].setBackground(1,self.gui.STYLES['green'])
                    self.ui_map[drive_id]['check_map'][track_id].setText(1,'%s - Success' % track_name)
                else:
                    self.ui_map[drive_id]['check_map'][track_id].setBackground(0,self.gui.STYLES['red'])
                    self.ui_map[drive_id]['check_map'][track_id].setBackground(1,self.gui.STYLES['red'])
                    self.ui_map[drive_id]['check_map'][track_id].setText(1,'%s - Failed' % track_name)
                #output.append('Track %s: %s' % (track_id, repr(bol_success)))
            self._reset_button_refresh(drive_id,False)
            #make_mkv_client_gui.clear_layout(layout,enable=True)
            #layout.addWidget(make_mkv_client_gui.group_box('Rip Output', [QtGui.QLabel('Drive ID: %s\n%s' % (drive_id, '\n'.join(output)))]))
            
        else:
            pass

    def _reset_button_refresh(self, drive_id=None, add_operation=True):
        ##  Reset the global refresh button if neccessita
        #   Enable/Disable Single Disc Buttons
        #   Also throws tray_message to alert of disc operation completion
        if add_operation:
            self.scan_operations+=1
            not_currently_scanning = False
        else:
            self.scan_operations-=1
            not_currently_scanning = self.scan_operations==0
        self.ui_map['rip_all'].setEnabled( not_currently_scanning )
        self.ui_map['refresh_all'].setEnabled( not_currently_scanning )
        if drive_id is not None:
            for btn_name in ('iso_btn','rip_btn','get_info'):    #<  Button types to disable
                try:
                    self.ui_map[drive_id][btn_name].setEnabled(not add_operation)
                except KeyError:    #<  button doesn't exist yet
                    pass
        if not_currently_scanning:
            self.systray.tray_message('Operations Complete!','All Current Disc Operations Have Completed.')
    
    #   Thread/Socket functions
    
    def scan_drives(self, drives):
        ##  Once the command has completed, this manipulates the GUI
        #   @param  Dict    drives  Drives [sys location (/dev/sr#)] => Movie Name
        #   @return QtGui.QHBoxLayout   Layout of disc info w/ checks
        cmd = drives['cmd']
        del drives['cmd']
        logging.debug('Emitting Finish(%s)' % repr({'return':drives,'cmd':cmd}))
        self.recv_thread.finished.emit( {'return':drives,'cmd':cmd} )

    def _scan_drives(self):
        ##  Wrapper function for scanning the drives
        #   @return List    [Scan_thread_function, scan_server_command]
        self._reset_button_refresh()
        return self.socket.send_str('scan_drives')
    
    def disc_info(self,disc_info):
        cmd = disc_info['cmd']
        del disc_info['cmd']
        self.recv_thread.finished.emit( {'return':disc_info,'cmd':cmd} )
    def _disc_info(self,drive_id):
        ##  Wrapper function for getting disc info
        #   @param  Int         drive_id    Drive ID to get
        #   @todo   Document this
        self._reset_button_refresh(drive_id)
        return self.socket.send_str('disc_info|%s' % (drive_id))
    
    def rip(self,rip_information):
        ##  Ripping thread complete function
        #   @todo document this
        cmd = rip_information['cmd']
        del rip_information['cmd']
        self.recv_thread.finished.emit( {'return':rip_information,'cmd':cmd} )
    def _rip(self,drive_id,rip_info):
        ##  Wrapper function for ripping tracks
        #   @param  Str     drive_id    Drive id (sys location /dev/sr#)
        #   @param  Lambda  rip_info    Lamba function to get the checked boxes..ghetto, I know
        #   @return List    [rip_thread_complete_function, rip_server_command, movie_name_override_text, drive_id]
        if len(rip_info()[1]) > 0:
            self._reset_button_refresh(drive_id)
            layout = self.ui_map[drive_id]['disc_layout']
            make_mkv_client_gui.clear_layout(layout,0,True)
            return self.socket.send_str('rip|%s|%s|%s' % (rip_info()[0], drive_id, ','.join(rip_info()[1])))
        
    def iso(rip_information):
        ##  Ripping thread complete function
        #   @todo document this
        cmd = rip_information['cmd']
        del rip_information['cmd']
        self.recv_thread.finished.emit( {'return':rip_information,'cmd':cmd} )
    def _iso(self,drive_id):
        ##  Wrapper function for ripping tracks
        #   @param  Str     drive_id    Drive id (sys location /dev/sr#)
        #   @param  Lambda  rip_info    Lamba function to get the checked boxes..ghetto, I know
        #   @return List    [rip_thread_complete_function, rip_server_command, movie_name_override_text, drive_id]
        self._reset_button_refresh(drive_id)
        layout = self.ui_map[drive_id]['disc_layout']
        make_mkv_client_gui.clear_layout(layout,0,True)
        return self.socket.send_str('iso|%s/%s|%s' % (self.output_dir.text(), self.ui_map[drive_id]['new_name'].text(), drive_id))
    
    @staticmethod
    def get_size(size_str):
        ##  Get the file size from a str repr
        try:    #<  Split from disc ids if necessary
            fn, size = size_str.rsplit(':',1)
        except ValueError:  
            size = size_str
        value, unit = size.split(' ')
        multiplier = make_mkv_client.SIZE_MULT[unit]
        return float(value)*multiplier
    
##  Do it now!
if __name__ == '__main__':
    make_mkv_client()
    