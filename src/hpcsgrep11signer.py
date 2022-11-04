#
#
import logging

import grpc

import src.server_pb2_grpc as g11grpc
import src.server_pb2 as g11

from pyblake2 import blake2b

from src.signer import Signer

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

        CKM_ECDSA                          = 0x00001041
        mech=g11.Mechanism(Mechanism=CKM_ECDSA)

        request = g11.SignSingleRequest(Mech=mech, PrivKey=sk, Data=hashed_data)

        response = self.stub.SignSingle(request)
        logging.debug(f'Raw signature: {response.Signature}')
        encoded_sig = Signer.b58encode_signature(response.Signature)
        logging.debug(f'Base58-encoded signature: {encoded_sig}')
        return encoded_sig
