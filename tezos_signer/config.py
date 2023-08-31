#
# Here we parse our configuration file.
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
#         'baking': 1,          # just a boolean
#         'voting': ['pass'],   # a list of permitted votes
#     }
# }


import logging

from flask import json
from pytezos.crypto.encoding import is_pkh
from pytezos.crypto.key import Key

from tezos_signer import DDBChainRatchet, HsmSigner, LocalSigner, \
                         MockChainRatchet, MockSigner, ValidateSigner

ratchets = {
    "mockery": MockChainRatchet,
    "dynamodb": DDBChainRatchet,
}

signers = {
    "local": LocalSigner,
    "amazon_hsm": HsmSigner,
    "mockery": MockSigner,
}


class TacoinfraConfig:
    def __init__(self, filename=None, conf=None):
        if dict is None and filename is None:
            filename = "keys.json"

        if filename is not None:
            with open("keys.json", "r") as myfile:
                json_blob = myfile.read().replace("\n", "")
                conf = json.loads(json_blob)

        logging.info(f"Loaded config contains: {json.dumps(conf, indent=2)}")

        self.aws_region = conf.get("aws_region")
        self.bind_addr = conf.get("bind_addr", "127.0.0.1")
        self.bind_port = conf.get("bind_port", "5000")
        self.boto3_endpoint = conf.get("boto3_endpoint")
        self.ddb_table = conf.get("ddb_table")
        self.hsm_username = conf.get("hsm_username")
        self.hsm_slot = int(conf.get("hsm_slot", "0"))
        self.hsm_lib = conf.get("hsm_lib")
        self.policy = conf.get("policy")

        if "chain_ratchet" not in conf:
            raise (KeyError("config.chain_ratchet not defined"))
        if conf["chain_ratchet"] not in ratchets:
            raise (KeyError(f'ratchet: {conf["chain_ratchet"]} not found'))
        cr = ratchets[conf["chain_ratchet"]](self)

        self.keys = {}
        for k in conf["keys"]:
            l = k.split(":")
            key = {}
            if isinstance(conf["keys"], dict):
                key = conf["keys"].get(k)
            if len(l) > 1:
                key["signer"] = l[1]
                key["signer_args"] = l[2:]
            if is_pkh(l[0]):
                key["pkh"] = l[0]
            else:
                ptkey = Key.from_encoded_key(l[0])
                k = ptkey.public_key_hash()
                key["pkh"] = k
                key["public_key"] = ptkey.public_key()
                try:
                    key["private_key"] = ptkey.secret_key()
                    if "signer" not in key:
                        key["signer"] = "local"
                except ValueError:
                    pass

            if "signer" not in key:
                raise (Exception(f"key {k} does not define a signer"))
            if key["signer"] not in signers:
                raise (KeyError(f'signer: {key["signer"]} not defined'))
            ss = signers[key["signer"]](self, key)

            key["signer"] = ValidateSigner(self, key, ratchet=cr, subsigner=ss)

            self.keys[k] = key

    def get_addr(self):
        return self.bind_addr

    def get_aws_region(self):
        return self.aws_region

    def get_boto3_endpoint(self):
        return self.boto3_endpoint

    def get_ddb_table(self):
        return self.ddb_table

    def get_hsm_lib(self):
        return self.hsm_lib

    def get_hsm_slot(self):
        return self.hsm_slot

    def get_hsm_username(self):
        return self.hsm_username

    def get_key(self, pkh):
        return self.keys.get(pkh)

    def get_port(self):
        return self.bind_port

    def get_policy(self):
        return self.policy
