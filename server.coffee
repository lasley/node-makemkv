#!/usr/bin/env coffee
##  Makemkvcon object
#         
#   Manipulate makemkv with node.js
#    
#   @author     David Lasley, dave -at- dlasley -dot- net
#   @website    https://dlasley.net/blog/projects/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id: remote_makemkv_server.py 102 2013-02-06 01:27:56Z dave@dlasley.net $
__version__ = '$Revision:$'

fs = require('fs')
spawn = require('child_process').spawn

class MakeMkv
    
    NEWLINE_CHAR: '\n'
    SELECTION_PROFILE: SERVER_SETTINGS['selection_profile'] #< @todo
    ATTRIBUTE_IDS: SERVER_SETTINGS['attibute_ids'] #< @todo
    COL_PATTERN: /((?:[^,"\']|"[^"]*"|\'[^']*\')+)/
    # Chars not allowed on the filesystem
    RESERVED_CHAR_MAP: { '/':'-', '\\':'-', '?':' ', '%':' ', '*':' ', \
                         ':':'-', '|':'-', '"':' ', '<':' ', '>':' ', }
    PERMISSIONS: {'file':'0666', 'dir':'0777'} #< New file and dir permissions
    
    constructor: (@save_to) => #< Assign save_to
        
    get_busy: (disc_id, busy) =>
        #   Determine which discs are being used
        #   @param  int disc_id Disc ID
        #   @param  bol busy    
        if not disc_id
            {
                'cmd'   :   'get_busy',
                'val'   :   this.busy_devices
            }
        else
            if this.busy_devices[disc_id]
                if busy == this.busy_devices[disc_id] #< Busy disc
                    false
            this.busy_devices[disc_id] = busy #< gtg
            true
            
    rip_track: (out_path, disc_id, track_ids, callback=false) =>
        #   Rip a track to out_path (dir)
        #   @param  str     out_path    Save dir
        #   @param  int     disc_id     Disc ID
        #   @param  list    track_ids   List of ints (track IDs) to rip
        #   @param  func    callback    Callback function, will receive return var as param
        #   @return dict    Rip success? Keyed by track ID
        ripped_tracks = {'disc_id':disc_id, 'cmd':'rip', 'results':[], }
                            
        return_false = () =>
            for track_id in track_ids
                ripped_tracks['results'].push(track_id)
            return ripped_tracks
        
        recurse_tracks = (track_ids, ripped_tracks, recurse_tracks) =>
            track_id = track_ids.pop()
            
            if track_id == undefined #< Tracks done
                if callback
                    callback(ripped_tracks)
                else
                    ripped_tracks #< Return
            
            return_ = []
            errors = []
            makemkv = spawn(@MAKEMKVCON_PATH, ['-r', '--noscan', 'mkv', '--cache=256',
                                                'dev:'+disc_id, track_id, out_path, ])
            makemkv.stdout.on('data', (data)=>return_.push(data))
            makemkv.stderr.on('data', (data)=>errors.push(data))
            makemkv.on('exit', (code)=>
                if code == 0
                    data = data.join('')
                    if indexOf('1 titles saved.') != -1
                        ripped_tracks[track_id] = true
                    else
                        ripped_tracks[track_id] = false
                else
                    errors = errors.join('')
                    console.log('rip_track failed on #{disc_id}:#{track_id}. Output was:{@NEWLINE_CHAR}'+
                                '"#{errors}"#{@NEWLINE_CHAR}')
                    ripped_tracks[track_id] = false
                recurse_tracks(track_ids, ripped_tracks, recurse_tracks) #< Next
            )
        
        if this.get_busy(disc_id, true) #< If disc not busy, set busy and go
            out_path = this._mk_dir(out_path)
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
            if this.get_busy(disc_id, true) #< If disc not busy, set busy and go
                out_path = this._mk_dir(out_path)
                if not out_path
                    return false
                rip_output = {'disc_id':disc_id, 'out_file':out_path+'.iso', 'cmd':'iso', }
                return_ = []
                errors = []
                makemkv = spawn(@MAKEMKVCON_PATH, ['--noscan', 'backup', '--cache=256', '--decrypt',
                                                   'disc:'@drive_map[disc_id], out_path])  #< to folder, decrypt
                makemkv.stdout.on('data', (data)=>return_.push(data))
                makemkv.stderr.on('data', (data)=>errors.push(data))
                makemkv.on('exit', (code)=>
                    if code == 0
                        mkisofs = spawn('mkisofs', ['-J', '-r', '-allow-limited-size', '-iso-level', '3', 
                                                     '-udf', '-o', rip_output['out_file'], out_path])
                        mkisofs.stdout.on('data', (data)=>return_.push(data))
                        mkisofs.stderr.on('data', (data)=>errors.push(data))
                        mkisofs.on('exit', (code)=>
                            if code == 0
                                #   @todo - Delete the tree
                                this.get_busy(disc_id)
                                if callback
                                    callback(return_.join(''))
                                else
                                    return_.join('') #< return
                        )
                    # If it gets here, there was a problem somewhere
                    this.get_busy(disc_id)
                    console.log(sprintf('ERROR:\nreturn:"%s"\nerrors"%s"\nlatest code%d',
                                        return_.join(''), errors.join(''), code))
                    false
                )
        
        disc_info: (disc_id, callback=false) =>
            #   Get disc info
            #   @param  int     disc_id     Disc ID
            #   @param  func    callback    Callback function, will receive info_out as param
            #   @return dict    info_out    Disc/track information
            if this.get_busy(disc_id, true) #< If disc not busy, set busy and go
                info_out = {'disc':{}, 'tracks':{}, 'disc_id':disc_id, 'cmd':'disc_info', }
                return_ = []
                errors = []
                makemkv = spawn(@MAKEMKVCON_PATH, ['--noscan', '-r', 'info', 'dev:'+disc_id, ])
                makemkv.stdout.on('data', (data)=>return_.push(data))
                makemkv.stderr.on('data', (data)=>errors.push(data))
                makemkv.on('exit', (code)=>
                    if code == 0
                        for line in disc_info.split(@NEWLINE_CHAR)
                            split_line = `(function(line){
                                return_ = [];
                                split = line.split(@COL_PATTERN);
                                for(i=1, len=split.length; i<len; i+=2)
                                    return_.push(split[i]);
                                return_;
                            })(line);` #< Take every other col, couldn't figure out how to do this in coffeescript...
                            if split_line.length > 1 and split_line[0] != 'TCOUNT'
                                if line[0] == 'C' #< Disc Info
                                    attr_id = split_line[0].split(':')[-1]
                                    attr_val = split_line[-1].replace('"','')
                                    info_out['disc'][ \
                                        ATTRIBUTE_IDS[attr_id] if (attr_id in ATTRIBUTE_IDS) else attr_id 
                                    ] = attr_val
                                else #< Track Info
                                    switch line[0]
                                        when 'T' #< Track
                                            track_id = split_line[0].split(':')[-1]
                                            if track_id not in info_out['tracks']
                                                track_info = info_out['tracks'][track_id] = {
                                                    'cnts':{'Subtitles':0, 'Video':0, 'Audio':0, } }
                                                attr_id = split_line[1]
                                                track_info[ \
                                                    ATTRIBUTE_IDS[attr_id] if (attr_id in ATTRIBUTE_IDS) else attr_id 
                                                ] = split_line[-1].replace('"','')
                                        when 'S' #< Track parts
                                            track_part_id = split_line[1]
                                            if 'track_parts' not in info_out['tracks'][track_id]
                                                info_out['tracks'][track_id]['track_parts'] = {}
                                            if track_part_id not in info_out['tracks'][track_id]['track_parts']
                                                info_out['tracks'][track_id]['track_parts'] = {}
                                            attr_id = split_line[2]
                                            track_info[ \
                                                ATTRIBUTE_IDS[attr_id] if (attr_id in ATTRIBUTE_IDS) else attr_id 
                                            ] = split_line[-1].replace('"','')
                                            
                        #   Count the track parts
                        for track_id, track_info in info_out['tracks']
                            for part_id, track_part in track_info['track_parts']
                                info_out['tracks'][track_id]['cnts'][track_part['Type']] += 1
                        
                        #   Release disc, set cache_refreshed, and return
                        this.get_busy(disc_id)
                        info_out['cache_refreshed'] = new Date()
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
        #   Scan drives, return info. Also sets this.drive_map
        #   @param  func    callback Callback function, will receive drives as param
        #   @return dict    drives  Dict keyed by drive index, value is movie name
        if this.get_busy(false, true) #< Make sure none of the discs are busy
            drives = {'cmd':'scan_drives'}
            @drive_map = {}
            return_ = []
            makemkv = spawn(@MAKEMKVCON_PATH, ['-r', 'info'])
            makemkv.stdout.on('data', (data)=>return_.push(data))
            makemkv.stderr.on('data', (data)=>return_.push(data))
            makemkv.on('exit', (code)=>
                drive_scan = return_.join('').split(@NEWLINE_CHAR)
                for line in drive_scan
                    if line[0..4] == 'DRV:' and line.indexOf('/dev/') != -1 #<  DRV to make sure it's drive output, /dev to make sure that there is a drive
                        info = line.split(@COL_PATTERN)
                        drive_location = info[-2].replace('"', '')
                        drives[drive_location] = info[-4].replace('"', '') if info[-4] != '""' else false #<  [Drive Index] = Movie Name
                        @drive_map[drive_location] = info[1].split(':')[1] #<    Index the drive location to makemkv's drive ID
                this.get_busy(false)
                
                if callback
                    callback(drives)
                else
                    drives #< Return
            )

    _mk_dir: (dir) =>
        #   Create dir if not exists
        #   @param  str dir Directory to create
        #   @return mixed   false if failed, otherwise new dir
        dir = this._sanitize_fn(dir)
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