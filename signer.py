from flask import Flask, request, Response, json, jsonify
from src.remote_signer import RemoteSigner
from os import path

app = Flask(__name__)

# sample config used for testing
config = {
    'hsm_address': 'hsm.internal',
    'hsm_username': 'resigner',
    'hsm_slot': 1,
    'hsm_lib': '/opt/cloudhsm/lib/libcloudhsm_pkcs11.so',
    'rpc_addr': 'node.internal',
    'rpc_port': 8732,
    'keys': {
        'tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW': {
            'public_key': 'p2pk67jx4rEadFpbHdiPhsKxZ4KCoczLWqsEpNarWZ7WQ1SqKMf7JsS',
            'private_handle': 7,
            'public_handle': 9
        }
    }
}

if path.isfile('keys.json'):
    with open('data.txt', 'r') as myfile:
        json_blob = myfile.read().replace('\n', '')
        config = json.loads(json_blob)


@app.route('/keys/<key_hash>', methods=['POST'])
def sign(key_hash):
    response = None
    try:
        data = request.get_json(force=True)
        if key_hash in config['keys']:
            key = config['keys'][key_hash]
            rs = RemoteSigner(config, data)
            response = jsonify({
                'signature': rs.sign(key['private_handle'])
            })
        else:
            response = Response('Key not found', status=404)
    except Exception as e:
        data = {'error': str(e)}
        response = app.response_class(
            response=json.dumps(data),
            status=500,
            mimetype='application/json'
        )
    return response


@app.route('/keys/<key_hash>', methods=['GET'])
def get_public_key(key_hash):
    response = None
    try:
        if key_hash in config['keys']:
            key = config['keys'][key_hash]
            response = jsonify({
                'public_key': key['public_key']
            })
        else:
            response = Response('Key not found', status=404)
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
