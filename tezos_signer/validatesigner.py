#
# The ValidateSigner applies a ChainRatchet to the signature request
# and then passes it down to a signer.  In order to do this, it must
# parse the request and to obtain the level and round to pass to the
# ratchet code.

import logging

from tezos_signer import Signer, SignatureReq

baking_req_types = ["Baking", "Endorsement", "Preendorsement" ]
voting_req_types = ["Ballot"]

class ValidateSigner(Signer):
    def __init__(self, config, ratchet=None, subsigner=None):
        self.keys = config['keys']
        self.ratchet = ratchet
        self.subsigner = subsigner
        self.policy = config['policy']

    def check_policy(self, sigreq):
        allowed = False

        if sigreq.get_type() in baking_req_types:
            if 'baking' not in self.policy or not self.policy['baking']:
                raise(Exception("Baking is against policy"))
            allowed = True

        if sigreq.get_type() in voting_req_types:
            if 'voting' not in self.policy:
                raise(Exception('Voting is against policy'))
            if sigreq.get_vote() not in self.policy['voting']:
                raise(Exception(f'Voting "{self.get_vote()}" ' +
                                 'is against policy'))
            allowed = True

        if not allowed:
            raise(Exception('Request is against policy'))

    def sign(self, handle, sigreq):
        logging.debug(f"About to sign {sigreq.get_payload()} " +
                      f"with key handle {handle}")

        self.check_policy(sigreq)

        if sigreq.get_type() in baking_req_types:
            sig_type = f"{sigreq.get_type()}_{sigreq.get_chainid()}"
            level = sigreq.get_level()
            round = sigreq.get_round()

            self.ratchet.check(sig_type, level, round)

        return self.subsigner.sign(handle, sigreq)

