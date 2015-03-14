# Karma configuration
# Generated on Thu Feb 19 2015 18:45:36 GMT-0800 (PST)

module.exports = (config) ->
  config.set

    # base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: ''


    # frameworks to use
    # available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: [ 'qunit' ]


    # list of files / patterns to load in the browser
    files: [
        ##  Assets
        './libs/**',
        
        ##  App, Models, Controllers, Views, Others (in that order)
        '../**/client/*.coffee',
        '../**/client/*.js',
        '../**/client/models/*.coffee',
        '../**/client/controllers/*.coffee',
        #'../**/client/views/**',
        
        ##  Testing Assets
        './ember-qunit-builds/ember-qunit.js',
        './ember_test_bootstrap.js',
        
        ##  Tests
        '../**/tests/test_*.js',
        '../**/test_*.coffee',
    ]


    # list of files to exclude
    exclude: [
        #'../**/assets/core_ui/theme/**',
    ]


    # preprocess matching files before serving them to the browser
    # available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
        '../**/*.coffee': [ 'coffee' ],
        #'../**/*.handlebars': [ 'ember' ],
    }


    # test results reporter to use
    # possible values: 'dots', 'progress'
    # available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: [ 'progress', 'junit', ]
    
    #bambooReporter:{
    #    filename: 'test-reports/unit.mocha.json'
    #},
    
    junitReporter: {
        outputFile: '../test-reports/unit-js.xml',
        suite: ''
    }

    # web server port
    port: 9876


    # enable / disable colors in the output (reporters and logs)
    colors: false


    # level of logging
    # possible values:
    # - config.LOG_DISABLE
    # - config.LOG_ERROR
    # - config.LOG_WARN
    # - config.LOG_INFO
    # - config.LOG_DEBUG
    logLevel: config.LOG_INFO


    # enable / disable watching file and executing tests whenever any file changes
    autoWatch: false


    # start these browsers
    # available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: [ 'PhantomJS' ]


    # Continuous Integration mode
    # if true, Karma captures browsers, runs the tests and exits
    singleRun: true
    
    plugins: [
        'karma-qunit',
        'karma-ember-preprocessor',
        'karma-phantomjs-launcher',
        'karma-coffee-preprocessor',
        'karma-junit-reporter',
    ],





