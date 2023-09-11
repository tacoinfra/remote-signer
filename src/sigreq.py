import string
import struct

from src.bitcoin.py3specials import bin_to_b58check


def get_be_int(bytes):
    return struct.unpack(">L", bytes[0:4])[0]


CHAIN_ID = get_be_int(b"\x00\x57\x52\x00")


class SignatureReq:
    def __init__(self, hexdata):
        if not all(c in string.hexdigits for c in hexdata):
            raise Exception("Invalid signature request: not all hex digits")

        self.payload = hexdata
        data = bytes.fromhex(hexdata)

        self.level = None
        self.chainid = bin_to_b58check(data[1:5], magicbyte=CHAIN_ID)

        if data[0] == 0x01:  # Emmy block
            self.type = "Baking"
            self.level = get_be_int(data[5:])
            self.round = 0

        elif data[0] == 0x02:  # Emmy endorsement
            self.type = "Endorsement"
            self.level = get_be_int(data[-4:])
            self.round = 0

        elif data[0] == 0x03:  # Operation, for now, we only do ballots
            self.chainid = None
            self.type = "Unknown operation"
            self.blockhash = data[1:32]  # The block hash
            if data[33] == 0x06:  # 0x06 is a ballot
                self.pkh_type = data[34]  # Public Key Hash type
                self.pkh = data[35:55]  # Public Key Hash
                self.period = data[55:59]
                self.proposal = data[59:91]
                if data[91] == 0x00:
                    self.type = "Ballot"
                    self.vote = "yay"
                elif data[91] == 0x01:
                    self.type = "Ballot"
                    self.vote = "nay"
                elif data[91] == 0x02:
                    self.type = "Ballot"
                    self.vote = "pass"

        elif data[0] == 0x11:  # Tenderbake block
            self.type = "Baking"
            self.level = get_be_int(data[5:])
            fitness_sz = get_be_int(data[83:])
            offset = 87 + fitness_sz - 4
            self.round = get_be_int(data[offset:])

        elif data[0] == 0x12:  # Tenderbake preendorsement
            self.type = "Preendorsement"
            self.level = get_be_int(data[40:])
            self.round = get_be_int(data[44:])

        elif data[0] == 0x13:  # Tenderbake endorsement
            self.type = "Endorsement"
            self.level = get_be_int(data[40:])
            self.round = get_be_int(data[44:])

        else:
            self.type = "Unknown tag"

        self.logstr = f"{self.chainid} {self.type}"
        if self.level is not None:
            self.logstr += f" at {self.level}/{self.round}"

    def get_payload(self):
        return self.payload

    def get_type(self):
        return self.type

    def get_chainid(self):
        return self.chainid

    def get_level(self):
        return self.level

    def get_round(self):
        return self.round

    def get_vote(self):
        return self.vote

    def get_logstr(self):
        return self.logstr
