HOST = '192.168.69.104'
PORT = 6001
PROXY_HOST = 'localhost'
PROXY_PORT = 8080
OUT_PATH = '/media/Motherload/7-ripp/'
DRIVE_NAME_MAPS = {
        '/dev/sr0'  :   '1st',
        '/dev/sr1'  :   '3rd',
        '/dev/sr2'  :   '2nd',
        '/dev/sr3'  :   '4th',
        '/dev/sr4'  :   '5th',
    }   #<  Drive Identification on GUI
OUTLIER_MODIFIER = 0.5  #<  If title size is below size_upper_quartile * OUTLIER_MODIFIER, it will be red and unchecked

# Don't edit below here
import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)