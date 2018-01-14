// root@f863c022c6ff:/opt/node-makemkv# makemkvcon -r info

let makemkvconInfo = `MSG:1005,0,1,"MakeMKV v1.10.8 linux(x64-release) started","%1 started","MakeMKV v1.10.8 linux(x64-release)"
DRV:0,0,999,0,"BD-ROM HL-DT-ST BDDVDRW UH12NS30 1.03","","/dev/sr4"
DRV:1,0,999,0,"BD-ROM HL-DT-ST BDDVDRW CH10LS28 1.00","","/dev/sr3"
DRV:2,0,999,0,"BD-ROM HL-DT-ST BDDVDRW UH12LS29 1.00","","/dev/sr2"
DRV:3,0,999,0,"BD-ROM HL-DT-ST BDDVDRW CH10LS28 1.00","","/dev/sr1"
DRV:4,2,999,12,"BD-ROM HL-DT-ST BDDVDRW CH10LS28 1.00","THE_UNIVERSE_3D","/dev/sr0"
DRV:5,256,999,0,"","",""
DRV:6,256,999,0,"","",""
DRV:7,256,999,0,"","",""
DRV:8,256,999,0,"","",""
DRV:9,256,999,0,"","",""
DRV:10,256,999,0,"","",""
DRV:11,256,999,0,"","",""
DRV:12,256,999,0,"","",""
DRV:13,256,999,0,"","",""
DRV:14,256,999,0,"","",""
DRV:15,256,999,0,"","",""
Use: makemkvcon [switches] Command [Parameters]

Commands:
  info <source>
      prints info about disc
  mkv <source> <title id> <destination folder>
      saves a single title to mkv file
  stream <source>
      starts streaming server
  backup <source> <destination folder>
      backs up disc to a hard drive

Source specification:
  iso:<FileName>    - open iso image <FileName>
  file:<FolderName> - open files in folder <FolderName>
  disc:<DiscId>     - open disc with id <DiscId> (see list Command)
  dev:<DeviceName>  - open disc with OS device name <DeviceName>

Switches:
  -r --robot        - turn on "robot" mode, see http://www.makemkv.com/developers
`;
