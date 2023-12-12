#
# This is a simple local signer class.  It expects to have the secret
# key passed in via the standard config next to the public_key.

from pytezos_core.key import Key

from tezos_signer import Signer


class LocalSigner(Signer):
    def __init__(self, config, key):
        self.config = config
        self.private_key = key['private_key']

    def sign(self, sigreq):
        key = Key.from_encoded_key(self.private_key)
        return key.sign(sigreq.get_payload())
