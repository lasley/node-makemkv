#!/opt/python2.7/bin/python
##    Video Renaming
#         
#    Video renaming class
#    
#    @requires   python-levenshtein
#    
#    @author     David Lasley, dave -at- dlasley -dot- net
#    @package    video_manipulation
#    @version    $Id$

import re
import os
#import freebase
from xml.dom import minidom
from pprint import pprint
class rename:
    space_chars         =   (' ','_','-','.')
    video_extensions    =   ('mkv','mpg','avi')
    #invalid_dirs        =   ('.AppleDouble')   #<@todo
    regex_file          =   os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rename_regexes.xml')
    dont_upper_these    =   ('the','a','an','of','by','up','is','in','at','on','to') #dont uppercase these words
    dir_hierarchy       =   ('season','disc','episode')
    roman_numeral_regex =   '^m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$'
    def __init__(self,bad_files_path,good_files_path):
        self.files_in = bad_files_path
        self.files_out = good_files_path
        if not os.path.isdir(good_files_path):
            os.mkdir(good_files_path)
    
    def index_current(self):
        '''
            Indexes current files
        '''
        temp_index, file_index, sanitized_index = {} , {}, {}
        for root, dirs, files in os.walk(self.files_in,followlinks=True):
            if '.Apple' not in root: 
                for _file in files:
                    split_file = _file.rsplit('.',1)
                    try:
                        if split_file[1] in self.video_extensions:
                            #implementing folder indexing
                            minus_starting = root.replace(self.files_out,'')
                            sanitized_arr = []
                            for folder_part in minus_starting.split(os.sep):
                                if folder_part.strip() != '':
                                    try:
                                        sanitized_arr.append(sanitized_index[folder_part.lower()])
                                    except KeyError:
                                        sanitized_index[folder_part.lower()] = rename.full_sanitize(folder_part)
                                        sanitized_arr.append(sanitized_index[folder_part.lower()])
                            sanitized_arr.append( rename.full_sanitize(split_file[0]) )
                            media_props = {}
                            for sanitized in sanitized_arr:
                                if sanitized[0].strip() != '':
                                    media_props['title_case'] = sanitized[0]
                                for key,val in sanitized[1].iteritems():
                                    media_props[key] = val
                            media_props['path'] = os.path.join(root,_file)
                            try:
                                temp_index[media_props['title_case']].append(media_props)
                            except KeyError:
                                temp_index[media_props['title_case']] = [ media_props ]
                            #if media_props['title_case'] == 'Weeds' and media_props['season'] == '04':
                            #    print sanitized_arr
                            #    exit()
                    except IndexError: #no extension
                        pass
        #rename.dir_from_dict(self.files_out, temp_index)
        
        for title,media_list in temp_index.iteritems():
            for media_info in media_list:
                #print media_info
                #exit()
                extension = media_info['path'].rsplit('.',1)[1]
                new_path = os.path.join(self.files_out, media_info['title_case'])
                if len(media_list) == 1:
                    rename.mk_file(media_info['path'], new_path, extension)
                else:
                    if not os.path.isdir(new_path):
                        os.mkdir(new_path)
                    for dir_part in self.dir_hierarchy:
                        if dir_part == 'episode':
                            season_txt = []
                            for txt_order in rename.dir_hierarchy:
                                try:
                                    season_txt.append('%s%s' % (txt_order[0].capitalize(),media_info[txt_order]))
                                except KeyError:
                                    pass
                            season_txt = ''.join(season_txt)
                            new_path = os.path.join(new_path, '%s - %s' % (media_info['title_case'], season_txt))
                            print new_path
                            rename.mk_file(media_info['path'], new_path, extension)
                        else:
                            try:
                                new_path = os.path.join(new_path,'%s %s' % (dir_part.capitalize(),media_info[dir_part]))
                                if not os.path.isdir(new_path):
                                    os.mkdir(new_path)
                            except KeyError:    #part doesnt exist
                                print 'Passing %s, %s, %s' % (new_path,dir_part,repr(media_info))
                                pass
                    
            #if len(_temp_index):
            #    pass
                    #if len(sanitized[1]) > 1:    #  If there's seasons or something
                    #    _metas = []
                    #    
                    #    for meta_type in self.dir_hierarchy:
                    #        try:
                    #            sanitized[1][meta_type]
                    #            try:
                    #                
                    #                self.file_index
                    #        except KeyError: pass       #meta doesnt exist
                    #    print sanitized
                    #    exit()
                    #try:
                    #    self.file_index[sanitized[0]]
                        #if type(self.file_index[sanitized[0]]) == str:
                        #    if len(sanitized[1]) > 1:    #  If there's seasons or something
                        #        print('%s\r%s' % (self.file_index[sanitized[0]], sanitized))
                        #        exit()
                        #        self.file_index[sanitized[0]]
                            #self.file_index[sanitized[0]] = {}
                    #except KeyError:
                    #    self.file_index[sanitized[0]] = {}
                    #self.file_index[saniz]
            #exit('%s\r\r%s'%(dirs,files))
    #
    #@staticmethod        
    #def dir_from_dict(save_to,dict_in):
    #    if not os.path.isdir(save_to): os.mkdir(save_to) #create necessita
    #    return_dict = {}
    #    for key,item in dict_in.iteritems():
    #        if type(item) == dict:
    #            return_dict[key] = rename.dir_from_dict(os.path.join(save_to,key),item)
    #        else:
    #            ext = item[0].rsplit('.',1)[1]
    #            try:
    #                os.link(item[0],os.path.join(save_to,'%s %s.%s' % (rename.title_case(item[1]['sanitized']), item[1]['season_txt'], ext)))
    #            except OSError: #<file exists
    #                for i in xrange(2,100):
    #                    _name = '%s %s (%s).%s' % (rename.title_case(item[1]['sanitized']), item[1]['season_txt'], i, ext)
    #                    if not os.path.isfile(_name):
    #                        os.link(item[0],os.path.join(save_to,_name))
    #                        break
    
    @staticmethod
    def mk_file(old_path, new_path_minus_extension, extension):
        try:
            os.link(old_path, '%s.%s' % (new_path_minus_extension, extension))
            return '%s.%s' % (new_path_minus_extension, extension)
        except OSError: #<file exists
            end_num = 1
            try:
                _name = os.path.join(old_path, '%s (%s).%s' % (new_path_minus_extension, end_num, extension))
                with(open(_name)) as f: end_num+=1
            except IOError:
                os.link(old_path, _name)
                return _name
    
    @staticmethod
    def full_sanitize(string):
        '''
            Fully sanitize an input string
            
            @param  Str     string  Input
            @return Tuple   [sanitized,volume_info]
        '''
        volume_info = rename.volume_info(rename.sanitize_spaces(string))
        return (
                rename.title_case(
                    rename.sanitize_spaces(
                        rename.do_regexes(volume_info['sanitized']
                                          )
                        )
                    ),
                volume_info)

    #def rename_dir(self):
    
    #@todo
    #@staticmethod
    #def freebase_search(string,types=['/film/film','/tv/tv_program']):
    #    
    #    query = {
    #                'name'  :   string,
    #                "type|="  :   types,
    #                'id'    :   None,
    #            }
    #    derp = freebase.mqlread(query)
    #    from pprint import pprint
    #    pprint( derp )
    #
    @staticmethod
    def do_regexes(string,dom=None):
        '''
            Load XML of regexes, loop, replace
            
            @param  Str string  Input
            @return Sanitized string
        '''
        if dom is None: dom = minidom.parse(rename.regex_file)
        out_string = string[0:]
        for regex in dom.getElementsByTagName('regex'):
            out_string = re.sub( regex.firstChild.nodeValue, ' ', out_string, flags=re.IGNORECASE )
        for obj_replace in dom.getElementsByTagName('replace'):
            change_to = obj_replace.getElementsByTagName('change_to')[0].firstChild.nodeValue
            for regex in obj_replace.getElementsByTagName('original_r'):
                out_string = re.sub( regex.firstChild.nodeValue, change_to, out_string, flags=re.IGNORECASE )
        return out_string
    
    @staticmethod
    def volume_info(string):
        '''
            Extract episode/seasons from string.
            Also removes the extracted strings from input variable
            
            @param  Str     string  input string
            @return Dict    {season,episode,disk,txt}
        '''
        regex = re.compile(
            "(e|d|s|v|t)(pisode|isc|isk|eason|olume|ol|rack|itle)? ?([0-9]{1,2})\,? ?",
            re.IGNORECASE   )
        match_map = {
            'e' :   'episode',
            't' :   'episode',
            'v' :   'season',
            's' :   'season',
            'd' :   'disc',
        }
        matched = {}
        matched_section = None
        trim_num = 0
        sanitized = []
        string = string.lower()
        for match in regex.finditer(string):
            try:
                matched[match_map[match.group(1)]] = '%02d' % int(match.group(3))
                sanitized.append(string[trim_num:match.start()])
                trim_num = match.end()
            except KeyError:
                pass
        sanitized.append(string[trim_num:])
        matched['sanitized'] = ''.join(sanitized).strip()
        return matched
    
    @staticmethod
    def format_season(season_information,include_disc_num=True):
        ##  Format season information to Sanitized S#D#E#
        #   @param  Dict    season_information  as returned by volume_info
        #   @param  Bool    include_disc_num    include disc in out
        season_output = []
        for typ in rename.dir_hierarchy:
            if include_disc_num or typ != 'disc':
                try:
                    season_output.append('%s%s'%(typ[0].capitalize(),season_information[typ]))
                except KeyError: pass
            if len(season_output)>0: 
                return '%s %s' % (season_information['sanitized'], ''.join(season_output))
            else:
                return season_information['sanitized']
    
    @staticmethod
    def sanitize_spaces(string_in):
        '''
            Make all video_renaming.space_chars into spaces, multiples into singles, strip
            
            @param  Str string_in   input string
            @return Str Sanitized String
        '''
        space_chars = '\\'.join(rename.space_chars)
        return re.sub('[\\%s]{1,}'%space_chars, ' ', string_in).strip()
    
    @staticmethod
    def title_case(string_in):
        '''
            Make string title case & move `the` to end with a comma.
            Also .upper() Roman Numerals
            
            @param  Str string_in   String in
            @return Str Title cased string
        '''
        split = string_in.lower().split(' ')
        the_string = False
        out = []
        for word in split:
            if word != '':
                try:
                    if word not in rename.dont_upper_these:
                        word = word.upper() if re.search(rename.roman_numeral_regex,word) else word.capitalize()
                    out.append(word)
                except NameError:
                    if word == 'the':
                        the_string = True
                    else:
                        out = [word.capitalize()]
        out[0] = out[0].capitalize()
        joined = ' '.join(out)
        return '%s, the' % joined if the_string else joined
#r = rename('/media/Motherload/9-aggregated_unrenamed','/media/Motherload/1.5-renamed')
#r.index_current()
#string = 'The A Dexter eng a an the  xiv   bluray hd hdmi special edition unrated ur S01D01E01'
#print rename.full_sanitize(string)
#print string