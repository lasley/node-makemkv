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
        
        #   Bind to receive/process socket cmds
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
            
    _bind: () =>
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
    
    _new_el: (id=false, class_=false, parent=false, type_='div') ->
        #   Create a new el
        #   @param  str id      ID of el
        #   @param  str class   Class of el
        #   @param  obj parent  perform parent.appendChild(this)
        #   @param  str type_   Type of element to create
        #   @return obj 
        el = document.createElement(type_)
        if id
            el.id = id
        if class_
            el.className = class_
        if parent
            parent.appendChild(el)
        el
    
    scan_drives: (socket_in) =>
        #   Callback for scan_drives cmd
        #       Displays all drive data
        #   @param  dict    socket_in  Data dict passed from server
        
        data = socket_in['data']
        
        _new_disc_panel = (drive, disc_name, width) =>
            #   Create a new disc panel on UI
            #   @param  str drive       Drive ID
            #   @param  str disc_name   Disc ID
            #   @param  int width       Grid width of panel container
            #   @return DivElement
            container = @_new_el(false, 'col-lg-' + width)
            panel = @_new_el(drive, 'panel panel-default', container)
            heading = @_new_el(false, 'panel-heading', panel)
            
            title = @_new_el(drive + '_title', 'panel-title', heading)
            title.innerHTML = disc_name
            
            body = @_new_el(drive + '_body', 'panel-body', panel)
            footer = @_new_el(false, 'panel-footer', panel)
            
            refresh_btn = @_new_el(false, 'btn btn-default disc-info-btn', \
                                  footer, 'button')
            refresh_btn.setAttribute('data-drive-id', drive)
            refresh_btn.setAttribute('type', 'button')
            refresh_btn.innerHTML = 'Get Info'
            refresh_btn.addEventListener('click', (event) =>
                drive_id = event.currentTarget.getAttribute('data-drive-id')
                @_socket_cmd('disc_info', drive_id)
            )
            
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
            #if disc #< Get extended disc info only if there's a disc
            #    @_socket_cmd('disc_info', drive)
            
    disc_info: (socket_in) =>
        #   Callback for disc_info cmd
        #       Displays disc info in disc pane
        
        data = socket_in['data']
        disc_panel = document.getElementById(data['disc_id']+'_body')
        disc_panel.innerHTML = ''
        
        #   Form and form container
        form = @_new_el(false, 'form-horizontal', disc_panel, 'form')
        form.setAttribute('role', 'form')
        form_div = @_new_el(false, 'form-group', form)
        
        #   Label for input
        label = @_new_el(false, 'col-sm-2 control-label', form_div, 'label')
        label.setAttribute('for', data['disc_id'] + '_name')
        label.innerHTML = 'Disc Name'
        
        #   Input container and input
        input_div = @_new_el(false, 'col-sm-10', form_div)
        input_el = @_new_el(data['disc_id'] + '_name', 'form-control', input_div, 'input')
        input_el.setAttribute('placeholder', data['disc']['Sanitized'])
        input_el.setAttribute('value', data['disc']['Sanitized'])
        
        #   Table for all the tracks
        table = @_new_el(false, 'table table-bordered table-condensed', disc_panel, 'table')
        
        #   Disc info headers
        headers = ['#', ]
        
        for track_id of data['tracks']
            row = @_new_el(false, false, table, 'tr')
            col = @_new_el(false, false, row, 'td')
            col.innerHTML = track_id
            for attr in ['orig_fn', ] 
                @_new_el(false, false, row, 'td').innerHTML = data['tracks'][track_id][attr]
                
    
    change_out_dir: (socket_in) ->
        #   Receive output dir and change on display
        #   @param  dict    socket_in    Data dict passed from server
        document.getElementById('output_dir').value = socket_in['data']
        
client = new MakeMKVClient()