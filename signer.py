#!/usr/bin/env python3

from flask import Flask, request, Response, json, jsonify
from werkzeug.exceptions import HTTPException
from src.sigreq import SignatureReq
from src.validatesigner import ValidateSigner
from src.ddbchainratchet import DDBChainRatchet
from src.hsmsigner import HsmSigner
from os import path, environ
import logging

DEBUG = environ.get("DEBUG", None)


def logreq(sigreq, msg):
    if sigreq is not None:
        logging.info(f"Request: {sigreq.get_logstr()}:{msg}")


FORMAT = "%(asctime)s %(threadName)s %(message)s"

if DEBUG:
    from rich.logging import RichHandler

    logging.basicConfig(
        level="NOTSET",
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler(show_path=False, level=logging.INFO)],
    )
else:
    logging.basicConfig(
        filename="./remote-signer.log", format=FORMAT, level=logging.INFO
    )

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

if path.isfile("keys.json"):
    with open("keys.json", "r") as myfile:
        json_blob = myfile.read().replace("\n", "")
        config = json.loads(json_blob)
        logging.info(f"Loaded config contains: {json.dumps(config, indent=2)}")

#
# We keep the ChainRatchet, HSM, and ValidateSigner outside sign()
# so that they persist.

cr = DDBChainRatchet(
    environ["REGION"],
    environ["DDB_TABLE"],
    environ.get("BOTO3_ENDPOINT") if DEBUG else None,
)
hsm = HsmSigner(config)
rs = ValidateSigner(config, ratchet=cr, subsigner=hsm)


@app.route("/keys/<key_hash>", methods=["GET", "POST"])
def sign(key_hash):
    response = None
    sigreq = None
    try:
        if key_hash in config["keys"]:
            key = config["keys"][key_hash]
            if request.method == "POST":
                sigreq = SignatureReq(request.get_json(force=True))
                response = jsonify(
                    {"signature": rs.sign(key["private_handle"], sigreq)}
                )
            else:
                response = jsonify({"public_key": key["public_key"]})
        else:
            logging.warning(f"Couldn't find key {key_hash}")
            response = Response("Key not found", status=404)
    except HTTPException as e:
        logging.error(e)
        logreq(sigreq, "Failed")
        raise
    except Exception as e:
        data = {"error": str(e)}
        logging.error(f"Exception thrown during request: {str(e)}")
        response = app.response_class(
            response=json.dumps(data), status=500, mimetype="application/json"
        )
        logreq(sigreq, "Failed")
        return response

    logreq(sigreq, "Success")

    return response


@app.route("/authorized_keys", methods=["GET"])
def authorized_keys():
    return app.response_class(
        response=json.dumps({}), status=200, mimetype="application/json"
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
