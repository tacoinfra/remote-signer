from flask import Flask, request, Response, json, jsonify
from src.remote_signer import RemoteSigner

app = Flask(__name__)


@app.route('/', methods=['POST'])
def sign():
    response = None
    try:
        data = request.get_json(force=True)
        rs = RemoteSigner(data)
        response = jsonify({
            'signature': rs.sign(test_mode=True)
        })
    except Exception as e:
        data = {'error': str(e)}
        response = app.response_class(
            response=json.dumps(data),
            status=500,
            mimetype='application/json'
        )
    return response


@app.route('/', methods=['GET'])
def get_public_key():
    response = None
    try:
        rs = RemoteSigner()
        response = jsonify({
            'public_key': rs.get_signer_pubkey(test_mode=True)
        })
    except Exception as e:
        data = {'error': str(e)}
        response = app.response_class(
            response=json.dumps(data),
            status=500,
            mimetype='application/json'
        )
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
