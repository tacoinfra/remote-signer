#
#
import logging

import grpc

import src.server_pb2_grpc as g11grpc
import src.server_pb2 as g11

from pyblake2 import blake2b

from src.signer import Signer
import sys

from pytezos_core.encoding import base58_encode

class HPCSGrep11Signer(Signer):
    def __init__(self, config):
        self.config = config
        cert = None
        key = None
        cert = open(config["cert_path"], 'rb').read()
        key = open(config["key_path"], 'rb').read()
        ca_cert = open(config["cacert_path"], 'rb').read()

        credentials = grpc.ssl_channel_credentials(ca_cert, key, cert)
        channel = grpc.secure_channel(config["url"], credentials)
        self.stub=g11grpc.CryptoStub(channel)

    def sign(self, pkh, sigreq):
        sk=bytes.fromhex(self.config['keys'][pkh]['secret_key'])
        hashed_data = blake2b(bytes.fromhex(sigreq.get_payload()), digest_size=32).digest()
        logging.debug(f'Hashed data to sign: {hashed_data}')

        ckm={"3":0x00001041 , "1":0x8001001c}  # CKM_ECDSA et CKM_IBM_ED25519_SHA512
        mech=g11.Mechanism(Mechanism=ckm[pkh[2]])
#        d={"3": hashed_data, "1": bytes.fromhex(sigreq.get_payload()) } 
#        request = g11.SignSingleRequest(Mech=mech, PrivKey=sk, Data=d[pkh[2]])
        request = g11.SignSingleRequest(Mech=mech, PrivKey=sk, Data=hashed_data)

        p={"3": b'p2sig', "1": b'edsig' } 
        response = self.stub.SignSingle(request)
        logging.debug(f'Raw signature: {response.Signature}')
#        encoded_sig = Signer.b58encode_signature(response.Signature)
        encoded_sig = base58_encode(response.Signature, prefix=p[pkh[2]])
        logging.debug(f'Base58-encoded signature: {encoded_sig}')
        return encoded_sig
