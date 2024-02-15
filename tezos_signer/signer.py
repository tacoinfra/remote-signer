#
# This is the base class for all of our Signer objects.  They are expected
# to implement a constructor and a single method "sign".  They return a
# base58-encoded signature.

from pytezos.crypto.encoding import base58_encode


class Signer:
    def __init__(self):
        return

    @staticmethod
    def b58encode_signature(sig):
        return base58_encode(sig, prefix=b'p2sig').decode()

    def sign(self, sigreq):
        raise(NotImplementedError("Unimplemented virtual method"))

class MockSigner(Signer):
    def __init__(self, data):
        self.raw_signed_block = data

    def sign(self, sigreq=None):
        return Signer.b58encode_signature(self.raw_signed_block)
