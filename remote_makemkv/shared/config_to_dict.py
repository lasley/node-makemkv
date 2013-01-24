#!/usr/bin/env python
##  Class to take an ini and output a dictionary
#   @author     David Lasley, dave -at- dlasley -dot- net
#   @website    http://code.google.com/p/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id$
#
#   Thanks to Alex Martelli - http://stackoverflow.com/questions/3220670/read-all-the-contents-in-ini-file-into-dictionary-with-python
import ConfigParser

class config_to_dict(ConfigParser.SafeConfigParser):
    def do(self,config_file):
        self.read(config_file)
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d