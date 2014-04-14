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
#   @version    $Id: link_checker.py,v 12d42dd25501 2013/10/11 20:29:34 dlasley $
###
__version__ = "$Revision: 12d42dd25501 $"

http = require('http')
io = require('socket.io')
url = require('url')
fs = require('fs')
CoffeeScript = require('coffee-script')
MakeMKV = require('./makemkv.coffee')


class MakeMKVServer

    CLIENT_FILE: __dirname + '/client.html'
    SUCCESS_STRING: 'success'
    CLIENT_COFFEE: __dirname + '/client.coffee'

    constructor: (port) ->
        @MakeMKV = new MakeMKV(false)
        @cache = {}
        server = http.createServer((req, res) =>
            req.setEncoding 'utf8'
            path = url.parse(req.url).pathname
            if req.method == 'POST'
                req.on('data', (chunk) =>
                    data = JSON.parse(chunk.toString())
                    @do_broadcast(socket, {'app':path[1..], 'data':data})
                    res.end(@SUCCESS_STRING)
                )
            else
                switch path
                    when '/' #< Serve static client html
                        res.writeHead(200, {'Content-Type': 'text/html'})
                        res.end(fs.readFileSync(@CLIENT_FILE,
                                                {encoding:'utf-8'}))
                    when '/client' #< Serve the client coffeescript
                        res.writeHead(200, {'Content-Type': 'application/javascript'})
                        cs = fs.readFileSync(@CLIENT_COFFEE, {encoding:'utf-8'})
                        res.end(CoffeeScript.compile(cs)) #< @todo globalize the load, this is good for testing
                    when '/favicon.ico' #< Favicon
                        res.writeHead(200, {'Content-Type': 'image/x-icon'} )
                        #   @todo..make an icon
                        res.end('Success')
                        
        ).listen(port)

        socket = io.listen(server)
        
        #   Bind socket actions on client connect
        socket.on('connection', (client) =>
            
            single_broadcast = (data) => @do_emit(socket, data)
            
            client.on('display_cache', (data) =>
                #   Send cache to client
                multi_broadcast = (msgs)=>
                    for msg in msgs 
                        single_broadcast(msg)
                @MakeMKV.display_cache(multi_broadcast)
            )
            
            client.on('change_out_dir', (data) =>
                #   User has sent command to change save_dir
                console.log('changing out dir')
                @MakeMKV.change_out_dir(data, single_broadcast)
            )
            
            client.on('scan_drives', (data) =>
                #   User has sent command to scan drives
                console.log('scanning drives')
                @MakeMKV.scan_drives(single_broadcast)
            )
            
            client.on('disc_info', (data) =>
                #   User has sent command to retrieve single disc info
                console.log('getting disc info for', data)
                @MakeMKV.disc_info(data, single_broadcast)
            )
            
            #   Socket debugging
            client.on('message', (data) ->
                console.log('Client sent:', data)
            )
            client.on('disconnect', () ->
                console.log('Client d/c')
            )
            
        )
        
    display_cache: (callback=false) =>
        #   Send cached data to client in logic order
        #       scan_drives, disc_info, rip_track
        cmd_order = ['change_out_dir', 'scan_drives', 'disc_info', 'rip']
        cached = []
        for cmd in cmd_order
            if typeof(@cache[cmd]) == 'object'
                for namespace of @cache[cmd]
                    cached.push({'cmd':cmd, 'data':@cache[cmd][namespace]})
        
        console.log(cached)
        
        if callback
            callback(cached)
        else
            cached
            
    do_emit: (socket, msg) ->
        #   Signal emit
        #   @param  socket  socket  socket
        #   @param  dict    msg     Msg, {'cmd':(str)signal_to_emit,'data':(dict)}
        cmd = msg['cmd']
        data = msg['data']
        namespace = if data['disc_id'] then data['disc_id'] else 'none'
        data = @_cache_data(cmd, data, namespace)
        console.log(data)
        socket.sockets.emit(cmd, data)
        
    _cache_data: (cmd, data, namespace=false) =>
        #   Cache data to variable for when clients join
        #   @param  dict    data    Data obj, must contain keys `cmd`, `data`
        #   @param  str     namespace   Namespace to cache data in (multiple single drive cmds)
        #   @return mixed   return `data` key of input with cache_refreshed date
        
        if typeof(@cache[data['cmd']]) != 'object'
            @cache[data['cmd']] = {}

        @cache[data['cmd']][namespace] = {'cache_refreshed': new Date(), \
                                           'data': data['data'] }

        @cache[data['cmd']][namespace]
    
    change_out_dir: (dir, callback=false) =>
        #   Register change to save directory
        @MakeMKV.save_to = dir
        @cache_data({'cmd':'change_out_dir', 'data':@MakeMKV.save_to})
        if callback
            callback(@MakeMKV.save_to)
        else
            @MakeMKV.save_to
        
        
server = new MakeMKVServer(1337)

