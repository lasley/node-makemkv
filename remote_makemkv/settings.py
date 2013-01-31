HOST = '192.168.69.104'
PORT = 6001
PROXY_HOST = None #< None if none, or 'Host'
PROXY_PORT = 8080
OUT_PATH = '/media/Motherload/7-test-rip/'
DRIVE_NAME_MAPS = {
        '/dev/sr0'  :   '1st',
        '/dev/sr1'  :   '3rd',
        '/dev/sr2'  :   '2nd',
        '/dev/sr3'  :   '4th',
        '/dev/sr4'  :   '5th',
    }   #<  Drive Identification on GUI
MAKEMKVCON_PATH = u'makemkvcon' #< @todo - determine this on the fly
OUTLIER_MODIFIER = 0.5  #<  If title size is below size_upper_quartile * OUTLIER_MODIFIER, it will be red and unchecked. Set to 0 for no auto selection

# Don't edit below here unless you know what you are doing
import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)