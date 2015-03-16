#!/usr/bin/env coffee
###
#   Remote MakeMKV Controller
#
#   Provides the server aspect of Remote MakeMKV
#
#   @author     David Lasley, dave@dlasley.net
#   @website    https://dlasley.net/blog/projects/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
###

#   Optional udev req
try
    udev = require('udev')
catch (ex)
    udev = false

http = require('http')
io = require('socket.io')
url = require('url')
fs = require('fs')
path = require('path')
CoffeeScript = require('coffee-script')
MakeMKV = require('./makemkv.coffee')

class MakeMKVServer extends MakeMKV

    CLIENT_DIR: path.join(__dirname, '..', 'client')
    #CLIENT_HTML: path.join(CLIENT_DIR, 'static', 'client.html')
    #CLIENT_CSS: path.join(CLIENT_DIR, 'static', 'client.css')
    #CLIENT_ICON: path.join(CLIENT_DIR, 'static', 'favicon.png')
    #CLIENT_COFFEE: path.join(CLIENT_DIR, 'client.coffee')
    
    STR_SUCCESS: 'success'
    
    NAMESPACE_NULL = null
    NAMESPACE_OUT_DIR = 'change_out_dir'
    NAMESPACE_SCAN = 'scan_drives'
    NAMESPACE_INFO = 'disc_info'
    NAMESPACE_RIP = 'rip_track'
    NAMESPACE_DIR_LIST = 'list_dir'
    NAMESPACE_DIR_SCAN = 'scan_dirs'
    NAMESPACE_CACHE_SHOW = 'display_cache'
     
    NAMESPACE_ORDER: [ NAMESPACE_NULL, NAMESPACE_OUT_DIR, NAMESPACE_SCAN,
                       NAMESPACE_INFO, NAMESPACE_RIP ]

    constructor: (port) ->
        
        super(false) #< MakeMKV obj init
        @cache = {}
        @change_out_dir() #< Prime the out dir cache
        
        ##  Serve the UI
        server = http.createServer((req, res) =>
            
            req.setEncoding 'utf8'
            parsed_url = url.parse(req.url, true)
            path_ = parsed_url.pathname
            
            console.log(req.method + ' to ' + path_)
            
            switch req.method
            
                when 'POST'
                
                    req.on('data', (chunk) =>
                        data = JSON.parse(chunk.toString())
                        @do_broadcast(socket, {'app':path_[1..], 'data':data})
                        res.end(@STR_SUCCESS)
                    )
                
                when 'GET'
                    
                    ext = path_.split('.')[-1]
                    load_path = path.join(@CLIENT_DIR, path_)
                    
                    #   Override these in switch/case
                    code = 200
                    content_type = 'application/octet-stream'
                    do_response = true
                    handler = false
                    
                    #   Look for extension, override vars
                    switch ext
                        
                        when 'coffee'
                            content_type = 'application/javascript'
                            handler = Coffeescript.compile
                        
                        when 'handlebars'
                            content_type = 'text/x-handlebars-template'
                        
                        when 'html'
                            content_type = 'text/html'
                        
                        when 'css'
                            content_type = 'text/css'
                            
                        when 'ico'
                            content_type = 'image/x-icon'
                        
                        when '/list_dir' #< List directory handler
                            do_response = false
                            res.writeHead(200, {'Content-Type': 'application/javascript'})
                            @list_dir(parsed_url.query['id'], (dir)=>
                                res.end(JSON.stringify(dir))
                            )
                    
                    if do_response
                        
                        res.writeHead(code, { 'Content-Type': content_type })
                        fs.readFile(load_path, {encoding:'utf-8'}, (err, data) ->
                            
                            if handler
                                #   @TODO: Add caching. This is good for testing though :)
                                data = handler(data)
                            res.end(data) 
                        
                        )
                        
        ).listen(@LISTEN_PORT)
        
        @socket = io.listen(server,)# {log: false})
        console.log('Listening on ' + @LISTEN_PORT)
        
        if udev
            monitor = udev.monitor()
            monitor.on('change', @_udev_change)
            console.log('Set udev hook to monitor device changes')
        
        #   Bind socket actions on client connect
        @socket.on('connection', (client) => register_client(client))
    
    #   Register client event handlers
    #   @param  client  socket.client   Client to bind
    register_client: (client) =>
        
        #   Wraps an emitter for all clients
        #   @param  data    obj as required by @_do_emit
        single_broadcast = (data) =>
            @_do_emit(@socket, data)
        
        #   Wraps an emitter to disable certain panels
        #   @param  disc_id str
        panel_disable = (disc_id) =>
            @_do_emit(
                @socket,
                { 'cmd': '_panel_disable',
                  'data': { 'disc_id':disc_id, "busy":budy }
                }
            )
        
        #   Wrap Send cache to client
        _display_cache = () =>
            @display_cache((msgs) =>
                for msg in msgs 
                    client.emit(msg.cmd, msg.data)
            )
            
        _display_cache() #< Actually send it
        
        client.on(NAMESPACE_CACHE_SHOW, (data) =>
            _display_cache()
        )
        
        #   User has sent command to change save_dir
        client.on(NAMESPACE_CHANGE, (data) =>
            console.log('changing out dir')
            @save_out_dir(data, single_broadcast)
        )
        
        #   User has sent command to scan drives
        client.on(NAMESPACE_SCAN, (data) =>
            console.log('scanning drives')
            panel_disable('all')
            @scan_drives(single_broadcast)
        )
        
        #   User has sent command to retrieve single disc info
        client.on(NAMESPACE_INFO, (data) =>
            console.log('getting disc info for', data)
            panel_disable(data)
            @disc_info(data, single_broadcast)
        )
        
        #   User has sent command to retrieve single disc info
        client.on(NAMESPACE_RIP, (data) =>
            console.log('getting disc info for', data)
            panel_disable(data.drive_id)
            @rip_track(data.save_dir, data.drive_id,
                       data.track_ids, single_broadcast)
        )
        
        #   User is browsing a directory, only send to them
        client.on(NAMESPACE_DIR_LIST, (data) =>
            console.log('listing dir ' + data)
            @list_dir(data, (dir) => client.emit('list_dir', dir))
        )
        
        client.on(NAMESPACE_DIR_SCAN, (data) =>
            console.log('scanning dirs ' + data)
            @scan_dirs(data, single_broadcast)
        )
        
        ##  Socket debugging
        client.on('message', (data) ->
            console.log('Client sent:', data)
        )
        client.on('disconnect', () ->
            console.log('Client d/c')
        )

    #   Send cached data to client in logic order
    #       scan_drives, disc_info, rip_track
    display_cache: (callback=false) =>
        
        cached = []
        for cmd in @NAMESPACE_ORDER
            if typeof(@cache[cmd]) == 'object'
                for namespace of @cache[cmd]
                    if @cache[cmd][namespace]
                        cached.push(
                            { 'cmd':cmd, 'data':@cache[cmd][namespace] }
                        )
        
        #   Disable busy drive panels
        for disc_id, busy of @busy_devices
            cached.push(
                { 'cmd': '_panel_disable',
                  'data': { 'disc_id':disc_id, 'busy':busy } }
            )
        
        if callback
            callback(cached)
        else
            cached

    #   Signal emit
    #   @param  socket  socket  socket
    #   @param  msg     obj      Msg, {'cmd':(str)signal_to_emit,'data':(obj)}
    _do_emit: (socket, msg) ->
        
        cmd = msg['cmd']
        data = msg['data']
        
        if data['data'] #< If there's a second data dimension (cached)
            data = data['data'] #< Pull and save it instead
            
        namespace = if data['disc_id'] then data['disc_id'] else 'none'
        data = @cache_data(cmd, data, namespace)
        socket.sockets.emit(cmd, data)    

    #   Cache data to variable for when clients join
    #   @param  cmd         str     Command that will be emitted
    #   @param  data        mixed   Data obj
    #   @param  namespace   str     Namespace to cache data in (multiple single drive cmds)
    #   @return obj     data with cache_refreshed date {'data':mixed, 'cache_refreshed':Date}
    cache_data: (cmd, data, namespace='none') =>
        
        if typeof(@cache[cmd]) != 'object'
            @cache[cmd] = {}
            
        console.log(
            'Setting cache for cmd ' + cmd + ' in namespace ' + namespace
        )

        @cache[cmd][namespace] = {'cache_refreshed': new Date(), 'data': data }
        
        #   @TODO: Delete now stale entries
        #cmd_index = @NAMESPACE_ORDER.indexOf(cmd) + 1
        #if @NAMESPACE_ORDER[cmd_index]
        #    for i in @NAMESPACE_ORDER[cmd_index...]
        #        if @cache[i]
        #            console.log('Clearing ' + i + ' ' + namespace + ' was ' + @cache[i][namespace])
        #            @cache[i][namespace] = undefined
        
        return @cache[cmd][namespace]
    
    #   Register change to save directory (UI)
    change_out_dir: () =>
        @cache_data(NAMESPACE_CHANGE, @save_to)

    #   Update the output directory
    #   @param  dir str New save dir
    save_out_dir: (dir, callback=false) =>
        
        @save_to = dir
        @change_out_dir()
        
        if callback
            callback(@save_to)
        else
            return @save_to
    
    #   Scan directories with MakeMKV
    #   @param  dirs    array   Directories to scan
    #   @param  callback    callback function, receives disc_info every time avail
    scan_dirs: (dirs, callback) =>
        #   @TODO: add logic around this instead of just scanning everything..
        for dir in dirs
            @scan_dir(path.join(@USER_SETTINGS.source_dir, dir), callback)
    
    #   Dir relay
    #   @param  dir str         Dir to list
    #   @param  callback        callback function
    #   @return Obj of items in folder, matching jstree specifications
    list_dir: (dir, callback) =>
        
        source_dir = @USER_SETTINGS.source_dir
        
        if dir in [undefined, '#']
            jailed_dir = source_dir
            dir = '/'
        else
            jailed_dir = path.join(source_dir, dir)
        
        console.log(dir + ' ' + jailed_dir)
        
        fs.readdir(jailed_dir, (err, dir_arr) =>

            folder_data = []
            
            valid_exts = ['img', 'iso']
            valid_exts.push.apply(@sanitizer.VID_EXTS)
            
            if dir_arr
                dir_arr.forEach((file) =>
                
                    relative_p = path.join(dir, file)
                    extension = file.split('.').pop()
                    stat = fs.statSync(path.join(jailed_dir, file))
                    
                    if stat and stat.isDirectory()
                        folder_data.push({
                            text: file, children: true, icon: 'folder', id: file
                        }) 
                    else if extension in valid_exts
                        folder_data.push({
                            text: file, children: false, icon: 'file', id: file
                        })
                        
                )
                
            console.log(folder_data)
            callback(folder_data)
        )
        
            
    #   Scan drives, return info. Also sets @drive_map
    #   @param  callback    Callback function, will receive drives as param
    #   @return drives Obj keyed by drive index, value is movie name
    scan_drives: (callback=false) =>
        
        if @toggle_busy(false, true) #< Make sure none of the discs are busy
            drives = {'cmd':NAMESPACE_SCAN, 'data':{}}
            @drive_map = {}
            #   Spawn MakeMKV with callback
            @_spawn_generic(['-r', 'info'], (code, drive_scan)=>
                try
                    for line in drive_scan
                        #   DRV to make sure it's drive output, /dev to make sure that there is a drive
                        if line[0..3] == 'DRV:' and line.indexOf('/dev/') != -1 
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
                catch err
                    console.log('disc_scan: ' + err)
                    
                @toggle_busy(false)

                if callback
                    callback(drives)
                else
                    drives
            )
    
    
    #   Receiver for udev change event. Fires media info to clients if it is a media disc.
    #       Also begins disc_info(device.DEVNAME)
    _udev_change: (device) =>
        
        if '1' in [device.ID_CDROM_DVD, device.ID_CDROM_BD, device.ID_CDROM_MEDIA]
            
            if device.ID_FS_LABEL
                
                console.log('Disc inserted' + device.DEVNAME)
                
                @_do_emit(@socket, {'cmd':'udev_update', 'data':{
                    'disc_id': device.DEVNAME,
                    'label': device.ID_FS_LABEL or device.ID_FS_LABEL_ENC
                }})
                
                #@_do_emit(@socket, {'cmd': '_panel_disable', 'data': {
                #    'disc_id':device.DEVNAME, "busy":true
                #}})
                
            else 
                console.log("Disc ejected " + device.DEVNAME)
            
            @disc_info(device.DEVNAME, (data) =>
                data['disc_id'] = device.DEVNAME
                console.log('??? --- ' + data['disc_id'])
                @_do_emit(@socket, data)
            )
        
    #   Error handler
    #   @param  type    str    Type of error
    #   @param  msg     str    Error msg
    _error: (type, msg) =>
        @_do_emit(@socket, {'cmd': '_error', 'data':{
            'type': type, 'msg': msg
        }})