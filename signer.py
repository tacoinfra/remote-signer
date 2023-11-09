#!/usr/bin/env python3

from flask import Flask, request, Response, json, jsonify
from werkzeug.exceptions import HTTPException

from src.sigreq import SignatureReq

from src.chainratchet import MockChainRatchet
from src.ddbchainratchet import DDBChainRatchet
from src.sqlitechainratchet import SQLiteChainRatchet

from src.signer import MockSigner
from src.localsigner import LocalSigner
from src.hpcsgrep11signer import HPCSGrep11Signer
from src.hsmsigner import HsmSigner
from src.validatesigner import ValidateSigner

from os import path
import logging

def logreq(sigreq, msg):
    if sigreq != None:
        logging.info(f"Request: {sigreq.get_logstr()}:{msg}")

logging.basicConfig(filename='./remote-signer.log',
                    format='%(asctime)s %(threadName)s %(message)s',
                    level=logging.DEBUG)

app = Flask(__name__)

#
# The config file (keys.json) has a structure:
#
# config = {
#     'hsm_username': 'resigner',
#     'hsm_slot': 1,
#     'hsm_lib': '/opt/cloudhsm/lib/libcloudhsm_pkcs11.so',
#     'keys': {
#         'tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW': {
#             'public_key':
#                 'p2pk67jx4rEadFpbHdiPhsKxZ4KCoczLWqsEpNarWZ7WQ1SqKMf7JsS',
#             'private_handle': 7,
#             'public_handle': 9
#         }
#     },
#     'policy': {
#         'baking': 1,		# just a boolean
#         'voting': ['pass'],	# a list of permitted votes
#     }
# }

if path.isfile('keys.json'):
    with open('keys.json', 'r') as myfile:
        json_blob = myfile.read().replace('\n', '')
        config = json.loads(json_blob)
        logging.info(f"Loaded config contains: {json.dumps(config, indent=2)}")

#
# We keep the ChainRatchet, HSM, and ValidateSigner outside sign()
# so that they persist.

signers = {
    'local'      : LocalSigner,
    'grep11'      : HPCSGrep11Signer,
    'mockery'    : MockSigner,
    'amazon_hsm' : HsmSigner,
}

if "signer" not in config:
    raise(KeyError('config["signer"] not defined'))
if config["signer"] not in signers:
    raise(KeyError(f'signer: {config["signer"]} not defined'))
ss = signers[config["signer"]](config)

ratchets = {
    'mockery'    : MockChainRatchet,
    'dynamodb'   : DDBChainRatchet,
    'sqlitedb'   : SQLiteChainRatchet,
}

if "chain_ratchet" not in config:
    raise(KeyError('config["chain_ratchet"] not defined'))
if config["chain_ratchet"] not in ratchets:
    raise(KeyError(f'chain_ratchet: {config["chain_ratchet"]} not defined'))
cr = ratchets[config["chain_ratchet"]](config)

rs  = ValidateSigner(config, ratchet=cr, subsigner=ss)

@app.route('/keys/<key_hash>', methods=['GET', 'POST'])
def sign(key_hash):
    response = None
    sigreq = None
    try:
        if key_hash in config['keys']:
            key = config['keys'][key_hash]
            if request.method == 'POST':
                sigreq = SignatureReq(request.get_json(force=True))
                response = jsonify({
                    'signature': rs.sign(key_hash, sigreq)
                })
            else:
                response = jsonify({ 'public_key': key['public_key'] })
        else:
            logging.warning(f"Couldn't find key {key_hash}")
            response = Response('Key not found', status=404)
    except HTTPException as e:
        logging.error(e)
        logreq(sigreq, "Failed")
        raise
    except Exception as e:
        data = {'error': str(e)}
        logging.error(f'Exception thrown during request: {str(e)}')
        response = app.response_class(
            response=json.dumps(data),
            status=500,
            mimetype='application/json'
        )
        logreq(sigreq, "Failed")
        return response

    logreq(sigreq, "Success")

    return response


@app.route('/authorized_keys', methods=['GET'])
def authorized_keys():
    return app.response_class(
        response=json.dumps({}),
        status=200,
        mimetype='application/json'
    )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
