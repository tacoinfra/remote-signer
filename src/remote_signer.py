
import struct
from pyhsm.hsmclient import HsmClient, HsmAttribute
from pyhsm.hsmenums import HsmMech
from pyhsm.convert import hex_to_bytes, bytes_to_hex
from binascii import unhexlify
from os import environ
import bitcoin
from pyblake2 import blake2b
import logging

from src.sigreq import SignatureReq


class RemoteSigner:
    TEST_SIGNATURE = 'p2sigfqcE4b3NZwfmcoePgdFCvDgvUNa6DBp9h7SZ7wUE92cG3hQC76gfvistHBkFidj1Ymsi1ZcrNHrpEjPXQoQybAv6rRxke'
    P256_SIGNATURE = struct.unpack('>L', b'\x36\xF0\x2C\x34')[0]  # results in p2sig prefix when encoded with base58 (p2sig(98))


    def __init__(self, config, ratchet=None):
        self.keys = config['keys']
        self.ratchet = ratchet
        self.hsm_slot = config['hsm_slot']
        hsm_user = config['hsm_username']
        logging.info('HSM user is {}'.format(config['hsm_username']))
        logging.info('Attempting to read env var HSM_PASSWORD')
        hsm_password = environ['HSM_PASSWORD']
        self.hsm_pin = '{}:{}'.format(hsm_user, hsm_password)
        self.hsm_libfile = config['hsm_lib']
        logging.info('HSM lib is {}'.format(config['hsm_lib']))
        self.node_addr = config['node_addr']

    def already_signed(self, sig_type):
        not_signed = self.ratchet.check(sig_type, self.sigreq.get_level())
        if not_signed:
            logging.info('{} signature for level {} has not been generated before'.format(sig_type, self.sigreq.get_level()))
        else:
            logging.error('{} signature for level {} has already been generated!'.format(sig_type, self.sigreq.get_level()))
        return not not_signed

    @staticmethod
    def b58encode_signature(sig):
        return bitcoin.bin_to_b58check(sig, magicbyte=RemoteSigner.P256_SIGNATURE)

    def sign(self, handle, payload, test_mode=False):
        logging.info('Verifying payload')
        self.sigreq = SignatureReq(payload)
        sig_type = f"{self.sigreq.get_type()}_{self.sigreq.get_chainid()}"
        encoded_sig = ''
        logging.info(f"About to sign {payload} with key handle {handle}")
        if self.already_signed(sig_type):
            logging.error('Invalid level')
            raise Exception('Invalid level')
        if test_mode:
            return self.TEST_SIGNATURE
        logging.info('About to sign with HSM client. Slot = {}, lib = {}, handle = {}'.format(self.hsm_slot, self.hsm_libfile, handle))
        with HsmClient(slot=self.hsm_slot, pin=self.hsm_pin, pkcs11_lib=self.hsm_libfile) as c:
            hashed_data = blake2b(hex_to_bytes(data_to_sign), digest_size=32).digest()
            logging.info('Hashed data to sign: {}'.format(hashed_data))
            sig = c.sign(handle=handle, data=hashed_data, mechanism=HsmMech.ECDSA)
            logging.info('Raw signature: {}'.format(sig))
            encoded_sig = RemoteSigner.b58encode_signature(sig)
            logging.info('Base58-encoded signature: {}'.format(encoded_sig))
        return encoded_sig
