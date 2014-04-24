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
        @socket = io.connect(window.location.host)
        
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
            
    _bind: () =>
        #   Bind client events
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

            @_panel_disable(panel, true)
            
            checked_boxes = []
            for check in panel.find('input[type="checkbox"]')
                if check.checked
                    checked_boxes.push(check.getAttribute('data-track-id'))
                
            @_socket_cmd('rip_track', {
                'save_dir':save_dir, 'drive_id':drive_id,
                'track_ids':checked_boxes
            })
        )
        
        $('#main').on('click', '.panel-title', (event) =>
            panel = document.getElementById(event.currentTarget.id.split('_')[0]) #< id=disc_title
            @_panel_collapse(panel))
        
    _socket_cmd: (cmd, data) =>
        #   Send JSON.stringify(data)
        #   @param  str     cmd     Command that is being performed
        #   @param  mixed   data    Data to send
        @socket.emit(cmd, data)
    
    _new_el: (parent=false, class_=false, type_='div', kwargs={}) ->
        #   Create a new el
        #   @param  obj parent  perform parent.appendChild(this)
        #   @param  str class_  Class of el
        #   @param  str type_   Type of element to create
        #   @param  obj kwargs  Dict of attrs to set
        #   @return obj 
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
            panel = @_new_el(container, 'panel panel-default', 'div', {id:drive})
            heading = @_new_el(panel, 'panel-heading')
            header_container = @_new_el(heading)
            
            if not disc_name
                disc_name = 'None'
            
            title = @_new_el(header_container, 'panel-title', 'div', {
                html:disc_name, id:drive + '_title'
            })
            title.css('cursor', 'pointer')

            glyph = @_new_el(title, 'glyphicon glyphicon-minus', 'span')

            body = @_new_el(panel, 'panel-body', 'div', {id:drive + '_body'})
            footer = @_new_el(panel, 'panel-footer', 'div')
            
            footer_div = @_new_el(footer, 'row')
            
            #   Get Disc Info Button
            refresh_btn = @_new_el(
                @_new_el(footer_div, 'col-md-1'),
                'btn btn-default disc-info-btn get-info', 'button',
                {'data-drive-id':drive, 'type':'button', html:'Get Info',}
            )

            #   Rip Tracks Button
            rip_btn = @_new_el(
                @_new_el(footer_div, 'col-md-1 col-md-offset-9'),
                'btn btn-default disc-info-btn hidden rip-tracks', 'button',
                {'data-drive-id':drive, 'type':'button', html:'Rip Tracks',}
            )
            
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
            
    disc_info: (socket_in) =>
        #   Callback for disc_info cmd
        #       Displays disc info in disc pane
        
        data = socket_in['data']
        
        #   Get Disc panel body and clear it
        disc_panel = $(document.getElementById(data['disc_id'] + '_body'))
        disc_panel.html('')
        
        #   New title
        document.getElementById('/dev/sr3_title').childNodes[0].nodeValue = data['disc']['Name']
        
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
        
        row = @_new_el(@_new_el(table, false, 'thead'), false, 'tr')
        row.css('cursor', 'pointer')
        
        for header of headers
            col = @_new_el(row, false, 'th', {html:header})
            if header == 'Size'
                col.attr('data-metric-name', 'b|byte')
                col.addClass('sorter-metric')

        tbody = @_new_el(table, false, 'tbody')
        
        #   Loop tracks, display data
        for track_id, track_data of data['tracks']
            
            #   Initial row, track #, checkboxes
            row = @_new_el(tbody, false, 'tr')
            
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
                    
        table.tablesorter()
                    
        #   Un-hide Rip Button
        panel = $(document.getElementById(data['disc_id']))
        $(panel.find('.rip-tracks')[0]).removeClass('hidden')
        
    rip_track: (socket_in) =>
        #   Receive track rip status, output to GUI
        #   @param  dict    socket_in    Data dict passed from server
        console.log(socket_in)
        
        data = socket_in['data']
        panel = $(document.getElementById(data['disc_id']))
        
        @_panel_disable(panel, false)

        for track_id, result of data['results']
            result =  if result then 'bg-success' else 'bg-danger'
            chk_box = panel.find('input[data-track-id="' + track_id + '"]')
            $(chk_box).parent().parent().removeClass().addClass(result)
            

    change_out_dir: (socket_in) ->
        #   Receive output dir and change on display
        #   @param  dict    socket_in    Data dict passed from server
        
        document.getElementById('output_dir').value = socket_in['data']
        
    _panel_collapse: (panel) ->
        ##  UI function to (un)collapse panel
        #   @param  obj panel   Bootstrap3 Panel obj
        panel = $(panel)
        body = $(panel.children('.panel-body')[0])
        glyph =  $(panel.find('.glyphicon')[0])
        
        body.toggleClass('hidden')
        glyph.toggleClass('glyphicon-minus')
        glyph.toggleClass('glyphicon-plus')
        
        #   Clear most likely unintentional selection
        if window.getSelection
            if window.getSelection().empty #< Chrome
                window.getSelection().empty()
            else if window.getSelection().removeAllRanges #< FF
                window.getSelection().removeAllRanges()
        else if document.selection #< IE
            document.selection.empty()
            
    _panel_disable: (panel, disable=true) ->
        panel.find(':input').prop('disabled', disable)
            
client = new MakeMKVClient()