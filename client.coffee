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

    constructor: (bind=true) -> 
        #   Construct the socket, set callbacks
        #   @param  bool    bind    Bind the buttons? Default, yes
        @socket = io.connect('192.168.69.104:1337')
        
        @socket.on('connect', () =>
            console.log('Connected to server');
            @socket.send('Client Connected');
            @socket.emit('display_cache', true)
        )
        
        #   Receive/process socket cmds
        @socket.on('change_out_dir', (data) => @change_out_dir(data))
        @socket.on('scan_drives', (data) => @scan_drives(data))
        @socket.on('disc_info', (data) => @disc_info(data))
        
        #   Socket debugging
        @socket.on('message', (data) =>
            console.log('Client sent: ', data);
        )
        @socket.on('disconnect', () ->
            console.log('d/c');
        )
        
        
        if bind
            @_bind()
            
    _bind: () ->
        #   Bind client events
        $('#send_out_dir').on('click', (event) =>
            new_dir = $('#output_dir').val()
            @_socket_cmd('change_out_dir', new_dir)
        )
        
        $('#refresh_all').on('click', (event) =>
            @_socket_cmd('scan_drives', true)
        )
        
    _socket_cmd: (cmd, data) =>
        #   Send JSON.stringify(data)
        #   @param  str     cmd     Command that is being performed
        #   @param  mixed   data    Data to send
        @socket.emit(cmd, data)
        
    scan_drives: (data) =>
        #   Callback for scan_drives cmd
        #       Displays all drive data
        #   @param  dict    data    Data dict passed from server
        
        _new_el = (id=false, class_=false) ->
            div = document.createElement('div')
            if id
                div.id = id
            if class_
                div.className = class_
            div
        
        _new_disc_panel = (drive, disc_name, width) =>
            #   Create a new disc panel on UI
            #   @param  str drive       Drive ID
            #   @param  str disc_name   Disc ID
            #   @param  int width       Grid width of panel container
            #   @return DivElement
            container = _new_el(false, 'col-md-' + width)
            panel = _new_el(drive, 'panel panel-default')
            title = _new_el(drive+ '-title', 'panel-title')
            title.innerHTML = disc_name
            panel.appendChild(title)
            container.appendChild(panel)
            container
        
        main_div = document.getElementById('main')
        main_div.innerHTML = ''
        
        #   Have to extract keys because the obj doesn't have a len
        data_keys = Object.keys(data)
        col_width = Math.floor(12 / data_keys.length)
        for drive in data_keys
            console.log(drive)
            disc = data[drive]
            main_div.appendChild(_new_disc_panel(drive, disc, col_width))
            if disc #< Get extended disc info only if there's a disc
                @_socket_cmd('disc_info', drive)
            
    disc_info: (data) ->
        #   Callback for disc_info cmd
        #       Displays disc info in disc pane
        disc_panel = $('#'+data['disc_id'])
        
    
    change_out_dir: (data) ->
        #   Receive output dir and change on display
        #   @param  dict    data    Data dict passed from server
        document.getElementById('output_dir').value = data
        
client = new MakeMKVClient()