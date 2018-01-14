/* Remove MakeMKV server component */

const io = require('socket.io'),
    url = require('url'),
    fs = require('fs'),
    path = require('path'),
    MakeMkv = require('./makemkv.js').MakeMkv,
    settings = require('./settings.json'),
    constants = require('./constants.js');

var udev;
try {
    udev = require('udev');
} catch (ex) {
    console.log('`udev` was not found. Automatic disc recognition disabled.');
}

var http, httpsOptions;
if (settings.SSL.ENABLED) {
    http = require('https');
    httpsOptions = {
        key: settings.SSL.KEY,
        cert: settings.SSL.CERT,
    };
} else {
    http = require('http');
}


const LISTEN_PORT = settings.SERVER_PORT;
const MIME_TYPES = constants.MIME_TYPES;

/*  Holds data and allows for subscriptions to receive updates to that data.

 */
class Subscribable {

    constructor(eventName, initialData) {
        this.name = eventName;
        this.data = initialData ? initialData : {};
        this.clients = new Set();
    }

    subscribe(socketClient) {
        this.clients.add(socketClient);
        socketClient.on('disconnect', () => this.disconnect(socketClient));
        this.emitData(socketClient);
    }

    disconnect(socketClient) {
        this.clients.delete(socketClient);
    }

    broadcastData() {
        this.clients.forEach((client) => this.emitData(client));
    }

    emitData(socketClient) {
        socketClient.emit(this.name, this.data);
    }

    updateBulk(obj, dataObject) {
        for (var key in obj) {
            if (obj.hasOwnProperty(key)) {
                this.update(key, obj[key], true, dataObject);
            }
        }
        this.broadcastData();
    }

    update(key, value, skipBroadcast, dataObject) {
        if (dataObject === undefined) {
            dataObject = this.data;
        }
        if (key.includes('.')) {
            let currentKey = key.split('.', 1),
                futureKey = key.replace(`${currentKey}.`, '');
            dataObject = dataObject[currentKey];
            return this.update(futureKey, value, skipBroadcast, dataObject);
        }
        this.dataObject[key] = value;
        if (!skipBroadcast) {
            this.broadcastData();
        }
    }

}


class MakeMkvServer {

    constructor(port) {

        this.clients = new Set();
        this.discInfo = new Subscribable();
        this.driveInfo = new Subscribable();
        this.makeMkv = new MakeMkv();

        if (udev) {
            // @TODO: This.
            //this.hardwareMonitor = udev.monitor();
            //this.hardwareMonitor.on('change', )
        }

        this.initDevices();
        this.initHttp(port);
        this.initSocketServer(this.http);

    }

    initHttp(port) {

        if (port === undefined) {
            port = LISTEN_PORT;
        }

        let requestListener = (request, response) => {

            let urlParsed = url.parse(request.url, true),
                urlPath = urlParsed.pathname,
                filePath = `./client/build/${urlPath}`;

            request.setEncoding('utf-8');

            fs.exists(filePath, (exists) => {

                if (!exists) {
                    filePath = path.join(__dirname, '/client/build/index.html');
                }

                // Serve index.html if a directory
                if (fs.statSync(filePath).isDirectory()) {
                    filePath += 'index.html';
                }

                // Serve the file
                fs.readFile(filePath, (error, data) => {

                    if (error) {
                        response.statusCode = 500;
                        response.end(`Error getting the file: ${error}.`);
                    } else {
                        const extension = path.parse(filePath).ext;
                        response.setHeader(
                            'Content-type',
                            MIME_TYPES[extension] || 'text/plain'
                        );
                        response.statusCode = 200;
                        response.end(data);
                    }

                });

            });

        };

        if (httpsOptions) {
            this.http = http.createServer(
                httpsOptions, requestListener
            );
        } else {
            this.http = http.createServer(requestListener);
        }

        this.http.listen(port);

    }

    initSocketServer(httpServer) {

        this.socket = io(httpServer);
        this.socket.on(
            'connection',
            (client) => this.initSocketClient(client)
        );

    }

    initSocketClient(client) {

        console.debug('Client connected.');

        this.clients.add(client);

        client.on('disconnect', () => {
            console.debug('Client disconnected.');
            this.clients.delete(client);
        });

        // Subscriptions
        client.on(
            'subscribeToDiscInfo', () => this.discInfo.subscribe(client)
        );
        client.on(
            'subscribeToDriveInfo', () => this.driveInfo.subscribe(client)
        );

        // Actions
        client.on('doDiscInfo', (data) => this.doDiscInfo(data));
        client.on('doRipTrack', (data) => this.doRipTrack(data));

    }

    initDevices() {
        this.makeMkv.scanDiscs(
            (driveInfo) => this.driveInfo.updateBulk(driveInfo)
        );
    }

    doDiscInfo(data) {
        let driveId = data.driveId;
        let callback = (stdErr, discInfo) => {
            this.discInfo[driveId] = {};
            this.discInfo.updateBulk(discInfo, this.discInfo[driveId]);
        };
        this.makeMkv.getDiscInfo(driveId, callback);
    }

    doRipTrack(data) {

        let driveId = data.driveId,
            discName = data.discName,
            trackIds = data.trackIds,
            updateData = {};

        let callback = (trackId, isSuccess, messages) => {
            this.discInfo.update(
                `${driveId}.tracks.${trackId}.ripStatus`,
                isSuccess ? 'success' : 'fail'
            )
        };

        // Generate that object representing the data to update.
        updateData[`${driveId}.isRipping`] = true;
        trackIds.map((trackId) => {
            let trackKey = `${driveId}.tracks.${trackId}.ripStatus`;
            updateData[trackKey] = 'busy';
        });

        this.discInfo.updateBulk(updateData);
        this.makeMkv.ripTracks(
            discName, driveId, trackIds, callback
        )

    }

}


server = new MakeMkvServer();
