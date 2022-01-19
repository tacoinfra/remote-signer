#!/usr/bin/env python3

from flask import Flask, request, Response, json, jsonify
from src.validatesigner import ValidateSigner
from src.ddbchainratchet import DDBChainRatchet
from src.hsmsigner import HsmSigner
from os import path, environ
import logging

logging.basicConfig(filename='./remote-signer.log',
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)

app = Flask(__name__)

# sample config used for testing
config = {
    'hsm_username': 'resigner',
    'hsm_slot': 1,
    'hsm_lib': '/opt/cloudhsm/lib/libcloudhsm_pkcs11.so',
    'node_addr': 'http://node.internal:8732',
    'keys': {
        'tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW': {
            'public_key':
                'p2pk67jx4rEadFpbHdiPhsKxZ4KCoczLWqsEpNarWZ7WQ1SqKMf7JsS',
            'private_handle': 7,
            'public_handle': 9
        }
    }
}

logging.info('Opening keys.json')
if path.isfile('keys.json'):
    logging.info('Found keys.json')
    with open('keys.json', 'r') as myfile:
        json_blob = myfile.read().replace('\n', '')
        logging.info('Parsed keys.json successfully as JSON')
        config = json.loads(json_blob)
        logging.info(f"Config contains: {json.dumps(config, indent=2)}")


@app.route('/keys/<key_hash>', methods=['POST'])
def sign(key_hash):
    response = None
    try:
        data = request.get_json(force=True)
        if key_hash in config['keys']:
            logging.info(f'Found key_hash {key_hash} in config')
            key = config['keys'][key_hash]
            logging.info(f'Attempting to sign {data}')
            cr = DDBChainRatchet(environ['REGION'], environ['DDB_TABLE'])
            hsm = HsmSigner(config)
            rs = ValidateSigner(config, ratchet=cr, subsigner=hsm)
            response = jsonify({
                'signature': rs.sign(key['private_handle'], data)
            })
            logging.info(f'Response is {response}')
        else:
            logging.warning(f"Couldn't find key {key_hash}")
            response = Response('Key not found', status=404)
    except Exception as e:
        data = {'error': str(e)}
        logging.error(f'Exception thrown during request: {str(e)}')
        response = app.response_class(
            response=json.dumps(data),
            status=500,
            mimetype='application/json'
        )
    logging.info(f'Returning flask response {response}')
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
            logging.info(f"Found PK {key['public_key']} for hash {key_hash}")
        else:
            logging.warning(f"Couldn't public key for hash {key_hash}")
            response = Response('Key not found', status=404)
    except Exception as e:
        data = {'error': str(e)}
        logging.error(f'Exception thrown during request: {str(e)}')
        response = app.response_class(
            response=json.dumps(data),
            status=500,
            mimetype='application/json'
        )
    logging.info(f'Returning flask response {response}')
    return response


@app.route('/authorized_keys', methods=['GET'])
def authorized_keys():
    return app.response_class(
        response=json.dumps({}),
        status=200,
        mimetype='application/json'
    )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
