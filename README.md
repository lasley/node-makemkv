#### This is a conversion from instructions located at https://blog.dlasley.net/projects/remote-makemkv/ 

#### Apologies, I'm working on a real Markdown version...

# Node MakeMKV: The Missing Web UI


 Node-MakeMKV is the successor to [Remote-MakeMKV](https://blog.dlasley.net/2013/01/remote-makemkv/). The intent of this project is to provide a web front end for MakeMKV to allow for a headless ripping server. This application is written in CoffeeScript and Node.js. The server has been successfully tested on Linux (Ubuntu and CentOS). The client has been successfully tested in all major desktop and mobile browsers.

<div class="toc">
<div class="toc-title">Table of Contents <span class="toc-toggle">[[hide](javascript:toggle_toc(399);)]</span></div>
<div id="_toclist_399">

*   [<span class="tocnumber">1</span> <span class="toctext">Downloads</span>](#downloads)
*   [<span class="tocnumber">2</span> <span class="toctext">Installation</span>](#installation)
*   [<span class="tocnumber">3</span> <span class="toctext">Usage</span>](#usage)
*   [<span class="tocnumber">4</span> <span class="toctext">Repos</span>](#repos)
</div>
</div>

## Downloads [∞](#downloads "Link to this section")

*   [Node-MakeMKV Alpha1 (.tar.gz)](http://blog.dlasley.net/user-files/uploads/node-makemkv-1.1.0-alpha.tar.gz)
*   [Node-MakeMKV Alpha1 (.zip)](http://blog.dlasley.net/user-files/uploads/node-makemkv-1.1.0-alpha.zip)
*   [GitHub](https://github.com/dlasley/node-makemkv/releases/tag/v1.1.0-alpha)

## Installation [∞](#installation "Link to this section")

*   [Install Node.js and CoffeeScript](https://blog.dlasley.net/2014/04/installing-node-js-and-coffeescript/)
*   Edit the `[settings]` section of `server_settings.ini` per the below specifications:
<table style="max-width: 600px; margin-left: auto; margin-right: auto;">
<thead>
<tr>
<th>**Variable**</th>
<th>**Description**</th>
</tr>
</thead>
<tbody>
<tr>
<td>`output_dir`</td>
<td>Root ripping directory. Folders for each rip will be created inside of this directory.</td>
</tr>
<tr>
<td>`listen_port`</td>
<td>Port to listen on, defaults to `1337`</td>
</tr>
<tr>
<td>`makemkvcon_path`</td>
<td>Full path to makemkvcon binary, most likely won’t need to be changed</td>
</tr>
<tr>
<td>`browse_jail`</td>
<td>Root browsing directory.. client hopefully shouldn’t be able to go above this</td>
</tr>
<tr>
<td>`outlier_modifier`</td>
<td>For auto track selection, higher is more restrictive (selected if trackSize &gt;= discSizeUpperQuartile*outlier_modifier)</td>
</tr>
</tbody>
</table>

*   Default MakeMKV selection profile as defined in ~/.MakeMKV/settings.conf will be used for track selections. I am currently working on defining these programmatically.

## Usage [∞](#usage "Link to this section")

*   Run the server – `coffee ./server.coffee` – _Note: you must run the server as a user that has permissions to read from optical media_

*   Navigate to `SERVER_HOSTNAME:LISTEN_PORT` to view the GUI

    <div class="align-center image-align-center">[![node-makemkv-gui-1.png](https://blog.dlasley.net/user-files/plugins/blogtext/api/thumbnail/do.php?id=7fd06b9d290478f843a943b72d2ddf2785489601_542x0_resize_if_larger "node-makemkv-gui-1.png")](https://blog.dlasley.net/user-files/uploads/2014/04/node-makemkv-gui-1.png "node-makemkv-gui-1.png")</div>

*   Click the `Refresh Drives` button to scan available drives for discs

    <div class="align-center image-align-center">[![node-makemkv-refresh-1.png](https://blog.dlasley.net/user-files/plugins/blogtext/api/thumbnail/do.php?id=f7df313e30a09d1426385a7185da352977d1253e_542x0_resize_if_larger "node-makemkv-refresh-1.png")](https://blog.dlasley.net/user-files/uploads/2014/04/node-makemkv-refresh-1.png "node-makemkv-refresh-1.png")</div>

*   Click any of the `Get Info` buttons to get disc level information for a specific drive. Panels with the header title `None` do not have a valid disc in the drive (or some other drive level error)

    <div class="align-center image-align-center">[![node-makemkv-getinfo-1.png](https://blog.dlasley.net/user-files/plugins/blogtext/api/thumbnail/do.php?id=21c7978eedb2eebe6f8e5b028f1b11dbf69aed04_542x0_resize_if_larger "node-makemkv-getinfo-1.png")](https://blog.dlasley.net/user-files/uploads/2014/04/node-makemkv-getinfo-1.png "node-makemkv-getinfo-1.png")</div>

*   Once the disc has been scanned, track information will be displayed in the disc panel. Use the checkboxes in the rip column to select which tracks you would like to rip, and the `Rip Tracks` button to initiate ripping. The `Disc Name` field can be used to define the folder that MakeMKV will rip into for this disc (relative to the `Output Directory` defined earlier)

    <div class="align-center image-align-center">[![node-makemkv-discinfo-panel-1.png](https://blog.dlasley.net/user-files/plugins/blogtext/api/thumbnail/do.php?id=600998bbeb33192dc5387373a48deba7f6448d60_542x0_resize_if_larger "node-makemkv-discinfo-panel-1.png")](https://blog.dlasley.net/user-files/uploads/2014/04/node-makemkv-discinfo-panel-1.png "node-makemkv-discinfo-panel-1.png")</div>

## Repos [∞](#repos "Link to this section")

*   [Mercurial](https://repo.dlasley.net/remote_makemkv/file/0ec3db7cb4ef)
*   [GitHub](https://github.com/dlasley/node-makemkv)
