module.exports.NEWLINE_CHAR = /((?:[^,"']|"[^"]*"|'[^']*')+)/;
module.exports.ALL_DRIVES = 'ALL';

// makemkv-oss-x.x.x/makemkvgui/inc/lgpl/apdefs.h._AP_ItemAttributeId
module.exports.TRACK_ATTRIBUTES = Object.freeze({
    0: "Unknown",
    1: "Type",
    2: "Name",
    3: "Lng Code",
    4: "Lng Name",
    5: "Codec ID",
    6: "Codec Short",
    7: "Codec Long",
    8: "Chapter Count",
    9: "Duration",
    10: "Disk Size",
    11: "Disk Size Bytes",
    12: "Stream Type Extension",
    13: "Bitrate",
    14: "Audio Channels Cnt",
    15: "Angle Info",
    16: "Source File Name",
    17: "Audio Sample Rate",
    18: "Audio Sample Size",
    19: "Video Size",
    20: "Video Aspect Ratio",
    21: "Video Frame Rate",
    22: "Stream Flags",
    23: "Date Time",
    24: "Original Title ID",
    25: "Segments Count",
    26: "Segments Map",
    27: "Output Filename",
    28: "Metadata Lng Code",
    29: "Metadata Lng Name",
    30: "Tree Info",
    31: "Panel Title",
    32: "Volume Name",
    33: "Order Weight",
    34: "Output Format",
    35: "Output Format Description",
    36: "Max Value",
    37: "Panel Text",
    38: "MKV Flags",
    39: "MKV Flags Text",
    40: "Audio Channel Layout Name",
    41: "Output Codec Short",
    42: "Output Conversion Type",
    43: "Output Audio Sample Rate",
    44: "Output Audio Sample Size",
    45: "Output Audio Channel Count",
    46: "Output Audio Channel Layout Name",
    47: "Output Audio Channel Layout",
    48: "Output Audio Mix Description",
    49: "Comment",
    50: "Offset Sequence ID",
});

// makemkv-oss-x.x.x/makemkvgui/inc/lgpl/apdefs.h._AP_DriveState*
module.exports.DRIVE_STATE_FLAG = Object.freeze({
    0: "Empty and Closed",
    1: "Empty and Open",
    2: "Inserted",
    3: "Loading",
    256: "No Drive",
    257: "Unmounting",
});

// makemkv-oss-x.x.x/makemkvgui/inc/lgpl/apdefs.h._AP_DskFsFlag*
// Note that these are bitwise flags (like Linux permissions)
module.exports.DISC_FS_FLAG = Object.freeze({
    1: "DVD Files Present",
    2: "HD DVD Files Present",
    4: "BluRay Files Present",
    8: "AACS Files Present",
    16: "BDSVM Files Present",
});

module.exports.MIME_TYPES = {
    ".ico": "image/x-icon",
    ".html": "text/html",
    ".js": "application/javascript",
    ".json": "application/json",
    ".css": "text/css",
}
