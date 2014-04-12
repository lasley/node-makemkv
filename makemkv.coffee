#!/usr/bin/env coffee
###
#   Makemkvcon object
#         
#   Manipulate makemkv with node.js
#    
#   @author     David Lasley, dave@dlasley.net
#   @website    https://dlasley.net/blog/projects/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id: remote_makemkv_server.py 102 2013-02-06 01:27:56Z dave@dlasley.net $
###
__version__ = '$Revision:$'

fs = require('fs')
spawn = require('child_process').spawn
ini = require('ini')

class MakeMKV

    constructor: (save_to) -> #< Assign save_to
        @MAKEMKVCON_PATH = '/usr/bin/makemkvcon'
        @NEWLINE_CHAR = '\n'
        
        SETTINGS_PATH = './server_settings.ini'
        SERVER_SETTINGS = ini.parse(fs.readFileSync(SETTINGS_PATH, 'utf-8'))
        @SELECTION_PROFILE = SERVER_SETTINGS.selection_profile
        @ATTRIBUTE_IDS = SERVER_SETTINGS.attibute_ids 
        
        @COL_PATTERN = /((?:[^,"\']|"[^"]*"|\'[^']*\')+)/
        # Chars not allowed on the filesystem
        @RESERVED_CHAR_MAP = { '/':'-', '\\':'-', '?':' ', '%':' ', '*':' ', \
                             ':':'-', '|':'-', '"':' ', '<':' ', '>':' ', }
        @PERMISSIONS = {'file':'0666', 'dir':'0777'} #< New file and dir permissions
        @cache = {}
        @change_out_dir(save_to)
        @busy_devices = {}
    
    cache_data: (data) =>
        #   Cache data to variable for when clients join
        #   @param  dict    data    Data obj, must contain keys `cmd`, `data`
        
        #if not @cache[data['cmd']]
        @cache[data['cmd']] = data['data']
        #else #< Update the dict, instead of replace
        #    if(typeof(data['data'] == Object))
        #    for key, val in data['data']
        #        @cache[data['cmd']][key] = val
    
    display_cache: (callback=false) =>
        #   Send cached data to client in logic order
        #       scan_drives, disc_info, rip_track
        cmd_order = ['change_out_dir', 'scan_drives', 'disc_info', 'rip']
        cached = []
        for cmd in cmd_order
            if @cache[cmd]
                cached.push({'cmd':cmd, 'data':@cache[cmd]})

        if callback
            callback(cached)
        else
            cached
    
    change_out_dir: (dir, callback=false) =>
        #   Register change to save directory
        @save_to = dir
        @cache_data({'cmd':'change_out_dir', 'data':@save_to})
        if callback
            callback(@save_to)
        else
            @save_to
    
    get_busy: (disc_id, busy) =>
        #   Determine which discs are being used
        #   @param  int disc_id Disc ID
        #   @param  bol busy    
        if not disc_id
            {
                'cmd'   :   'get_busy',
                'val'   :   @busy_devices
            }
        else
            if @busy_devices[disc_id]
                if busy == @busy_devices[disc_id] #< Busy disc
                    false
            @busy_devices[disc_id] = busy #< gtg
            true
            
    rip_track: (out_path, disc_id, track_ids, callback=false) =>
        #   Rip a track to out_path (dir)
        #   @param  str     out_path    Save dir
        #   @param  int     disc_id     Disc ID
        #   @param  list    track_ids   List of ints (track IDs) to rip
        #   @param  func    callback    Callback function, will receive return var as param
        #   @return dict    Rip success? Keyed by track ID
        ripped_tracks = {'data':{'disc_id':disc_id, 'results':[]}, \
                        'cmd':'rip'}
                            
        return_false = () =>
            for track_id in track_ids
                ripped_tracks['data']['results'].push(track_id)
            return ripped_tracks
        
        recurse_tracks = (track_ids, ripped_tracks, recurse_tracks) =>
            track_id = track_ids.pop()
            
            if track_id == undefined #< Tracks done
                
                @cache_data(ripped_tracks)
                if callback
                    callback(ripped_tracks)
                else
                    ripped_tracks #< Return

            @_spawn_generic(['-r', '--noscan', 'mkv', '--cache=256',
                            'dev:'+disc_id, track_id, out_path, ], (code, data) =>
                if code == 0
                    if indexOf('1 titles saved.') != -1
                        ripped_tracks['data'][track_id] = true
                    else
                        ripped_tracks['data'][track_id] = false
                else
                    errors = data
                    console.log('rip_track failed on #{disc_id}:#{track_id}. Output was:{@NEWLINE_CHAR}'+
                                '"#{errors}"#{@NEWLINE_CHAR}')
                    ripped_tracks['data'][track_id] = false
                recurse_tracks(track_ids, ripped_tracks, recurse_tracks) #< Next
            )
        
        if @get_busy(disc_id, true) #< If disc not busy, set busy and go
            out_path = @_mk_dir(out_path)
            if not out_path
                return_false()
            recurse_tracks(track_ids, ripped_tracks, recurse_tracks)
        else
            false
            
    make_iso: (out_path, disc_id, callback=false) =>
        #   Generate an ISO
        #   @param  str out_path    Output dir
        #   @param  int disc_id     Disc Id
        #   @param  Callback function, will receive rip_output as param
        #   @return dict    rip_output
        if @get_busy(disc_id, true) #< If disc not busy, set busy and go
            out_path = @_mk_dir(out_path)
            if not out_path
                return false
            rip_output = {'data':{'disc_id':disc_id, 'out_file':out_path+'.iso',}, \
                            'cmd':'iso', }
            #   Spawn MakeMKV, backup to defined folder
            @_spawn_generic(['--noscan', 'backup', '--cache=256', '--decrypt', 'disc:',
                             @drive_map[disc_id], out_path], (code, data) =>
                if code == 0
                    @_spawn_generic(['-J', '-r', '-allow-limited-size', '-iso-level', '3', 
                                     '-udf', '-o', rip_output['data']['out_file'], out_path], (code, data) =>
                        if code == 0
                            #   @todo - Delete the tree
                            @get_busy(disc_id)
                            
                            @cache_data(data)
                            if callback
                                callback(data)
                            else
                                data #< return
                    )
                else
                    # If it gets here, there was a problem somewhere
                    @get_busy(disc_id)
                    console.log(sprintf('ERROR:\nreturn:"%s"\nlatest code%d',
                                        data, code))
            , 'mkisofs')
    
    disc_info: (disc_id, callback=false) =>
        #   Get disc info
        #   @param  int     disc_id     Disc ID
        #   @param  func    callback    Callback function, will receive info_out as param
        #   @return dict    info_out    Disc/track information
        if @get_busy(disc_id, true) #< If disc not busy, set busy and go
            info_out = {'data':{'disc':{}, 'tracks':{}, 'disc_id':disc_id}, \
                        'cmd':'disc_info' }
            return_ = []
            errors = []
            @_spawn_generic(['--noscan', '-r', 'info', 'dev:'+disc_id, ], (code, disc_info)=>
                if code == 0
                    for line in disc_info
                        
                        #   Loop the line split by COL_PATTERN, take every 2 starting at index 1
                        split_line = []
                        for col in line.split(@COL_PATTERN)[1..] by 2
                            split_line.push(col)
                            
                        if split_line.length > 1 and split_line[0] != 'TCOUNT'

                            switch(line[0])
                                
                                when 'C' #< CINFO (Disc Info)
                                    attr_id = split_line[0].split(':').pop()
                                    attr_val = split_line.pop()[1..-2]
                                    info_out['data']['disc'][ \
                                        if attr_id of @ATTRIBUTE_IDS then @ATTRIBUTE_IDS[attr_id] else attr_id 
                                    ] = attr_val
                                
                                when 'T' #< Track
                                    track_id = split_line[0].split(':').pop()
                                    if track_id not of info_out['data']['tracks']
                                        track_info = info_out['data']['tracks'][track_id] = {
                                            'cnts':{'Subtitles':0, 'Video':0, 'Audio':0, } }
                                        attr_id = split_line[1]
                                        track_info[ \
                                            if attr_id of @ATTRIBUTE_IDS then @ATTRIBUTE_IDS[attr_id] else attr_id 
                                        ] = split_line.pop()[1..-2]
                                
                                when 'S' #< Track parts
                                    track_id = split_line[0].split(':').pop()
                                    track_part_id = split_line[1]
                                    if 'track_parts' not of info_out['data']['tracks'][track_id]
                                        info_out['data']['tracks'][track_id]['track_parts'] = {}
                                    if track_part_id not of info_out['data']['tracks'][track_id]['track_parts']
                                        info_out['data']['tracks'][track_id]['track_parts'][track_part_id] = {}
                                    track_info = info_out['data']['tracks'][track_id]['track_parts'][track_part_id]
                                    attr_id = split_line[2]
                                    track_info[ \
                                        if attr_id of @ATTRIBUTE_IDS then @ATTRIBUTE_IDS[attr_id] else attr_id 
                                    ] = split_line.pop()[1..-2]
                                        
                    #   Count the track parts
                    for track_id, track_info in info_out['data']['tracks']
                        for part_id, track_part in track_info['track_parts']
                            info_out['data']['tracks'][track_id]['cnts'][track_part['Type']]++
                    
                    #   Release disc, set cache_refreshed, and return
                    @get_busy(disc_id)
                    info_out['data']['cache_refreshed'] = new Date()
                    
                    @cache_data(info_out)
                    if callback
                        callback(info_out)
                    else
                        info_out #< Return
                    
                else
                    errors = errors.join('')
                    console.log('disc_info failed on #{disc_id}. Output was:{@NEWLINE_CHAR}'+
                                '"#{errors}"{@NEWLINE_CHAR}')
                    false
            )
        else
            false

    scan_drives: (callback=false) =>
        #   Scan drives, return info. Also sets @drive_map
        #   @param  func    callback Callback function, will receive drives as param
        #   @return dict    drives  Dict keyed by drive index, value is movie name
        if @get_busy(false, true) #< Make sure none of the discs are busy
            drives = {'cmd':'scan_drives', 'data':{}}
            @drive_map = {}
            #   Spawn MakeMKV with callback
            @_spawn_generic(['-r', 'info'], (code, drive_scan)=>
                for line in drive_scan
                    if line[0..3] == 'DRV:' and line.indexOf('/dev/') != -1 #<  DRV to make sure it's drive output, /dev to make sure that there is a drive
                        info = line.split(@COL_PATTERN)
                        #   Assign drive_location, strip quotes
                        drive_location = info[info.length - 2][1..-2]
                        #   [Drive Index] = Movie Name
                        if info[info.length - 4] != '""'
                            #   Assign drive info, strip quotes
                            drives['data'][drive_location] =  info[info.length - 4][1..-2]
                        else
                            drives['data'][drive_location] = false 
                        @drive_map[drive_location] = info[1].split(':')[1] #<    Index the drive location to makemkv's drive ID
                @get_busy(false)
                
                @cache_data(drives)
                if callback
                    callback(drives)
                else
                    drives #< Return
            )

    _spawn_generic: (args, callback=false, path=undefined) =>
        #   Generic MakeMKVCon Spawn
        #   @param  list    args    List of str arguments
        #   @param  funct   callback
        if path == undefined
            path = @MAKEMKVCON_PATH
            
        makemkv = spawn(path, args)
        return_ = []
        
        makemkv.stdout.setEncoding('utf-8')
        makemkv.stdout.on('data', (data)=>
            return_.push(data)
        )
        
        makemkv.stderr.setEncoding('utf-8')
        makemkv.stderr.on('data', (data)=>
            return_.push(data)
        )
        
        makemkv.on('exit', (code)=>
            callback(code, return_.join('').split(@NEWLINE_CHAR))
        )

    _mk_dir: (dir) =>
        #   Create dir if not exists
        #   @param  str dir Directory to create
        #   @return mixed   false if failed, otherwise new dir
        dir = @_sanitize_fn(dir)
        try
            stats = fs.lstatSync(dir)
            if not stats.isDirectory() #< Path exists, but is normal file
                return false
        catch e #< Dir doesn't exist
            try
                fs.mkdirSync(dir, @PERMISSIONS['dir'])
            catch e #< Failed to make dir
                return false
        return dir

    _sanitize_fn: (out_path) =>
        #   Remove reserved characters from file name
        #   @param  file_path   str File path (will sanitize last part)
        #   @return str sanitized
        file_path = file_path.split('/')
        for key, val in @RESERVED_CHAR_MAP
            file_path[-1] = file_path[-1].replace(key, val)
        file.path.join('/') #< Return
        
        
module.exports = MakeMKV