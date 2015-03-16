# Node MakeMKV: The Missing Web UI


 Node-MakeMKV is the successor to [Remote-MakeMKV](https://blog.dlasley.net/2013/01/remote-makemkv/). The intent of this project is to provide a web front end for MakeMKV to allow for a headless ripping server. This application is written in CoffeeScript and Node.js. The server has been successfully tested on Linux (Ubuntu and CentOS). The client has been successfully tested in all major desktop and mobile browsers.
 

## Installation [∞](#installation "Link to this section")

*   [Install MakeMKV](http://www.makemkv.com/)
*   [Install Node.js and CoffeeScript](https://blog.dlasley.net/2014/04/installing-node-js-and-coffeescript/)
*   Install libudev-dev (to monitor disc drives for changes - optional)
*   Install NodeMakemkv - `npm install node-makemkv`
*   Copy default conversion profile and edit to your liking - `cp conversion_profile.dist.xml conversion_profile.xml`
*   Copy settings file - `cp settings.dist.json settings.json`
*   Edit the `USER_SETTINGS` section of `settings.json` per the below specifications:

Variable | Description
---------|-------------
`output_dir` | Root ripping directory. Folders for each rip will be created inside of this directory.
`source_dir` | Jail directory for client side browsing/ripping (`Browse Filesystem` button)
`listen_port` | Port to listen on, defaults to `1337`
`makemkvcon_path` | Full path to makemkvcon binary, most likely won’t need to be changed
`outlier_modifier` | For auto track selection, higher is more restrictive (selected if trackSize &gt;= discSizeUpperQuartile*outlier_modifier)

*   Default MakeMKV selection profile as defined in ~/.MakeMKV/settings.conf will be used for track selections.

## Usage [∞](#usage "Link to this section")

*   Run the server – `coffee ./run.coffee` – _Note: you must run the server as a user that has permissions to read from optical media_

*   Navigate to `http://$SERVER_IP:$LISTEN_PORT` to view the GUI

    ![node-makemkv-gui-1.png](https://blog.dlasley.net/user-files/uploads/2014/04/node-makemkv-gui-1.png "node-makemkv-gui-1.png")

*   Click the `Refresh Drives` button to scan available drives for discs

    ![node-makemkv-refresh-1.png](https://blog.dlasley.net/user-files/uploads/2014/04/node-makemkv-refresh-1.png "node-makemkv-refresh-1.png")

*   Click any of the `Refresh Disc` buttons to get disc level information for a specific drive. Panels with the header title `None` do not have a valid disc in the drive (or some other drive level error)

    ![node-makemkv-getinfo-1.png](https://blog.dlasley.net/user-files/uploads/2014/04/node-makemkv-getinfo-1.png "node-makemkv-getinfo-1.png")</div>

*   Once the disc has been scanned, track information will be displayed in the disc panel. Use the checkboxes in the rip column to select which tracks you would like to rip, and the `Rip Tracks` button to initiate ripping. The `Disc Name` field can be used to define the folder that MakeMKV will rip into for this disc (relative to the `Output Directory` defined earlier)

    ![node-makemkv-discinfo-panel-1.png](https://blog.dlasley.net/user-files/uploads/2014/04/node-makemkv-discinfo-panel-1.png "node-makemkv-discinfo-panel-1.png")

## Repos [∞](#repos "Link to this section")

*   [GitHub](https://github.com/dlasley/node-makemkv)
*   [Private Mirror](https://repo.dlasley.net/projects/VID/repos/node-makemkv/browse)
