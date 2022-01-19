
import struct
from binascii import unhexlify
from os import environ
import logging

from src.sigreq import SignatureReq


class ValidateSigner:
    def __init__(self, config, ratchet=None, subsigner=None):
        self.keys = config['keys']
        self.ratchet = ratchet
        self.subsigner = subsigner
        self.node_addr = config['node_addr']

    def already_signed(self, sig_type):
        not_signed = self.ratchet.check(sig_type, self.sigreq.get_level(),
                                        self.sigreq.get_round())
        log_msg = f'{sig_type} signature for level {self.sigreq.get_level()}'
        if not_signed:
            logging.info(log_msg  + ' has not been generated before')
        else:
            logging.error(log_msg + ' has already been generated!')
        return not not_signed

    def sign(self, handle, payload):
        logging.info('Verifying payload')
        self.sigreq = SignatureReq(payload)
        sig_type = f"{self.sigreq.get_type()}_{self.sigreq.get_chainid()}"
        encoded_sig = ''
        logging.info(f"About to sign {payload} with key handle {handle}")
        if self.already_signed(sig_type):
            logging.error('Invalid level')
            raise Exception('Invalid level')

        return self.subsigner.sign(handle, payload)
