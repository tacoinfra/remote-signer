var request = require('request');

module.exports = function (context, req) {
  context.log('JavaScript HTTP trigger function processed a request.');

  if (req.query.name || (req.body && req.body.name)) {
    request('http://www.google.com', function (error, response, body) {
      if (error) {
        context.res = {
          body: "Error " + (req.query.name || req.body.name)
        };
      } else {
        context.res = {
          body: "Goodbye " + (req.query.name || req.body.name) + body
        };
      }
    });
  } else {
    context.res = {
      status: 400,
      body: "Please pass a name on the query string or in the request body"
    };
  }
  context.done();
};
