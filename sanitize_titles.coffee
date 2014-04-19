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
    
    RESERVED_CHAR_MAP: { '/':'-', '\\':'-', '?':' ', '%':' ', '*':' ',
                        ':':'-', '|':'-', '"':' ', '<':' ', '>':' ', }
    DIR_HIERARCHY: ['season', 'disc', 'episode']
    
    constructor: () ->
                     
        parser = new xml2js.Parser({ explicitArray: true })
        fs.readFile(__dirname + '/rename_regexes.xml', (err, data) =>
            parser.parseString data, (err, result) =>
                @VIDEO_RULES = result.videos
                globals = result.globals
                @DEFAULT_TITLE = globals.default_title.shift()
                @SPACE_CHARS = new RegExp('[' + globals.space_chars.join('\\') + ']{1,}')
                @VID_EXTS = globals.video_extensions
                @NO_UPPERCASE = globals.no_upper
                @FORMAT_SEASON = new RegExp(globals.format_season, 'i')
        )
        
    do_sanitize: (title):
        ##  Fully sanitize an input string
        #   @param  Str     string  Input
        #   @return Tuple   [sanitized,volume_info]
        
        #   Reserved chars
        for change_to, change_from in @RESERVED_CHAR_MAP
            title = title.replace(change_from, change_to)
        
        #   Extract title info
        volume_info = @volume_info(title)
        
        #   regex->strip_spaces->title_case->return
        @do_title_case(@strip_spaces(@do_regex(volume_info['sanitized'])))
        
        
    do_regexes: (title) =>
        ##  Load XML of regexes, loop, replace
        #   @param  Str title  Input
        #   @return Sanitized string
        
        for regex in @VIDEO_RULES.regex
            title = title.replace(regex, ' ')
            
        for replace in @VIDEO_RULES.replace
            title = title.replace(replace.original_r, replace.change_to)
            
        title
    
    volume_info: (title) =>
        ##  Extract episode/seasons from string.
        ##  Also removes the extracted strings from input variable
        #
        #   @param  Str     string  input string
        #   @return Dict    {season,episode,disk,txt}
        lpad = (n, width=2, z='0') ->
            n = n + ''
            n.length >= width ? n : new Array(width - n.length + 1).join(z) + n
            
        match_map = {'e':@DIR_HIERARCHY[2], 't':@DIR_HIERARCHY[2], 'v':@DIR_HIERARCHY[0],
                    's':@DIR_HIERARCHY[0], 'd':@DIR_HIERARCHY[1]}
        matched = {}
        sanitized = []
        trim_loc = 0
        title = title.toLowerCase()
        
        while match = @FORMAT_SEASON.exec(title)
            if match[1] and match[3] #< If Letter and Number in right spot
                matched[match_map[match[1]]] = lpad(match[3])
                sanitized.push(title[trim_loc...match.index])
                trim_loc = match.index + match[0].length
        
        sanitized.append(title[trim_loc..])
        matched.sanitized = ''.join(sanitized)
        matched
        
    format_season: (season_info, inc_disc_num=false) =>
        ##  Format season information to Sanitized S#D#E#
        #   @param  Dict    season_information  as returned by volume_info
        #   @param  Bool    include_disc_num    include disc in out

        season_out = []   
        for type_ in @DIR_HIERARCHY
            if season_info[type_]
                season_out.push(type_[0].toUpperCase(), season_info[type_])
            
        if season_out
            season_info.sanitized + ' ' + season_out.join('')
        else
            season_info.sanitized
        
        
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
        
    do_title_case: (str_in, callback=false) ->
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
            
            
module.exports = SanitizeTitles