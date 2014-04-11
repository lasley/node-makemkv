#!/usr/bin/env coffee
###
#   Remote MakeMKV client logic
#         
#   Display MakeMKV stats to user, send commands to server
#    
#   @author     David Lasley, dave@dlasley.net
#   @website    https://dlasley.net/blog/projects/remote-makemkv/
#   @package    remote-makemkv
#   @license    GPLv3
#   @version    $Id: remote_makemkv_server.py 102 2013-02-06 01:27:56Z dave@dlasley.net $
###

class MakeMKVClient

    constructor: () -> 
        #   Construct the socket, set callbacks
        socket = io.connect('192.168.69.104:1337')
        socket.on('connect', () ->
            console.log('Connected to server');
            socket.send('Client Connected');
        )
        socket.on('message', (data) =>
            console.log(data);
            data = JSON.parse(data);
            switch (data['cmd'])
                when 'change_out_dir' then @change_out_dir(data['data'])
                when 'scan_drives' then @scan_drives(data['data'])
        )
        socket.on('disconnect', () ->
            console.log('d/c');
        );
        
    scan_drives: (data) =>
        #   Callback for scan_drives cmd
        #       Displays all drive data
        #   @param  dict    data    Data dict passed from server
        div = document.getElementById('main')
        data_keys = Object.keys(data)
        col_width = Math.floor(12 / data_keys.length)
        for drive in data_keys
            console.log(drive)
            disc = data[drive]
            col = document.createElement('div')
            col.innerHTML = drive + ' ' + disc
            col.className = 'col-md-' + col_width
            div.appendChild(col)
            
    change_out_dir: (data) =>
        #   Receive output dir and change on display
        #   @param  dict    data    Data dict passed from server
        document.getElementById('output_dir').value = data
        
client = new MakeMKVClient()