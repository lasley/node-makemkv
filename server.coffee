#!/usr/bin/env node
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

http = require('http')
io = require('socket.io')
url = require('url')
fs = require('fs')
path = require('path')
CoffeeScript = require('coffee-script')
MakeMKV = require('./makemkv.coffee')

class MakeMKVServer extends MakeMKV

    CLIENT_FILE: path.join(__dirname, 'client.html')
    TREEVIEW_FOLDER: path.join(__dirname, 'bootstrap-treeview', 'dist')
    SUCCESS_STRING: 'success'
    CLIENT_COFFEE: path.join(__dirname, 'client.coffee')

    constructor: (port) ->
        
        super(false) #< MakeMKV obj init
        @cache = {}
        @change_out_dir() #< Prime the out dir cache
        
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
                        res.end(@SUCCESS_STRING)
                    )
                
                when 'GET'
            
                    switch path_
                        
                        when '/' #< Serve static client html
                            res.writeHead(200, {'Content-Type': 'text/html'})
                            fs.readFile(@CLIENT_FILE, {encoding:'utf-8'}, (err, data)->res.end(data))

                        when '/client' #< Serve the client coffeescript
                            res.writeHead(200, {'Content-Type': 'application/javascript'})
                            fs.readFile(@CLIENT_COFFEE, {encoding:'utf-8'}, (err, data) ->
                                res.end(CoffeeScript.compile(data)) #< @todo globalize the load, this is good for testing
                            )
                        
                        when '/favicon.ico' #< Favicon
                            res.writeHead(200, {'Content-Type': 'image/x-icon'} )
                            #   @todo..make an icon
                            res.end('Success')
                            
                        when '/list_dir' #< List dir
                            res.writeHead(200, {'Content-Type': 'application/javascript'})
                            @list_dir(parsed_url.query['id'], (dir)=>res.end(JSON.stringify(dir)))
                        
        ).listen(@LISTEN_PORT)
        
        @socket = io.listen(server)
        console.log('Listening on ' + @LISTEN_PORT)
        
        #   Bind socket actions on client connect
        @socket.on('connection', (client) =>
            
            single_broadcast = (data) =>
                @_do_emit(@socket, data)
            
            #   Send cache to client
            _display_cache = () =>
                @display_cache((msgs)=>
                    for msg in msgs 
                        client.emit(msg.cmd, msg.data)
                )
                
            _display_cache() #< Actually send it
            
            client.on('display_cache', (data) =>
                _display_cache()
            )
            
            #   User has sent command to change save_dir
            client.on('change_out_dir', (data) =>
                console.log('changing out dir')
                @save_out_dir(data, single_broadcast)
            )
            
            #   User has sent command to scan drives
            client.on('scan_drives', (data) =>
                console.log('scanning drives')
                @_do_emit(@socket, {'cmd':'_panel_disable', 'data':{'disc_id':'all', "busy":true}})
                @scan_drives(single_broadcast)
            )
            
            #   User has sent command to retrieve single disc info
            client.on('disc_info', (data) =>
                console.log('getting disc info for', data)
                @_do_emit(@socket, {'cmd':'_panel_disable', 'data':{'disc_id':data, "busy":true}})
                @disc_info(data, single_broadcast)
            )
            
            #   User has sent command to retrieve single disc info
            client.on('rip_track', (data) =>
                console.log('getting disc info for', data)
                @_do_emit(@socket, {'cmd':'_panel_disable', 'data':{'disc_id':data.drive_id, "busy":true}})
                @rip_track(data['save_dir'], data['drive_id'], data['track_ids'], single_broadcast)
            )
            
            #   User is browsing a directory, only send to them
            client.on('list_dir', (data) =>
                console.log('listing dir ' + data)
                @list_dir(data, (dir) => client.emit('list_dir', dir))
            )
            
            client.on('scan_dirs', (data) =>
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
            
        )

    ##  Send cached data to client in logic order
    #       scan_drives, disc_info, rip_track
    display_cache: (callback=false) =>
        
        cmd_order = ['change_out_dir', 'scan_drives', 'disc_info', 'rip_track']
        cached = []
        for cmd in cmd_order
            if typeof(@cache[cmd]) == 'object'
                for namespace of @cache[cmd]
                    cached.push({'cmd':cmd, 'data':@cache[cmd][namespace]})
        
        #   Disable busy drive panels
        for disc_id, busy of @busy_devices
            cached.push({'cmd':'_panel_disable', 'data':{'disc_id':disc_id, 'busy':busy}})
        
        if callback
            callback(cached)
        else
            cached

    ##  Signal emit
    #   @param  socket  socket  socket
    #   @param  dict    msg     Msg, {'cmd':(str)signal_to_emit,'data':(dict)}
    _do_emit: (socket, msg) ->
        
        cmd = msg['cmd']
        data = msg['data']
        
        if data['data'] #< If there's a second data dimension (cached)
            data = data['data'] #< Pull and save it instead
            
        namespace = if data['disc_id'] then data['disc_id'] else 'none'
        data = @cache_data(cmd, data, namespace)
        socket.sockets.emit(cmd, data)    

    ##  Cache data to variable for when clients join
    #   @param  str     cmd     Command that will be emitted
    #   @param  mixed   data    Data obj
    #   @param  str     namespace   Namespace to cache data in (multiple single drive cmds)
    #   @return dict    data with cache_refreshed date {'data':mixed, 'cache_refreshed':Date}
    cache_data: (cmd, data, namespace='none') =>
        
        if typeof(@cache[cmd]) != 'object'
            @cache[cmd] = {}

        @cache[cmd][namespace] = {'cache_refreshed': new Date(), 'data': data }
        
        @cache[cmd][namespace]
    
    ##  Register change to save directory (UI)
    change_out_dir: () =>
        
        @cache_data('change_out_dir', @save_to)

    ##  Save change to save directory
    #   @param  str dir New save dir
    save_out_dir: (dir, callback=false) =>
        
        @save_to = dir
        @change_out_dir()
        
        if callback
            callback(@save_to)
        else
            @save_to
    
    ##  Scan directories with MakeMKV
    #   @param  list    dirs    Directories to scan
    #   @param  func    callback    callback function, receives disc_info every time avail
    scan_dirs: (dirs, callback) =>

        #   @todo - add logic around this instead of just scanning everything..
        for dir in dirs
            @scan_dir(path.join(@USER_SETTINGS.source_dir, dir), callback)
        
    
    ##  Dir relay
    #   @param  str     dir         Dir to list
    #   @param  func    callback    callback function
    #   @return dict    Dict of items in folder, matching jstree specifications
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
        
        
    ##  Error handler
    #   @param  str type    Type of error
    #   @param  str msg     Error msg
    error: (type, msg) =>
        @
        
server = new MakeMKVServer()

server.emitter.on('error', (type, msg) =>
    server._do_emit(server.socket, {'cmd':'_error', 'data':{'type':type, 'msg':msg}})
)