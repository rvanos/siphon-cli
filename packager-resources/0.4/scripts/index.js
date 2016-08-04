
var server = require('react-native/local-cli/server/server');
var CONF = require('react-native/local-cli/default.config');

var args = process.argv.splice(process.execArgv.length + 2);

if (args[0] != '--project-path' && typeof args[1] != 'string') {
  console.log('Useage: --project-path <path>');
}

CONF.getProjectRoots = function() {
  return [args[1], __dirname];
};

server({}, CONF)
  .then()
  .catch((err) => {
    console.log(err.message);
  });
