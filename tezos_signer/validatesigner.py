#
# The ValidateSigner applies a ChainRatchet to the signature request
# and then passes it down to a signer.  In order to do this, it must
# parse the request and to obtain the level and round to pass to the
# ratchet code.

import logging

from werkzeug.exceptions import abort

from tezos_signer import Signer

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
                abort(403, "Baking is against policy")
            allowed = True

        if sigreq.get_type() in voting_req_types:
            if 'voting' not in self.policy:
                abort(403, 'Voting is against policy')
            if sigreq.get_vote() not in self.policy['voting']:
                abort(403, f'Voting "{sigreq.get_vote()}" is against policy')
            allowed = True

        if 'allow_all' in self.policy and self.policy['allow_all']:
            allowed = True

        if not allowed:
            abort(403, 'Request is against policy')

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
