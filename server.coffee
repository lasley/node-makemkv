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

    CLIENT_FILE: './client.html'
    SUCCESS_STRING: 'success'
    CLIENT_COFFEE: './client.coffee'
    OUTPUT_DIR: '/media/Motherload/nodemkv'

    constructor: (port) ->
        @MakeMKV = new MakeMKV(@OUTPUT_DIR)
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
                    when '/'
                        res.writeHead(200, {'Content-Type': 'text/html'})
                        res.end(fs.readFileSync(@CLIENT_FILE,
                                                {encoding:'utf-8'}))
                    when '/client'
                        res.writeHead(200, {'Content-Type': 'application/javascript'})
                        cs = fs.readFileSync(@CLIENT_COFFEE, {encoding:'utf-8'})
                        res.end(CoffeeScript.compile(cs))
                    when '/favicon.ico'
                        res.writeHead(200, {'Content-Type': 'image/x-icon'} );
                        res.end('Success')
                    when '/socket_in'
                        data_arr = []
                        req.on('data', (chunk) =>
                            data_arr.push(chunk.toString())   
                        )
                        req.on('end', () =>
                            res.writeHead(200, {'Content-Type':'text/html'})
                            send_data = {'app':path[1..], 'data': data_arr.join('')}
                            @do_broadcast(socket, send_data)
                            res.end(@SUCCESS_STRING)
                        )
                        
        ).listen(port)

        socket = io.listen(server)

        socket.on('connection', (client) =>
            
            single_broadcast = (data) => @do_emit(socket, data)
            
            #   Receive signals, perform actions
            client.on('display_cache', (data) =>
                #   Send cache to client
                multi_broadcast = (msgs)=>
                    for msg in msgs 
                        @do_emit(socket, msg)
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
            
    do_emit: (socket, msg) ->
        cmd = msg['cmd']
        data = msg['data']
        console.log(data)
        socket.sockets.emit(cmd, data)
        
    do_disconnect: () ->
        # Maybe do something here?
        
        
server = new MakeMKVServer(1337)

