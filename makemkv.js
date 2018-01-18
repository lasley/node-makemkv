/* Interact with MakeMKV CLI */

const fs = require('fs'),
    os = require('os'),
    EventEmitter = require('events').EventEmitter,
    parseCsv = require('csv-parse/lib/sync'),
    path = require('path'),
    spawn = require('child_process').spawn,
    constants = require('./constants.js'),
    settings = require('./settings.json');

const ALL_DRIVES = constants.ALL_DRIVES,
    DRIVE_STATE_FLAG = constants.DRIVE_STATE_FLAG,
    TRACK_ATTRIBUTES = constants.TRACK_ATTRIBUTES;

const CONVERSION_PROFILE = settings.CONVERSION_PROFILE,
    MAKEMKVCON_PATH = settings.MAKEMKVCON_PATH,
    CACHE_SIZE = settings.CACHE_SIZE,
    OUTLIER_MODIFIER = settings.OUTLIER_MODIFIER,
    SELECTION_PROFILE = settings.SELECTION_PROFILE,
    SERVER_PORT = settings.SERVER_PORT,
    PERMISSIONS = settings.PERMISSIONS,
    OUTPUT_DIR = settings.OUTPUT_DIR;


class MakeMkv {

    constructor() {

        this.emitter = new EventEmitter();
        this.busyDevices = new Set();
        this.ripQueue = {};
        this.driveMap = {};

        this.ATTRIBUTE_TYPE_MESSAGE = 'MSG';
        this.ATTRIBUTE_TYPE_DRIVE_INFO = 'DRV';
        this.ATTRIBUTE_TYPE_TRACK_COUNT = 'TCOUNT';
        this.ATTRIBUTE_TYPE_DISC_INFO = 'CINFO';
        this.ATTRIBUTE_TYPE_TRACK_INFO = 'TINFO';
        this.ATTRIBUTE_TYPE_STREAM_INFO = 'SINFO';

        // @TODO: These should probably go in constants.js
        this.HEADERS_MESSAGE = [
            'code',
            'flags',
            'parameterCount',
            'messageRaw',
            'messageFormat',
        ];
        this.HEADERS_DRIVE_INFO = [
            'driveIndex',
            'driveState',
            'isEnabled',
            'mediaFlags',
            'driveName',
            'discName',
            'driveId',
        ];
        this.HEADERS_DISC_INFO_TCOUNT = [
            'trackCount',
        ];
        this.HEADERS_DISC_INFO_MAIN = [
            'attributeId',
            'constantId',
            'attributeValue',
        ];
        this.HEADERS_DISC_INFO_TRACK = [
            'trackIndex',
            'attributeId',
            'constantId',
            'attributeValue',
        ];
        this.HEADERS_DISC_INFO_STREAM = [
            'trackIndex',
            'streamIndex',
            'attributeId',
            'constantId',
            'attributeValue',
        ];

    }

    /*  Choose the tracks that should be automatically selected.

        Determine the tracks to select by calculating the upper quartile of
        sizes, then using the OUTLIER_MODIFIER to increase the bounds
        slightly::

            TrackCount * 0.75 * (OUTLIER_MODIFIER / 100)

        @param  {DiscInfo}  discInfo    The information returned from MakeMKV.
        @param  {function}  callback    Method to run on success. Receives an
            object keyed by the Drive ID that contains an object representing
            the high level information for that drive. Properties are:

                * driveIndex {int}
                * driveState {str}
                * isEnabled {int} Supposedly set to ``1`` if drive is accessible.
                  This does not seem to be the case in actuality.
                * mediaFlags {int} Media file system flags.
                * driveName {str} Canonical name of the drive.
                * discName {str} Canonical name of the disc in the drive.
                * driveId {str} The ID of the device as reported by the OS.
     */
    chooseTracks(discInfo, callback) {

    }

