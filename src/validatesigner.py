#
# The ValidateSigner applies a ChainRatchet to the signature request
# and then passes it down to a signer.  In order to do this, it must
# parse the request and to obtain the level and round to pass to the
# ratchet code.

import logging

from src.sigreq import SignatureReq

baking_req_types = ["Baking", "Endorsement", "Preendorsement" ]

class ValidateSigner:
    def __init__(self, config, ratchet=None, subsigner=None):
        self.keys = config['keys']
        self.ratchet = ratchet
        self.subsigner = subsigner

    def sign(self, handle, sigreq):
        if sigreq.get_type() not in baking_req_types:
            raise(Exception("Unsupported signature request tag"))

        sig_type = f"{sigreq.get_type()}_{sigreq.get_chainid()}"
        logging.debug(f"About to sign {sigreq.get_payload()} " +
                      f"with key handle {handle}")

        level = sigreq.get_level()
        round = sigreq.get_round()

        self.ratchet.check(sig_type, level, round)

        return self.subsigner.sign(handle, sigreq)
