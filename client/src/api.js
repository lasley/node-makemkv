import openSocket from 'socket.io-client';

import {
    SERVER_PORT,
} from './settings.json';

const socket = openSocket(`http://localhost:${SERVER_PORT}`);

function subscribeTo(eventName, callback, sendData) {
    socket.on(eventName, receiveData => callback(receiveData));
    socket.emit(`subscribeTo${eventName}`, sendData);
}

function doAction(actionName, sendData) {
    socket.emit(`do${actionName}`, sendData);
}

// Listen for updates to disc-level information on a drive.
function subscribeToDiscInfo(callback, driveId) {
    subscribeTo('DiscInfo', callback, { driveId });
}

// Listen for updates to any drive-level information.
function subscribeToDriveInfo(callback) {
    subscribeTo('DriveInfo', callback);
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