    /*  Get information on a disc in a drive and pass to callback.

        @param  {str}   driveId     The identifier of the drive as reported by
            the host OS.
        @param  {function}  callback    Method to be called when done. It will
            receive the following parameters:

                * stdErr {array}: an array of strings indicating any error responses
                  from MakeMKV.
                * discInfo {obj}: an object representing the disc information.
     */
    getDiscInfo(driveId, callback) {

        if (this.busyDevices.has(driveId)) {
            this._waitAvailable(
                driveId, this.getDiscInfo, driveId, callback
            );
        }

        this.busyDevices.add(driveId);

        let newCallback = (exitCode, stdErr, stdOut) => {
            this._parseDiscInfo(exitCode, stdErr, stdOut, callback);
        };

        let command = ['--noscan', 'info', `dev:${driveId}`];
        this._spawnMakemkv(driveId, command, newCallback);

    }

    /*  Scan all drives for the high level disc information.

        @TODO: The cyclomatic complexity is TOO HIGH!
     */
    scanDiscs(callback) {

        if (this.busyDevices.has(ALL_DRIVES)) {
            this._waitAvailable(
                ALL_DRIVES, this.scanDiscs, callback
            );
        }

        this.busyDevices.add(ALL_DRIVES);

        let newCallback = (exitCode, stdErr, stdOut) => {

            this.busyDevices.delete(ALL_DRIVES);

            let discData = {},
                parsedOutput = parseCsv(
                    stdOut.join(os.EOL),
                    {relax_column_count: true}
                );

            parsedOutput.map((dataRow) => {

                dataRow = this._parseOutputRow(dataRow);

                if (
                    !dataRow
                    || dataRow.attributeType !== this.ATTRIBUTE_TYPE_DRIVE_INFO
                    || !dataRow.driveId
                ) {
                    return;
                }

                // Assign the flags to string representations
                dataRow.driveState = DRIVE_STATE_FLAG[dataRow.driveState];

                // @TODO: Bitwise determination of the disc filesystem flags.

                // Add the processed row into the data.
                discData[dataRow.driveId] = dataRow;

            });

            callback(discData);

        };

        this._spawnMakemkv(ALL_DRIVES, ['info', 'disc:9999'], newCallback);

    }

    /*  Queue manager for track ripping.

        @param  {str}   saveDirectory   Folder to save the files to, relative to
            the save directory that is configured in settings (`OUTPUT_DIR`).
        @param  {str}   driveId     The ID of the device to rip from.
        @param  {array} trackIds    An array of integers defining the tracks to
            be ripped.
        @param  {function}  callback    Callback to run when each track is done.
            It will receive:
             * An integer as the first argument to indicate the Track ID.
             * A boolean as the second argument to indicate whether the rip was
               a success.
             * A string as the third argument to provide any messages
               from MakeMKV.
     */
    ripTracks(saveDirectory, driveId, trackIds, callback) {

        if (this.ripQueue.driveId === undefined) {
            this.ripQueue.driveId = new Set(trackIds);
        } else if (trackIds) {
            trackIds.map((trackId) => this.ripQueue.driveId.add(trackId));
        }

        if (!this.ripQueue.driveId.length) {
            // @TODO: What to do here?
            return;
        }

        let newCallback = (trackId, ripSuccess, messages) => {
            callback(trackId, ripSuccess, messages);
            this.ripTracks(saveDirectory, driveId, false, callback);
        };

        this.ripTrack(
            saveDirectory, driveId, this.ripQueue.driveId.pop(), newCallback
        );

    }

    /*  Rip one track and return the result to a callback.

     */
    ripTrack(saveDirectory, driveId, trackId, callback) {

        if (this.busyDevices.has(driveId)) {
            this._waitAvailable(
                driveId, this.ripTrack, saveDirectory, driveId, trackId, callback
            );
        }

        this.busyDevices.add(driveId);

        saveDirectory = path.join(OUTPUT_DIR, saveDirectory);
        let command = [
            '--noscan', 'mkv', `--cache=${CACHE_SIZE}`,
            `--profile=${CONVERSION_PROFILE}`,
            `dev:${driveId}`, trackId, saveDirectory,
        ];

        let newCallback = (exitCode, stdErr, stdOut) => {
            this.busyDevices.delete(driveId);
            let strOutput = stdOut.join('\n'),
                isSuccess = !exitCode && strOutput.indexOf('1 titles saved.') !== -1;
            callback(trackId, isSuccess, strOutput);
        };

        this._spawn(command, newCallback);

    }

