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
        @MAKEMKV = new MakeMKV(@OUTPUT_DIR)
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
            
            derp = (msg)=>@do_broadcast(socket, msg)
            @MAKEMKV.scan_drives(derp)
            
            client.on('message', (data) =>
                console.log('Client sent: ', data)
            )
            
            client.on('disconnect', () =>
                console.log('client d/c')
            )
            
            client.on('emit_data', (data) =>
                client.broadcast.send(JSON.stringify(data))
            )
        )
            
    do_broadcast: (socket, msg) ->
        socket.sockets.send(JSON.stringify(msg))
        console.log(msg)
        
    do_disconnect: () ->
        # Maybe do something here?
        
        
server = new MakeMKVServer(1337)

