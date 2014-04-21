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

    #   Construct the socket, set callbacks
    #   @param  bool    bind    Bind the buttons? Default, yes
    constructor: (bind=true) -> 
        @socket = io.connect('192.168.69.104:1337')
        
        @socket.on('connect', () =>
            console.log('Connected to server')
            @socket.send('Client Connected')
            @socket.emit('display_cache', true)
        )
        
        #   Bind to receive/process socket cmds
        @socket.on('change_out_dir', (data) => @change_out_dir(data))
        @socket.on('scan_drives', (data) => @scan_drives(data))
        @socket.on('disc_info', (data) => @disc_info(data))
        @socket.on('rip_track', (data) => @rip_track(data))
        
        #   Socket debugging
        @socket.on('message', (data) =>
            console.log('Client sent: ', data);
        )
        @socket.on('disconnect', () ->
            console.log('d/c');
        )
        
        
        if bind
            @_bind()
    
    #   Bind client events    
    _bind: () =>
        
        $('#send_out_dir').on('click', (event) =>
            new_dir = $('#output_dir').val()
            @_socket_cmd('change_out_dir', new_dir)
        )
        
        $('#refresh_all').on('click', (event) =>
            @_socket_cmd('scan_drives', true)
        )

        $('#main').on('click', '.get-info', (event) =>
            drive_id = event.currentTarget.getAttribute('data-drive-id')
            @_socket_cmd('disc_info', drive_id)
        )
        
        $('#main').on('click', '.rip-tracks', (event) =>
            
            drive_id = event.currentTarget.getAttribute('data-drive-id')
            panel = $(document.getElementById(drive_id))
            save_dir = document.getElementById(drive_id + '_name').value
            
            checked_boxes = []
            for check in panel.find('input[type="checkbox"]')
                if check.checked
                    checked_boxes.push(check.getAttribute('data-track-id'))
                
            @_socket_cmd('rip_track', {
                'save_dir':save_dir, 'drive_id':drive_id,
                'track_ids':checked_boxes
            })
        )

    #   Send JSON.stringify(data)
    #   @param  str     cmd     Command that is being performed
    #   @param  mixed   data    Data to send
    _socket_cmd: (cmd, data) =>

        @socket.emit(cmd, data)

    #   Create a new el
    #   @param  obj parent  perform parent.appendChild(this)
    #   @param  str class_  Class of el
    #   @param  str type_   Type of element to create
    #   @param  obj kwargs  Dict of attrs to set
    #   @return obj 
    _new_el: (parent=false, class_=false, type_='div', kwargs={}) ->

        el = $(document.createElement(type_))
        
        if class_
            el.addClass(class_)
            
        if parent
            #   Handle both jQuery and non
            if parent.append 
                parent.append(el)
            else
                $(parent).append(el)
        
        for attr of kwargs
            switch(attr)
                when 'html' then el.html(kwargs[attr])
                else el.attr(attr, kwargs[attr])
        
        el

    #   Callback for scan_drives cmd
    #       Displays all drive data
    #   @param  dict    socket_in  Data dict passed from server
    scan_drives: (socket_in) =>
        
        data = socket_in['data']

        #   Create a new disc panel on UI
        #   @param  str drive       Drive ID
        #   @param  str disc_name   Disc ID
        #   @param  int width       Grid width of panel container
        #   @return DivElement    
        _new_disc_panel = (drive, disc_name, width) =>
    
            container = @_new_el(false, 'col-lg-' + width)
            panel = @_new_el(container, 'panel panel-default', 'div', {id:drive})
            heading = @_new_el(panel, 'panel-heading')
            header_container = @_new_el(heading)
            
            title = @_new_el(header_container, 'panel-title', 'div', {
                html:disc_name, id:drive + '_title'
            })
            
            #   `-`/`+` glyph
            glyph = @_new_el(header_container, 'glyphicon glyphicon-minus', 'span',
                             {'cursor':'pointer'})
            glyph.on('click', (event) => @_panel_collapse(panel))

            body = @_new_el(panel, 'panel-body', 'div', {id:drive + '_body'})
            footer = @_new_el(panel, 'panel-footer', 'div')
            
            #   Get Disc Info Button
            refresh_btn = @_new_el(
                footer, 'btn btn-default disc-info-btn get-info', 'button', {
                    'data-drive-id':drive, 'type':'button', html:'Get Info',
            })

            #   Rip Tracks Button
            rip_btn = @_new_el(
                footer, 'btn btn-default disc-info-btn hidden rip-tracks', 'button', {
                    'data-drive-id':drive, 'type':'button', html:'Rip Tracks',
            })
            
            container
        
        main_div = $('#main')
        main_div.html('')
        
        cnt = 0
        for drive, disc of data
            console.log(drive)
            #disc = data[drive]
            
            if cnt%2 == 0
                row = @_new_el(main_div, 'row')
            
            row.append(_new_disc_panel(drive, disc, 6))
            cnt += 1
            
            #if disc #< Get extended disc info only if there's a disc
            #    @_socket_cmd('disc_info', drive)

    #   Callback for disc_info cmd
    #       Displays disc info in disc pane
    disc_info: (socket_in) =>
        
        data = socket_in['data']
        
        #   Get Disc panel body and clear it
        disc_panel = $(document.getElementById(data['disc_id'] + '_body'))
        disc_panel.html('')
        
        #   Form and form container
        form = @_new_el(disc_panel, 'form-horizontal', 'form', {role:'form'})
        form_div = @_new_el(form, 'form-group')
        
        #   Label for input
        label = @_new_el(form_div, 'col-sm-2 control-label', 'label', { 
            'for':data['disc_id'] + '_name', html: 'Disc Name'
        })
        
        #   Input container and input
        input_div = @_new_el(form_div, 'col-sm-10')
        input_el = @_new_el(input_div, 'form-control', 'input', {
            placeholder:data['disc']['Sanitized'], value:data['disc']['Sanitized'],
            id:data['disc_id'] + '_name'
        })
        
        #   Table for all the tracks (and the responsive container for it)
        tbl_cont = @_new_el(disc_panel, 'table-responsive')
        table = @_new_el(tbl_cont, 'table table-bordered table-condensed table-hover', 'table')
        
        #   Disc info header map and loop
        headers = {
            'Rip':false, '#':false, 'Source':'Source File Name', 
            'Chptrs':'Chapter Count', 'Size':'Disk Size', 'Track Types':'_ttypes',
            'S-Map':'Segments Map',
        }
        
        row = @_new_el(table, false, 'tr')
        for header of headers
            col = @_new_el(row, false, 'th', {html:header})
        
        #   Loop tracks, display data
        for track_id, track_data of data['tracks']
            
            #   Initial row, track #, checkboxes
            row = @_new_el(table, false, 'tr')
            
            col = @_new_el(row, false, 'td')
            @_new_el(col, false, 'input', {
                type:'checkbox', 'data-track-id':track_id, 
                'data-autochecked':track_data['autochk']
            })
            
            col = @_new_el(row, false, 'td', {html:track_id})
            
            #   Fill Track Type Cnts
            track_cnts = track_data['cnts']
            cnt_key_order = ['Video', 'Audio', 'Subtitles']
            track_data['_ttypes'] = []
            for key in cnt_key_order
                track_data['_ttypes'].push('<em>' + key + ':</em>' + track_cnts[key])
            track_data['_ttypes'] = track_data['_ttypes'].join(', ')
            
            #   Loop the rest of the cols
            for _, header of headers
                if header
                    col_data = track_data[header]
                    @_new_el(row, false, 'td', {html:col_data})
                    
        #   Un-hide Rip Button
        panel = $(document.getElementById(data['disc_id']))
        $(panel.find('.rip-tracks')[0]).removeClass('hidden')

    #   Receive track rip status, output to GUI
    #   @param  dict    socket_in    Data dict passed from server        
    rip_track: (socket_in) =>

        console.log(socket_in)
        
        data = socket_in['data']
        panel = $(document.getElementById(data['disc_id']))
        
        for result, track_id of data['results']
            result =  if result[track_id] then 'bg-success' else 'bg-danger'
            chk_box = panel.find('input[data-track-id="' + track_id + '"]')
            $(chk_box).parent().removeClass().addClass(result)
            
    #   Receive output dir and change on display
    #   @param  dict    socket_in    Data dict passed from server
    change_out_dir: (socket_in) ->
        
        document.getElementById('output_dir').value = socket_in['data']
        
    ##  UI function to (un)collapse panel
    #   @param  obj panel   Bootstrap3 Panel obj
    _panel_collapse: (panel) ->

        panel = $(panel)
        body = $(panel.children('.panel-body')[0])
        glyph =  $(panel.find('.glyphicon')[0])
        
        body.toggleClass('hidden')
        glyph.toggleClass('glyphicon-minus')
        glyph.toggleClass('glyphicon-plus')
        
client = new MakeMKVClient()