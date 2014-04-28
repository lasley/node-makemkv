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

##  Sanitize video titles.. could probably be abstracted for more uses
class SanitizeTitles
    
    #   Order of hierarchy
    DIR_HIERARCHY: ['season', 'disc', 'episode']
    @RESERVED_CHAR_MAP: { #   Filesystem reserved char replacement map
        '/':'-', '\\':'-', ':':'-', '|':'-', 
        '?':' ', '%':' ', '*':' ', '"':' ', '<':' ', '>':' '
    }
    
    ##  Init
    constructor: () ->
        
        @NO_UPPERCASE = ['the', 'a', 'an', 'of', 'by' , 'up' , 'is' , 'in' , 'at' , 'on' , 'to']
        @DEFAULT_TITLE = 'Title'
        @VID_EXTS = ['mkv', 'mpg', 'avi', 'mp4', 'm4v']
        @SPACE_CHARS = /[ _\Ð\-\.]+/g
        
        @FORMAT_SEASON = /[, ]+(e|d|s|v|t)(pisode|isc|isk|eason|eries|olume|ol|rack|itle)? ?([0-9]{1,2})/ig
        
        parser = new xml2js.Parser()
        fs.readFile(__dirname + '/rename_regexes.xml', (err, data) =>
            parser.parseString(data, (err, result) =>
                @VIDEO_RULES = result.renaming.videos.shift()
            )
        )
        
    ##  Fully sanitize an input string
    #   @param  Str     string  Input
    #   @param  list    fallbacks   fallback titles to use for S/D/T gathering
    #   @return list    [sanitized,volume_info]
    
    #   Reserved chars 
    do_sanitize: (title, fallbacks=[]) =>
        
        for change_to, change_from of @RESERVED_CHAR_MAP
            title = title.replace(change_from, change_to)
        
        #   Extract title info
        volume_info = @volume_info(title)
        
        #   Gather fallback Season/Episode Info
        for fallback in fallbacks
            if fallback
                vi = @volume_info(fallback)
                for key, val of vi
                    if not volume_info[key]
                        volume_info[key] = val
        
        #   regex-->title_case->format_season->_strip_spaces->return
        volume_info['sanitized'] = @_do_title_case(@do_regexes(volume_info['sanitized']))
        @_strip_spaces(@format_season(volume_info))
        
    ##  Loop regexes from XML, replace
    #   @param  Str title  Input
    #   @return Sanitized string   
    do_regexes: (title) =>

        for regex in @VIDEO_RULES.regex
            title = title.replace(regex, ' ')

        for replace in @VIDEO_RULES.replace
            title = title.replace(replace.original_r, replace.change_to)
            
        title
    
    ##  Extract episode/seasons from string.
    ##  Also removes the extracted strings from input variable
    #
    #   @param  Str     string  input string
    #   @return Dict    {season,episode,disk,txt}
    volume_info: (title) =>

        lpad = (value, padding=2, zeroes='0') ->
            zeroes = "0"
            zeroes += "0" for i in [1..padding]
            (zeroes + value).slice(padding * -1)
            
        match_map = {
            'e':@DIR_HIERARCHY[2], 't':@DIR_HIERARCHY[2], 'v':@DIR_HIERARCHY[0], 
            's':@DIR_HIERARCHY[0], 'd':@DIR_HIERARCHY[1]
        }
        
        matched = {}
        sanitized = []
        trim_loc = 0
        title = title.toLowerCase()
        
        while match = @FORMAT_SEASON.exec(title)
            if match[1] and match[3] #< If Letter and Number in right spot
                matched[match_map[match[1]]] = lpad(match[3])
                sanitized.push(title[trim_loc...match.index])
                trim_loc = match.index + match[0].length
        
        sanitized.push(title[trim_loc..])
        matched.sanitized = sanitized.join('')
        matched
    
    ##  Format season information to Sanitized S#D#E#
    #   @param  Dict    season_information  as returned by volume_info
    #   @param  Bool    include_disc_num    include disc in out
    format_season: (season_info, inc_disc_num=true) =>

        season_out = []   
        for type_ in @DIR_HIERARCHY
            if season_info[type_]
                if type_ != 'disc' or inc_disc_num
                    season_out.push(type_[0].toUpperCase(), season_info[type_])
            
        if season_out
            season_info.sanitized + ' ' + season_out.join('')
        else
            season_info.sanitized
        
    ##  Turn all SPACE_CHARS into spaces, multiples into singles
    #
    #   @param  Str string_in   input string
    #   @return Str Sanitized String
    _strip_spaces: (str_in, callback=false) ->

        str_ = str_in.replace(@SPACE_CHARS, ' ')
        if callback
            callback(str_)
        else
            str_
            
    ##  Make string title case & move leading `the` to end with a comma.
    #   Also .upper() Roman Numerals
    #
    #   @param  Str string_in   String in
    #   @return Str Title cased string
    _do_title_case: (str_in, callback=false) ->
        
        ROMAN_NUMERAL_REGEX = /^m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$/
        the_ = false
        out = []
        split_str = str_in.toLowerCase().split(' ')
        
        for word in split_str
            if word
                if ROMAN_NUMERAL_REGEX.test(word) #<   Cap if Roman Numeral
                    out.push(word.toUpperCase())
                else if word not in @NO_UPPERCASE #<   Cap first letter if not defined
                    out.push(word.charAt(0).toUpperCase() + word.slice(1))
                else #< No cap
                    if word == 'the' and not out.length #< Kill the if first word
                        the_ = true
                    else
                        out.push(word)
        
        joined = out.join(' ')
        if the_ #< Add the at the end
            joined += ', the'
        
        if callback
            callback(joined)
        else
            joined
            
            
module.exports = SanitizeTitles