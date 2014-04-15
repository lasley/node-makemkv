#!/usr/bin/env coffee
###
#   Title Sanitizer
#         
#   @author     David Lasley, dave@dlasley.net
#   @website    https://dlasley.net/blog/projects/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id: remote_makemkv_server.py 102 2013-02-06 01:27:56Z dave@dlasley.net $
###

fs = require 'fs',
xml2js = require 'xml2js'

class SanitizeTitles

    constructor: () ->
        @RESERVED_CHAR_MAP = { '/':'-', '\\':'-', '?':' ', '%':' ', '*':' ',
                               ':':'-', '|':'-', '"':' ', '<':' ', '>':' ', }
                               
        parser = new xml2js.Parser({ explicitArray: true })
        fs.readFile(__dirname + '/rename_regexes.xml', (err, data) =>
            parser.parseString data, (err, result) =>
                @VIDEO_RULES = result['videos']
                globals = result['globals']
                @DEFAULT_TITLE = globals['default_title'].shift()
                @SPACE_CHARS = new RegExp('[' + globals['space_chars'].join('\\') + ']{1,}')
                @VID_EXTS = globals['video_extensions']
                @NO_UPPERCASE = globals['no_upper']
        )
        
    format_season: (season_info, inc_disc_num=false) ->
        ##  Format season information to Sanitized S#D#E#
        #   @param  Dict    season_information  as returned by volume_info
        #   @param  Bool    include_disc_num    include disc in out
        DIR_HIERARCHY = ['season', 'disc', 'episode']
        season_out = []
            
        for type_ in DIR_HIERARCHY
            
        
        
    strip_spaces: (str_in, callback=false) ->
        ##  Turn all SPACE_CHARS into spaces, multiples into singles
        #
        #   @param  Str string_in   input string
        #   @return Str Sanitized String
        str_ = str_in.replace(@SPACE_CHARS, ' ')
        if callback
            callback(str_)
        else
            str_
        
    title_case: (str_in, callback=false) ->
        ##  Make string title case & move leading `the` to end with a comma.
        #   Also .upper() Roman Numerals
        #
        #   @param  Str string_in   String in
        #   @return Str Title cased string
        
        ROMAN_NUMERAL_REGEX = /^m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$/
        the_ = false
        out = []
        split_str = str_in.toLowerCase().split(' ')
        
        for word in split_str
            if word
                if word.test(ROMAN_NUMERAL_REGEX) #<   Cap if Roman Numeral
                    out.append(word.toUpperCase())
                else if word not in @NO_UPPERCASE #<   Cap first letter if not defined
                    out.append(word.charAt(0).toUpperCase() + word.slice(1))
                else #< No cap
                    if word == 'the' and not out.length #< Kill the if first word
                        the_ = true
                    else
                        out.append(word)
        
        joined = out.join(' ')
        if the_ #< Add the at the end
            joined += ', the'
        
        if callback
            callback(joined)
        else
            joined