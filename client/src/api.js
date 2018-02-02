import io from 'socket.io-client';

import {
    SERVER_PORT,
} from './settings.json';

const socket = io();

function waitForSocket(callback, ...args) {
    console.debug('Waiting for socket to become available.');
    if (socket.id) {
        console.debug('Socket is available.');
        callback(...args);
    } else {
        setTimeout(waitForSocket, 1000, callback, ...args);
    }
}

function subscribeTo(eventName, callback, context, sendData) {
    console.debug(`Subscribing to "${eventName}".`);
    waitForSocket(() => {
        socket.on(
            eventName,
            context ? callback.bind(context) : callback
        );
        socket.emit(`subscribeTo${eventName}`, sendData);
    });
}

function doAction(actionName, sendData) {
    console.debug(`Performing action "${actionName}".`);
    waitForSocket(() => {
        socket.emit(`do${actionName}`, sendData);
    });
}

// Listen for updates to disc-level information on a drive.
function subscribeToDiscInfo(callback, context, driveId) {
    subscribeTo('DiscInfo', callback, context, { driveId });
}

// Listen for updates to any drive-level information.
function subscribeToDriveInfo(callback, context) {
    subscribeTo('DriveInfo', callback, context);
}

// Start ripping tracks on a drive.
function actionRipTracks(discName, driveId, trackIds) {
    doAction('RipTracks', { discName, driveId, trackIds });
}

// Command server to get disc information for a drive.
function actionDiscInfo(driveId) {
    doAction('DiscInfo', { driveId });
}

export {
    actionDiscInfo,
    actionRipTracks,
    subscribeToDiscInfo,
    subscribeToDriveInfo,
};
