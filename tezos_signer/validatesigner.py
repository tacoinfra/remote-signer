#
# The ValidateSigner applies a ChainRatchet to the signature request
# and then passes it down to a signer.  In order to do this, it must
# parse the request and to obtain the level and round to pass to the
# ratchet code.

import logging

from tezos_signer import SignatureReq, Signer

baking_req_types = ["Baking", "Endorsement", "Preendorsement" ]
voting_req_types = ["Ballot"]

class ValidateSigner(Signer):
    def __init__(self, config, key, ratchet=None, subsigner=None):
        self.ratchet = ratchet
        self.subsigner = subsigner
        self.policy = config.get_policy()
        self.key = key

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

    def sign(self, sigreq):
        logging.debug(f"About to sign {sigreq.get_hex_payload()}")

        self.check_policy(sigreq)

        if sigreq.get_type() in baking_req_types:
            sig_type = f"{sigreq.get_type()}_{sigreq.get_chainid()}"
            sig_type += f"_{self.key['pkh']}"
            level = sigreq.get_level()
            round = sigreq.get_round()

            self.ratchet.check(sig_type, level, round)

        return self.subsigner.sign(sigreq)