    // Return a camelCase version of a Human String.
    _camelize(humanString) {
        if(!humanString) {
            return '';
        }
        return humanString.replace(
            /(?:^\w|[A-Z]|\b\w)/g, (letter, index) => {
                return index == 0 ? letter.toLowerCase() : letter.toUpperCase();
            })
            .replace(/\s+/g, '');
    }

    /*  Parse disc level information that is returned from MakeMKV.

        The output lines appear in a certain order::

            TCOUNT (track count)
            CINFO (Disc information)
            ...
            TINFO (Track 0 information)
            ...
            SINFO (Track 0, Stream 0 information)
            ...
            SINFO (Track 0, Stream 1 information)
            ...
            TINFO (Track 1 information)
            ...
            SINFO (Track 1, Stream 0 information)
            ... repeating ...

        @param  {int}   exitCode    MakeMKV exit code
        @param  {array} stdErr  Array of lines representing the error stream.
        @param  {array} stdOut  Array of lines representing the output stream.
        @param  {function}  callback    Method to be called when done. It will
            receive the following parameters:

                * stdErr {array}: an array of strings indicating any error responses
                  from MakeMKV.
                * discInfo {obj}: an object representing the disc information.

     */
    _parseDiscInfo(exitCode, stdErr, stdOut, callback) {

        let discInfo = {tracks:[]},
            attributeName = false,
            parsedOutput = parseCsv(
                stdOut.join(os.EOL),
                {relax_column_count: true}
            );

        parsedOutput.map((dataRow) => {

            dataRow = this._parseOutputRow(dataRow);

            switch(dataRow.attributeType) {

                case this.ATTRIBUTE_TYPE_DISC_INFO:
                    attributeName = this._getAttribute(dataRow.attributeId);
                    discInfo[attributeName] = dataRow.attributeValue;
                    break;

                case this.ATTRIBUTE_TYPE_TRACK_INFO:
                    attributeName = this._getAttribute(dataRow.attributeId);
                    discInfo.tracks[dataRow.trackIndex] = this._injectValue(
                        discInfo.tracks[dataRow.trackIndex],
                        attributeName,
                        dataRow.attributeValue
                    );
                    break;

                case this.ATTRIBUTE_TYPE_STREAM_INFO:
                    // Note that this will fail if the track hasn't come first.
                    // This should never happen, however.

                    let trackInfo = discInfo.tracks[dataRow.trackIndex];
                    attributeName = this._getAttribute(dataRow.attributeId);

                    if (trackInfo.streams === undefined) {
                        trackInfo.streams = [];
                    }

                    trackInfo.streams[dataRow.streamIndex] = this._injectValue(
                        trackInfo.streams[dataRow.streamIndex],
                        attributeName,
                        dataRow.attributeValue
                    );
                    break;

            }

        });

        console.log('Parsed disc info.');
        console.debug(discInfo);
        callback(stdErr, discInfo);

    }

    // Add a value into obj. If obj is undefined, an empty object will be created.
    _injectValue(obj, key, value) {
        if (obj === undefined) {
            obj = {};
        }
        obj[key] = value;
        return obj;
    }

    // Get an attribute variable name by its ID.
    _getAttribute(attributeId) {
        return this._camelize(TRACK_ATTRIBUTES[attributeId]);
    }

