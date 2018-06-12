import struct
import string
from tezos_rpc_client import TezosRPCClient
from pyhsm.hsmclient import HsmClient
from pyhsm.hsmenums import HsmMech
from pyhsm.convert import bytes_to_hex
from os import environ


class RemoteSigner:
    BLOCK_PREAMBLE = 1
    ENDORSEMENT_PREAMBLE = 2
    LEVEL_THRESHOLD: int = 16
    TEST_SIGNATURE = '87087b1c2d0c17da8e1ef8adae56b288306de5272fd98ce8a53701a7c07ca0e8ef60eb9a649dbaaa2b4f4ff7f01d3e272d941e3190173c693ed75f3dfc001f28'

    def __init__(self, payload, rpc_stub=None):
        self.payload = payload
        self.data = self.decode_block(self.payload)
        self.rpc_stub = rpc_stub
        self.hsm_slot = environ['HSM_SLOT']
        self.hsm_key_handle = environ['HSM_KEY_HANDLE']
        hsm_user = environ['HSM_USER']
        hsm_password = environ['HSM_PASSWORD']
        self.hsm_pin = '{}:{}'.format(hsm_user, hsm_password)
        self.hsm_libfile = environ['HSM_LIBFILE']

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
        rpc = self.rpc_stub or TezosRPCClient()
        current_level = rpc.get_current_level()
        payload_level = self.get_block_level()
        return current_level < payload_level <= current_level + self.LEVEL_THRESHOLD

    def sign(self, data_to_sign, test_mode=False):
        if self.valid_block_format(data_to_sign):
            if self.is_block() or self.is_endorsement():
                if self.is_within_level_threshold():
                    signed_data = ''
                    if test_mode:
                        return self.TEST_SIGNATURE
                    else:
                        with HsmClient(slot=self.hsm_slot, pin=self.hsm_pin, pkcs11_lib=self.hsm_libfile) as c:
                            sig = c.sign(handle=self.hsm_key_handle, data=data_to_sign, mechanism=HsmMech.ECDSA_SHA256)
                            signed_data = bytes_to_hex(sig)
                else:
                    raise Exception('Invalid level')
            else:
                raise Exception('Invalid preamble')
        else:
            raise Exception('Invalid payload')
        return signed_data