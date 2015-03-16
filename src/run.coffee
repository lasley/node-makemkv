#!/usr/bin/env coffee
MakeMKVServer = require(__dirname + 'server/server.coffee')
server = new MakeMKVServer()
server.emitter.on('error', server._error)