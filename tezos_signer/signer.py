#
# This is the base class for all of our Signer objects.  They are expected
# to implement a constructor and a single method "sign".  They return a
# base58-encoded signature.

from pytezos_core.encoding import base58_encode


class Signer:
    def __init__(self):
        return

    @staticmethod
    def b58encode_signature(sig):
        return base58_encode(sig, prefix=b'p2sig')

    def sign(self, handle, sigreq):
        raise(NotImplementedError("Unimplemented virtual method"))
