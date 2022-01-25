#
# The ValidateSigner applies a ChainRatchet to the signature request
# and then passes it down to a signer.  In order to do this, it must
# parse the request and to obtain the level and round to pass to the
# ratchet code.

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

    def sign(self, handle, payload):
        logging.info('Verifying payload')
        self.sigreq = SignatureReq(payload)
        sig_type = f"{self.sigreq.get_type()}_{self.sigreq.get_chainid()}"
        logging.info(f"About to sign {payload} with key handle {handle}")

        self.ratchet.check(sig_type, self.sigreq.get_level(),
                           self.sigreq.get_round())

        return self.subsigner.sign(handle, payload)
