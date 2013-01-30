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
        def click_all_buttons():
            for x in self.rip_button_map.values(): x.clicked.emit(True)
        #   App related
        self.app = QtGui.QApplication(sys.argv)
        icon = QtGui.QIcon('./mkv_icon_all.png')
        self.gui = make_mkv_client_gui(icon=icon)
        self.gui.setStyleSheet(self.gui.CSS)
        self.systray = makemkv_systray(self.gui,icon)
        qgrid = QtGui.QGridLayout()
        ##  Top Section
        #   Output Dir
        top_hbox = QtGui.QHBoxLayout()
        qgrid.addLayout(top_hbox,1,0,1,4)
        out_label = QtGui.QLabel('Output Dir:')
        #out_label.setAlignment(QtCore.Qt.AlignRight)
        top_hbox.addWidget(out_label)
        self.ui_map['output_dir'] = QtGui.QLineEdit(OUT_PATH)
        top_hbox.addWidget(self.ui_map['output_dir'])
        #   Rip All
        self.ui_map['rip_all'] = self.gui.button('Rip Selected', self.thread_finish, click_all_buttons)
        self.ui_map['rip_all'].setEnabled(False)
        top_hbox.addWidget(self.ui_map['rip_all'])
        #   Refresh All
        self.ui_map['refresh_all'] = self.gui.button('Refresh Drive(s)', self.thread_finish, self._scan_drives)
        self.ui_map['refresh_all'].setObjectName('btn_refresh_drives')
        top_hbox.addWidget(self.ui_map['refresh_all'])
        #   Disc UI
        self.ui_map['all_discs'] = QtGui.QHBoxLayout()
        self.ui_map['all_discs'].setObjectName('lout_all_discs')
        qgrid.addLayout(self.ui_map['all_discs'],2,0,5,4)
        #   Bottom Credit Line
        credits_label = QtGui.QLabel(u'MakeMKV \u00A9 2008-2013 GuinpinSoft inc - <a href="http://www.makemkv.com/buy">http://www.makemkv.com/buy</a><br>Remote MakeMKV GUI written by David Lasley - <a href="http://code.google.com/p/remote-makemkv/">http://code.google.com/p/remote-makemkv/</a> and licensed under GNU GPL v3.')
        credits_label.setAlignment(QtCore.Qt.AlignCenter)
        credits_label.setTextFormat(QtCore.Qt.RichText)
        credits_label.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
        qgrid.addWidget(credits_label,8,0,1,4)
        self.gui.main_layout.addLayout(qgrid)
    
    def thread_finish(self, thread_return):
        ##  Generic Thread End-Point (GUI UPDATES)
        #   @param  Dict    thread_return  Thread output
        logging.debug('thread_finish(%s)' % thread_return['cmd'])
        #   Define functions
        def scan_drives(thread_return):
            #   scan_drives endpoint
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
        
        def disc_info(thread_return):
            # disc_info endpoint
            disc_info = thread_return['return']
            drive_id = disc_info['disc_id']
            self._reset_button_refresh(drive_id,False)
            #   Checkbox functions
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
                        out_path = '%s/%s' % (self.ui_map['output_dir'].text(), self.ui_map[drive_id]['new_name'].text())
                if modify_checks:
                    return True
                else:
                    return [out_path,checked_tracks]
            def _lambda_loop(drive_id,modify_checks=False):
                #   @todo - Get rid of this
                return lambda: loop_checks(drive_id,modify_checks)
            
            #   Match Drive Name
            try:
                drive_name = DRIVE_NAME_MAPS[drive_id]
            except KeyError:
                drive_name = drive_id
                
            layout = self.ui_map[drive_id]['disc_layout']
            make_mkv_client_gui.clear_layout(layout)
            self.ui_map[drive_id]['get_info'] = self.gui.button('Rescan Drive', self.thread_finish, self._disc_info, drive_id)
            self.ui_map[drive_id]['get_info'].setObjectName('btn_disc_info:%s'%drive_id)
            self.ui_map[drive_id]['get_info'].setToolTip('Scan this disc for track information')
            
            #   Disc Title (or lack thereof)
            try:
                self.ui_map[drive_id]['disc_box'].setTitle(u'%s - %s' % (drive_name, disc_info['disc']['Volume Name']))    #<  If it changed
            except KeyError:
                self.ui_map[drive_id]['disc_box'].setTitle(u'%s - None' % (drive_name))    #<  No Disc
            #   If there are tracks, valid disc.
            check_map, sanitized = {}, {}
            if len(disc_info['tracks']) > 0:
                #   Sanitize the name using all avail info
                for i in ('Volume Name','Tree Info','Name'):
                    try:
                        sanitize = rename.full_sanitize(disc_info['disc'][i])
                        for key,val in sanitize[1].iteritems():
                            sanitized[key] = val
                        sanitized['sanitized'] = sanitize[0]
                    except KeyError:    #<  name type didn't exist for some reason..
                        pass
                
                #   Folder Name Text Area
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
                self.ui_map[drive_id]['disc_info'].setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
                layout.addWidget(self.ui_map[drive_id]['disc_info'])
                #   Bottom buttons
                btns = QtGui.QHBoxLayout()
                layout.addLayout(btns)
                btns.addWidget(self.ui_map[drive_id]['get_info'])
                self.ui_map[drive_id]['iso_btn'] = self.gui.button('To ISO', self.thread_finish, self._iso, drive_id)
                self.ui_map[drive_id]['iso_btn'].setToolTip('Decrypt all titles on disc and save to an ISO file.')
                btns.addWidget(self.ui_map[drive_id]['iso_btn'])
                self.ui_map[drive_id]['rip_btn'] = self.gui.button('Rip', self.thread_finish, self._rip, drive_id, _lambda_loop(drive_id))
                self.ui_map[drive_id]['rip_btn'].setToolTip('Rip selected titles to hard drive.')
                btns.addWidget(self.ui_map[drive_id]['rip_btn'])
                self.rip_button_map[drive_id] = self.ui_map[drive_id]['rip_btn']
                
                #   Sort Tracks By Size, also make a size array for mathing
                sort_lines,sizes = [],[]
                for track_id, track_info in disc_info['tracks'].iteritems():
                    sort_lines.append('%s:%s' % (track_id,track_info['Disk Size']))
                    sizes.append(make_mkv_client.get_size(track_info['Disk Size']))
                sort_lines.sort(key=make_mkv_client.get_size) #<  Sort by size
                
                #   Calculate outliers for title selection
                sizes = sorted(sizes)
                ##  Upper quartile
                try:
                    high_mid = ( len( sizes ) ) * 0.75
                    uq = sizes[ high_mid ]
                except TypeError:   #<  There were an even amount of values
                    ceil = int( math.ceil( high_mid ) )
                    floor = int( math.floor( high_mid ) )
                    uq = ( sizes[ ceil ] + sizes[ floor ] ) / 2
                low_num = uq * OUTLIER_MODIFIER #<   If OUTLIER_MODIFIER lower than the uq, probably not a good file...
                
                #   Fill the disc info Tree Widget
                self.ui_map[drive_id]['check_map'] = {}
                for sorted_track in reversed(sort_lines):
                    #   Global Title Info
                    track_id = sorted_track.rsplit(':',1)[0]
                    track_info = disc_info['tracks'][track_id]
                    try:
                        ch_cnt = track_info['Chapter Count']
                    except KeyError:
                        ch_cnt = '?'
                    #   Main Title
                    self.ui_map[drive_id]['check_map'][track_id] = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['disc_info'])
                    self.ui_map[drive_id]['check_map'][track_id].setText(0,'Title %s' % track_id)
                    self.ui_map[drive_id]['check_map'][track_id].setText(1,track_info['Output Filename'])
                    self.ui_map[drive_id]['check_map'][track_id].setExpanded(True)
                    #   Auto Title Selection
                    if make_mkv_client.get_size(track_info['Disk Size']) < low_num or ch_cnt == '?':
                        self.ui_map[drive_id]['check_map'][track_id].setBackground(0,self.gui.STYLES['red'])
                        self.ui_map[drive_id]['check_map'][track_id].setCheckState(0, QtCore.Qt.Unchecked )
                    else:
                        self.ui_map[drive_id]['check_map'][track_id].setBackground(0,self.gui.STYLES['green'])
                        self.ui_map[drive_id]['check_map'][track_id].setCheckState(0, QtCore.Qt.Checked )
                    #   Title Attributes (size,chpts)
                    child = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                    child.setText(0, 'Size')
                    child.setText(1, track_info['Disk Size'])
                    child = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                    child.setText(0, 'Chptrs')
                    child.setText(1, ch_cnt)
                    #   Sort the tracks into their types
                    sorted_tracks = {'Audio':{},'Video':{},'Subtitles':{}}
                    for key,val in track_info['track_parts'].iteritems():
                        sorted_tracks[val['Type']][key] = val
                    #   Loop track types
                    for typ,cnt in track_info['cnts'].iteritems():
                        child = QtGui.QTreeWidgetItem(self.ui_map[drive_id]['check_map'][track_id])
                        child.setText(0, typ)   #   Track type
                        child.setText(1, str(cnt))  #   Cnt of tracks in this type
                        #   Loop Tracks
                        for inner_track_id,track_data in sorted_tracks[typ].iteritems():
                            _child = QtGui.QTreeWidgetItem(child)
                            _child.setText(0,inner_track_id)
                            if type(track_data) == dict:
                                #   Try to get a name for the track
                                try:
                                    _child.setText(1,track_data['Name'])
                                except KeyError:
                                    try:
                                        _child.setText(1,track_data['Lng Name'])
                                    except KeyError:
                                        _child.setText(1,'N/A')
                                #   Loop track attributes
                                for attr_name,attr_val in track_data.iteritems():
                                    _child_ = QtGui.QTreeWidgetItem(_child)
                                    _child_.setText(0,attr_name)
                                    _child_.setText(1,attr_val)
                            else:
                                _child.setText(1,track_data)
                #   Size the columns           
                self.ui_map[drive_id]['disc_info'].resizeColumnToContents(0)
                self.ui_map[drive_id]['disc_info'].resizeColumnToContents(1)
            else:   #<  Rescan button
                layout.addWidget(self.ui_map[drive_id]['get_info'])
               
        def rip(thread_return):
            #   Rip endpoint
            self._reset_button_refresh(drive_id,False)
            drive_id = thread_return['return']['disc_id']
            layout = self.ui_map[drive_id]['disc_layout']
            make_mkv_client_gui.clear_layout(layout,enable=True)
            del thread_return['return']['disc_id']
            #   Loop and show the results
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
            #   Size the columns           
            self.ui_map[drive_id]['disc_info'].resizeColumnToContents(0)
            self.ui_map[drive_id]['disc_info'].resizeColumnToContents(1)
                    
        def iso(thread_return):
            #   ISO endpoint
            self._reset_button_refresh(drive_id,False)
            drive_id = thread_return['return']['disc_id']
            layout = self.ui_map[drive_id]['disc_layout']
            make_mkv_client_gui.clear_layout(layout,enable=True)
            #   @todo
        
        #   Map and call
        map_it = {
            'disc_info'     :   disc_info,
            'scan_drives'   :   scan_drives,
            'rip'           :   rip,
            'iso'           :   iso,
        }
        return map_it[thread_return['cmd']](thread_return)

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
            self.systray.tray_message('All Current Disc Operations Have Completed.')
    
    #   Button functions
    
    def scan_drives(self, drives):
        ##  Once the command has completed, this emits the finished() signal
        cmd = drives['cmd']
        del drives['cmd']
        logging.debug('Emitting Finish(%s)' % repr({'return':drives,'cmd':cmd}))
        self.recv_thread.finished.emit( {'return':drives,'cmd':cmd} )

    def _scan_drives(self):
        ##  Wrapper function for scanning the drives
        self._reset_button_refresh()
        return self.socket.send_str('scan_drives')
    
    def disc_info(self,disc_info):
        ##  Once the command has completed, this emits the finished() signal
        cmd = disc_info['cmd']
        del disc_info['cmd']
        self.recv_thread.finished.emit( {'return':disc_info,'cmd':cmd} )
    def _disc_info(self,drive_id):
        ##  Wrapper function for getting disc info
        #   @param  Str     drive_id    Drive id (sys location /dev/sr#)
        self._reset_button_refresh(drive_id)
        return self.socket.send_str('disc_info|%s' % (drive_id))
    
    def rip(self,rip_information):
        ##  Once the command has completed, this emits the finished() signal
        cmd = rip_information['cmd']
        del rip_information['cmd']
        self.recv_thread.finished.emit( {'return':rip_information,'cmd':cmd} )
    def _rip(self,drive_id,rip_info):
        ##  Wrapper function for ripping tracks
        #   @param  Str     drive_id    Drive id (sys location /dev/sr#)
        #   @param  Lambda  rip_info    Lamba function to get the checked boxes..ghetto, I know
        if len(rip_info()[1]) > 0:
            self._reset_button_refresh(drive_id)
            layout = self.ui_map[drive_id]['disc_layout']
            make_mkv_client_gui.clear_layout(layout,disable=True)
            return self.socket.send_str('rip|%s|%s|%s' % (rip_info()[0], drive_id, ','.join(rip_info()[1])))
        
    def iso(rip_information):
        ##  Once the command has completed, this emits the finished() signal
        cmd = rip_information['cmd']
        del rip_information['cmd']
        self.recv_thread.finished.emit( {'return':rip_information,'cmd':cmd} )
    def _iso(self,drive_id):
        ##  Wrapper function for ripping tracks
        #   @param  Str     drive_id    Drive id (sys location /dev/sr#)
        self._reset_button_refresh(drive_id)
        layout = self.ui_map[drive_id]['disc_layout']
        make_mkv_client_gui.clear_layout(layout,disable=True)
        return self.socket.send_str('iso|%s/%s|%s' % (self.ui_map['output_dir'].text(), self.ui_map[drive_id]['new_name'].text(), drive_id))
    
    @staticmethod
    def get_size(size_str):
        ##  Return file size in bytes
        try:    #<  Split from disc ids if necessary
            fn, size = size_str.rsplit(':',1)
        except ValueError:  
            size = size_str
        value, unit = size.split(' ')
        multiplier = make_mkv_client.SIZE_MULT[unit]
        return float(value)*multiplier
    
##  Do it now!
if __name__ == '__main__':
    make_mkv_client('localhost')
    