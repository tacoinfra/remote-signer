import struct
import string
from src.tezos_rpc_client import TezosRPCClient
from pyhsm.hsmclient import HsmClient, HsmAttribute
from pyhsm.hsmenums import HsmMech
from os import environ
import bitcoin
from pyblake2 import blake2b


class RemoteSigner:
    BLOCK_PREAMBLE = 1
    ENDORSEMENT_PREAMBLE = 2
    LEVEL_THRESHOLD: int = 16
    TEST_SIGNATURE = 'p2sigfqcE4b3NZwfmcoePgdFCvDgvUNa6DBp9h7SZ7wUE92cG3hQC76gfvistHBkFidj1Ymsi1ZcrNHrpEjPXQoQybAv6rRxke'
    TEST_KEY = 'p2pkDeaFc7jVTsjuA1ENABigmU1rGBkx9AJoWLpdpnyMHctQhyyQf6W'
    P256_SIGNATURE = struct.unpack('>L', b'\x36\xF0\x2C\x34')[0]  # results in p2sig prefix when encoded with base58
    P256_PUBLIC_KEY = struct.unpack('>L', b'\x03\xB2\x8B\x7F')[0]  # results in p2pk prefix when encoded with base58

    def __init__(self, payload='', rpc_stub=None):
        self.payload = payload
        self.data = self.decode_block(self.payload)
        self.rpc_stub = rpc_stub
        self.hsm_slot = int(environ['HSM_SLOT'])
        self.hsm_priv_key_handle = int(environ['HSM_PRIV_KEY_HANDLE'])
        self.hsm_pub_key_handle = int(environ['HSM_PUB_KEY_HANDLE'])
        hsm_user = environ['HSM_USER']
        hsm_password = environ['HSM_PASSWORD']
        self.hsm_pin = '{}:{}'.format(hsm_user, hsm_password)
        self.hsm_libfile = environ['HSM_LIBFILE']
        self.rpc_addr = environ['RPC_ADDR']
        self.rpc_port = environ['RPC_PORT']

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
        return struct.unpack('>L', str)[0]

    def is_within_level_threshold(self):
        rpc = self.rpc_stub or TezosRPCClient(node_url=self.rpc_addr, node_port=self.rpc_port)
        current_level = rpc.get_current_level()
        payload_level = self.get_block_level()
        return current_level < payload_level <= current_level + self.LEVEL_THRESHOLD

    @staticmethod
    def wrap(data, digest_size, magicbyte):
        return bitcoin.bin_to_b58check(blake2b(data, digest_size=digest_size).digest(), magicbyte=magicbyte)

    @staticmethod
    def wrap_signature(sig):
        return RemoteSigner.wrap(sig.encode('utf-8'), 64, RemoteSigner.P256_SIGNATURE)

    @staticmethod
    def wrap_public_key(key):
        return RemoteSigner.wrap(key.encode('utf-8'), 33, RemoteSigner.P256_PUBLIC_KEY)

    def get_signer_pubkey(self, test_mode=False):
        if test_mode:
            return self.TEST_KEY
        else:
            pubkey = ''
            with HsmClient(slot=1, pin=self.hsm_pin, pkcs11_lib=self.hsm_libfile) as c:
                pubkey = RemoteSigner.wrap_public_key(c.get_attribute_value(self.hsm_pub_key_handle, HsmAttribute.EC_POINT))
            return pubkey

    def sign(self, test_mode=False):
        signed_data = ''
        data_to_sign = self.payload[2:]  # strip preamble before signing
        if self.valid_block_format(data_to_sign):
            if self.is_block() or self.is_endorsement():
                if self.is_within_level_threshold():
                    if test_mode:
                        return self.TEST_SIGNATURE
                    else:
                        with HsmClient(slot=self.hsm_slot, pin=self.hsm_pin, pkcs11_lib=self.hsm_libfile) as c:
                            sig = c.sign(handle=self.hsm_priv_key_handle, data=data_to_sign, mechanism=HsmMech.ECDSA_SHA256)
                            signed_data = RemoteSigner.wrap_signature(sig)
                else:
                    raise Exception('Invalid level')
            else:
                raise Exception('Invalid preamble')
        else:
            raise Exception('Invalid payload')
        return signed_data
