#
# This is the base class for all of our Signer objects.  They are expected
# to implement a constructor and a single method "sign".  They return a
# base58-encoded signature.

import struct

import bitcoin

# results in p2sig prefix when encoded with base58 (p2sig(98)):
P256_SIGNATURE = struct.unpack(">L", b"\x36\xF0\x2C\x34")[0]


class Signer:
    def __init__(self):
        return

    @staticmethod
    def b58encode_signature(sig):
        return bitcoin.bin_to_b58check(sig, magicbyte=P256_SIGNATURE)

    def sign(self, *_args, **_kwargs):
        raise (NotImplementedError("Unimplemented virtual method"))
