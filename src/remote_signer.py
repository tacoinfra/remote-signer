import struct
import string
from src.tezos_rpc_client import TezosRPCClient
from pyhsm.hsmclient import HsmClient, HsmAttribute
from pyhsm.hsmenums import HsmMech
from pyhsm.convert import hex_to_bytes, bytes_to_hex
from os import environ
import bitcoin
from pyblake2 import blake2b
import logging


class RemoteSigner:
    BLOCK_PREAMBLE = 1
    ENDORSEMENT_PREAMBLE = 2
    LEVEL_THRESHOLD: int = 16
    TEST_SIGNATURE = 'p2sigfqcE4b3NZwfmcoePgdFCvDgvUNa6DBp9h7SZ7wUE92cG3hQC76gfvistHBkFidj1Ymsi1ZcrNHrpEjPXQoQybAv6rRxke'
    TEST_KEY = 'p2pk67jx4rEadFpbHdiPhsKxZ4KCoczLWqsEpNarWZ7WQ1SqKMf7JsS'
    P256_SIGNATURE = struct.unpack('>L', b'\x36\xF0\x2C\x34')[0]  # results in p2sig prefix when encoded with base58
    P256_PUBLIC_KEY = struct.unpack('>L', b'\x03\xB2\x8B\x7F')[0]  # results in p2pk prefix when encoded with base58

    def __init__(self, config, payload='', rpc_stub=None):
        self.keys = config['keys']
        self.payload = payload
        logging.info('Verifying payload')
        self.data = self.decode_block(self.payload)
        logging.info('Payload {} is valid'.format(self.data))
        self.rpc_stub = rpc_stub
        self.hsm_slot = config['hsm_slot']
        hsm_user = config['hsm_username']
        logging.info('HSM user is {}'.format(config['hsm_username']))
        logging.info('Attempting to read env var HSM_PASSWORD')
        hsm_password = environ['HSM_PASSWORD']
        self.hsm_pin = '{}:{}'.format(hsm_user, hsm_password)
        self.hsm_libfile = config['hsm_lib']
        logging.info('HSM lib is {}'.format(config['hsm_lib']))
        self.rpc_addr = config['rpc_addr']
        self.rpc_port = config['rpc_port']

    @staticmethod
    def valid_block_format(blockdata):
        return all(c in string.hexdigits for c in blockdata)

    @staticmethod
    def decode_block(data):
        return RemoteSigner.valid_block_format(data) and bytes.fromhex(data)

    def is_block(self):
        return self.data and list(self.data)[0] == self.BLOCK_PREAMBLE

    def is_endorsement(self):
        return list(self.data)[0] == self.ENDORSEMENT_PREAMBLE

    def get_block_level(self):
        str = self.data[1:5]
        level = struct.unpack('>L', str)[0]
        logging.info('Block level is {}'.format(level))
        return level

    def is_within_level_threshold(self):
        rpc = self.rpc_stub or TezosRPCClient(node_url=self.rpc_addr, node_port=self.rpc_port)
        current_level = rpc.get_current_level()
        payload_level = self.get_block_level()
        within_threshold = current_level < payload_level <= current_level + self.LEVEL_THRESHOLD
        if within_threshold:
            logging.info('Level {} is within threshold of current level {}'.format(payload_level, current_level))
        else:
            logging.error('Level {} is not within threshold of current level {}'.format(payload_level, current_level))
        return within_threshold

    @staticmethod
    def wrap(data, digest_size, magicbyte):
        return bitcoin.bin_to_b58check(blake2b(data, digest_size=digest_size).digest(), magicbyte=magicbyte)

    @staticmethod
    def wrap_signature(sig):
        return RemoteSigner.wrap(sig.encode('utf-8'), 64, RemoteSigner.P256_SIGNATURE)

    @staticmethod
    def wrap_public_key(key):
        return RemoteSigner.wrap(key.encode('utf-8'), 33, RemoteSigner.P256_PUBLIC_KEY)

    def get_signer_pubkey(self, handle, test_mode=False):
        if test_mode:
            return self.TEST_KEY
        else:
            pubkey = ''
            logging.info('Retrieving public key from key handle {}'.format(handle))
            with HsmClient(slot=1, pin=self.hsm_pin, pkcs11_lib=self.hsm_libfile) as c:
                logging.info('Successfully logged into HSM client')
                pubkey = RemoteSigner.wrap_public_key(c.get_attribute_value(handle, HsmAttribute.EC_POINT))
                logging.info('Successfully retrieved public key {}'.format(pubkey))
            return pubkey

    def validate_keys(self):
        logging.info('Validating all keys in config')
        for key_hash, val in self.keys.items():
            handle = val['public_handle']
            hsm_pubkey = self.get_signer_pubkey(handle)
            wrapped_key = self.wrap_public_key(hsm_pubkey)
            if wrapped_key != val['public_key']:
                raise Exception('Key handle {} does not match pubkey {}'.format(handle, val['public_key']))

    def sign(self, handle, test_mode=False):
        signed_data = ''
        logging.info('About to sign {} with key handle {}'.format(self.data, handle))
        data_to_sign = self.payload[2:]  # strip preamble before signing
        logging.info('Stripped preamble: {}'.format(data_to_sign))
        if self.valid_block_format(data_to_sign):
            logging.info('Block format is valid')
            if self.is_block() or self.is_endorsement():
                logging.info('Preamble is valid')
                if self.is_within_level_threshold():
                    logging.info('Block level is valid')
                    if test_mode:
                        return self.TEST_SIGNATURE
                    else:
                        logging.info('About to sign with HSM client. Slot = {}, lib = {}, handle = {}'.format(self.hsm_slot, self.hsm_libfile, handle))
                        with HsmClient(slot=self.hsm_slot, pin=self.hsm_pin, pkcs11_lib=self.hsm_libfile) as c:
                            sig = c.sign(handle=handle, data=hex_to_bytes(data_to_sign), mechanism=HsmMech.ECDSA_SHA256)
                            decoded_sig = bytes_to_hex(sig)
                            logging.info('Raw signature: {}'.format(decoded_sig))
                            signed_data = RemoteSigner.wrap_signature(decoded_sig)
                            logging.info('Wrapped signature: {}'.format(signed_data))
                else:
                    logging.error('Invalid level')
                    raise Exception('Invalid level')
            else:
                logging.error('Invalid preamble')
                raise Exception('Invalid preamble')
        else:
            logging.error('Invalid payload')
            raise Exception('Invalid payload')
        return signed_data