    /*  Parse one row of data and return the proper object.

        @param  {array} An array of data.
        @returns {object} An object with dynamic keys as defined by their
            class constant (the variable sent to ``parseData``). The type
            of attribute (``SINFO``, ``TCOUNT``, etc.) will also be added
            as the ``attributeType`` property.
     */
    _parseOutputRow(dataRow) {

        let [attrType, attrFlag] = dataRow[0].split(':');

        // Zip the keys and values into an obj and add the attribute type.
        let parseData = (keys) => {
            dataRow[0] = attrFlag;
            let data = {attributeType: attrType};
            keys.forEach((key, idx) => data[key] = dataRow[idx]);
            return data;
        };

        switch(attrType) {

            case this.ATTRIBUTE_TYPE_MESSAGE:
                return parseData(this.HEADERS_MESSAGE);

            case this.ATTRIBUTE_TYPE_DRIVE_INFO:
                return parseData(this.HEADERS_DRIVE_INFO);

            case this.ATTRIBUTE_TYPE_TRACK_COUNT:
                return parseData(this.HEADERS_DISC_INFO_TCOUNT);

            case this.ATTRIBUTE_TYPE_DISC_INFO:
                return parseData(this.HEADERS_DISC_INFO_MAIN);

            case this.ATTRIBUTE_TYPE_TRACK_INFO:
                return parseData(this.HEADERS_DISC_INFO_TRACK);

            case this.ATTRIBUTE_TYPE_STREAM_INFO:
                return parseData(this.HEADERS_DISC_INFO_STREAM);

            default:
                return false;

        }

    }

    /*  Spawn MakeMKV with args and send the streams to a callback when done.

        @param  {str}   driveId The Identifier of the drive that is being
            accessed. This is used to ensure that two processes do not access
            the same drive at the same time, which makes the drive create
            funny clicky noises so it's probably not good.
        @param  {list}  args    List of string arguments to pass to the binary.
        @param  {function}  callback    The method to call when done. It will
            receive the exit code as the first argument, stdErr as the second
            argument, and stdOut as the third. ``(exitCode, stdErr, stdOut)``
     */
    _spawnMakemkv(driveId, args, callback) {
        let command = ['-r'],
            newCallback = (...args) => {
                this.busyDevices.delete(driveId);
                callback(...args);
            };
        command = command.concat(args);
        this.busyDevices.add(driveId);
        this._spawn(command, MAKEMKVCON_PATH, newCallback);
    }

    /*  Spawn a binary with args and send the streams to a callback when done.

        @param  {list}  args    List of string arguments to pass to the binary.
        @param  {str}   binaryPath  The path to the binary to call. Defaults
            to the ``MAKEMKVCON_PATH`` defined in the settings.
        @param  {function}  callback    The method to call when done. It will
            receive the exit code as the first argument, stdErr as the second
            argument, and stdOut as the third. ``(exitCode, stdErr, stdOut)``
     */
    _spawn(args, binaryPath, callback) {

        console.log(`Spawning "${binaryPath}" with args: "${args}"`);

        let process = spawn(binaryPath, args);

        if (callback === undefined) {
            return;
        }

        let stdErr = [],
            stdOut = [];

        process.stdout.setEncoding('utf-8');
        process.stderr.setEncoding('utf-8');

        process.stdout.on(
            'data', (data) => { stdOut.push(...data.split(os.EOL)) }
        );
        process.stderr.on(
            'data', (data) => { stdErr.push(...data.split(os.EOL)) }
        );
        process.on('exit', (code) => {
            console.debug(`MakeMKV exited with code ${code}.`);
            callback(code, stdErr, stdOut);
        });

    }

    /*  Waits for drive to become available before performing the callback.

        @param  {str}   ID of the drive to wait for. Pass in the
            ``ALL_DRIVES`` constant in order to wait for all drives
            to become available.
        @param  {function}  Method to call when the defined drive is
            available.
     */
    _waitAvailable(driveId, callback, ...args) {
        let devices = this.busyDevices;
        let isAvailable = () => {
            if (driveId !== ALL_DRIVES) {
                return devices.has(driveId) && !devices.has(ALL_DRIVES);
            } else {
                return devices.length === 0;
            }
        };
        let timer = () => {
            if (isAvailable()) {
                return callback(...args);
            } else {
                return this._waitAvailable(driveId, callback, ...args);
            }
        };
        console.debug(`Waiting for ${driveId} to become available.`);
        setTimeout(timer, 1000);
    }

}


exports.MakeMkv = MakeMkv;
