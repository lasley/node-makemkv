#!/usr/bin/env python
##  GUI classes for make_mkv_client
#   @author     David Lasley, dave -at- dlasley -dot- net
#   @website    http://code.google.com/p/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id$
#
#   @requires-python-packages   pyqt4, socksipy-branch

from PyQt4 import QtGui, QtCore
import logging

class worker_thread(QtCore.QThread):
    ##  Generic worker thread
    finished = QtCore.pyqtSignal(dict)
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
        logging.debug('End Thread')
        ret = self.function(*self.args,**self.kwargs)
        #if ret is None: ret = []
        #self.finished.emit(ret)
  
class make_mkv_client_gui(QtGui.QWidget):
    CSS = '''{
        #green{
            background-collor: green;
        }
        #yellow{
            background-collor: yellow;
        }
        #orange{
            background-color: orange;
        }
        #red{
            background-color: red;
        }
    }'''
    STYLES={
        'yellow'    :   QtGui.QBrush(QtGui.QColor(255,255,0)),
        'green'    :   QtGui.QBrush(QtGui.QColor(0,255,0)),
        'red'       :   QtGui.QBrush(QtGui.QColor(255,0,0)),
        'white'     :   QtGui.QBrush(QtGui.QColor(255,255,255)),
    }
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
                if not disable and not enable:
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