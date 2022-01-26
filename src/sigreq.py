import struct
import string

import bitcoin

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
            self.round = 0

        elif data[0] == 0x02:   # Emmy endorsement
            self.type  = "Endorsement"
            self.level = get_be_int(data[-4:])
            self.round = 0

        elif data[0] == 0x11:   # Tenderbake block
            self.type  = "Baking"
            self.level = get_be_int(data[5:])
            fitness_sz = get_be_int(data[83:])
            offset = 87 + fitness_sz - 4
            self.round = get_be_int(data[offset:])

        elif data[0] == 0x12:   # Tenderbake preendorsement
            self.type  = "Preendorsement"
            self.level = get_be_int(data[40:])
            self.round = get_be_int(data[44:])

        elif data[0] == 0x13:   # Tenderbake endorsement
            self.type  = "Endorsement"
            self.level = get_be_int(data[40:])
            self.round = get_be_int(data[44:])

        else:
            raise(Exception('Invalid signature request tag'))

    def get_type(self):
        return self.type

    def get_chainid(self):
        return self.chainid

    def get_level(self):
        return self.level

    def get_round(self):
        return self.round
