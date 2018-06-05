module.exports = function(context, req) {
    context.log('JavaScript HTTP trigger function processed a request.');

    if (req.query.name || (req.body && req.body.name)) {

        const http = require('http');
        
        http.get('http://httpbin.org/get', (resp) => {
            let data = '';
            
            // A chunk of data has been recieved.
            resp.on('data', (chunk) => {
                data += chunk;
            });
            
            // The whole response has been received. Print out the result.
            resp.on('end', () => {
                console.log(JSON.parse(data).explanation);

                // using the express api style
                context.res
                    // set statusCode to 200
                    .status(200)
                    // set a header on the response
                    .set("QuerySet", req.query.name != undefined)
                    // send will automatically call context.done
                    .send(JSON.parse(data));
            });
        }).on("error", (err) => {
            console.log("Error: " + err.message);
        });
    } else {
        // alternate style
        context.res = {
            status: 400,
            body: "Please pass a name on the query string or in the request body"
        };
        context.done();
    }
};
