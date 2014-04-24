Node-MakeMKV is the successor to [[https://blog.dlasley.net/?p=399|Remote-MakeMKV]]. The intent of this project is to provide a web front end for MakeMKV to allow for a headless Linux ripping server. This application is written in CoffeeScript and Node.js, therefore it is only compatible with Linux servers. The client has been successfully tested in all major desktop and mobile browsers.

[[[TOC]]]

=Downloads=

[[http://blog.dlasley.net/user-files/uploads/node-makemkv-alpha1_node-makemkv-alpha1.tar.bz2|Node-MakeMKV Alpha1]]

=Installation=

* [[installing-node-js-and-coffeescript|Install Node.js and CoffeeScript]]
* Edit the `[settings]` section of `server_settings.ini` per the below specifications:

{| style="max-width: 600px; margin-left: auto; margin-right: auto;"
! **Variable** !! **Description**
|-
| `output_dir` || Root ripping directory. Folders for each rip will be created inside of this directory.
|-
| `listen_port` || Port to listen on, defaults to `1337`
|-
| `makemkvcon_path` || Full path to makemkvcon binary, most likely won't need to be changed
|}

* Default MakeMKV selection profile as defined in ~/.MakeMKV/settings.conf will be used for track selections. I am currently working on defining these programmatically.

=Usage=

* Run the server - `coffee ./server.coffee`

* Navigate to `SERVER_HOSTNAME:LISTEN_PORT` to view the GUI
  [[image:node-makemkv-gui-1.png|center|medium|link=source]]

* Click the `Refresh Drives` button to scan available drives for discs
  [[image:node-makemkv-refresh-1.png|center|medium|link=source]]

* Click any of the `Get Info` buttons to get disc level information for a specific drive. Panels with the header title `None` do not have a valid disc in the drive (or some other drive level error)
  [[image:node-makemkv-getinfo-1.png|center|medium|link=source]]

* Once the disc has been scanned, track information will be displayed in the disc panel. Use the checkboxes in the rip column to select which tracks you would like to rip, and the `Rip Tracks` button to initiate ripping. The `Disc Name` field can be used to define the folder that MakeMKV will rip into for this disc (relative to the `Output Directory` defined earlier)
  [[image:node-makemkv-discinfo-panel-1.png|center|medium|link=source]]

=Repo=
[[https://repo.dlasley.net/remote_makemkv/file/0ec3db7cb4ef|Mercurial]]
[[https://github.com/dlasley/remote-makemkv|GitHub]]
