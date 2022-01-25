#
# The ValidateSigner applies a ChainRatchet to the signature request
# and then passes it down to a signer.  In order to do this, it must
# parse the request and to obtain the level and round to pass to the
# ratchet code.

import logging

from src.sigreq import SignatureReq


class ValidateSigner:
    def __init__(self, config, ratchet=None, subsigner=None):
        self.keys = config['keys']
        self.ratchet = ratchet
        self.subsigner = subsigner
        self.node_addr = config['node_addr']

    def sign(self, handle, payload):
        self.sigreq = SignatureReq(payload)
        sig_type = f"{self.sigreq.get_type()}_{self.sigreq.get_chainid()}"
        logging.debug(f"About to sign {payload} with key handle {handle}")

        level = self.sigreq.get_level()
        round = self.sigreq.get_round()

        logging.info(f"Received request to sign at {level}/{round}")

        self.ratchet.check(sig_type, level, round)

        return self.subsigner.sign(handle, payload)
