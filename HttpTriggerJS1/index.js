module.exports = function (context, req) {
  context.log('JavaScript HTTP trigger function processed a request.');

  if (req.query.name || (req.body && req.body.name)) {
    var request = require('request');
    request('http://www.google.com', function (error, response, body) {
      context.res = {
        // status: 200, /* Defaults to 200 */
        body: "Goodbye " + (req.query.name || req.body.name) + body
      };
    });

    }
  else {
    context.res = {
      status: 400,
      body: "Please pass a name on the query string or in the request body"
    };
  }
  context.done();
};
