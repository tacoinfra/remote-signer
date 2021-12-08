import struct
import string

from binascii import unhexlify
from os import environ

import bitcoin
from pyblake2 import blake2b

def get_be_int(bytes):
    return struct.unpack('>L', bytes[0:4])[0]

CHAIN_ID = get_be_int(b'\x00\x57\x52\x00')

class SignatureReq:

    def __init__(self, hexdata):
        if not all(c in string.hexdigits for c in hexdata):
            raise('Invalid signature request: not all hex digits')

        data = bytes.fromhex(hexdata)

        self.chainid = bitcoin.bin_to_b58check(data[1:5], magicbyte=CHAIN_ID)

        if data[0] == 0x01:     # Emmy block
            self.type  = "Baking"
            self.level = get_be_int(data[5:])

        elif data[0] == 0x02:   # Emmy endorsement
            self.type  = "Endorsement"
            self.level = get_be_int(data[-4:])

        else:
            raise(Exception('Invalid signature request tag'))

    def get_type(self):
        return self.type

    def get_chainid(self):
        return self.chainid

    def get_level(self):
        return self.level
