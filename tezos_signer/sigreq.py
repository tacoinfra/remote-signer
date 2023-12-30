import string
import struct

from pytezos.crypto.encoding import base58_encode
from pytezos.crypto.key import blake2b


def get_be_int(bytes):
    return struct.unpack('>L', bytes[0:4])[0]

def drop_bytes(b, n):
    del(b[:n])

def parse_bytes(b, n):
    ret = b[:n]
    drop_bytes(b, n)
    if n == 1:
        ret = ord(ret)
    return ret

def parse_be_int(b):
    return get_be_int(parse_bytes(b, 4))

def parse_chain_id(b):
    return base58_encode(parse_bytes(b, 4), prefix=b'Net').decode()

class SignatureReq:

    def __init__(self, hexdata):
        if not all(c in string.hexdigits for c in hexdata):
            raise('Invalid signature request: not all hex digits')

        self.hex_payload = hexdata
        self.payload = bytes.fromhex(hexdata)

        data = bytearray(self.payload)
        self.level   = None
        tag = parse_bytes(data, 1)
        self.chainid = parse_chain_id(data)

        if tag == 0x03:   # Operation, for now, we only do ballots
            self.chainid = None
            self.type = "Unknown operation"
            self.blockhash = parse_bytes(data, 28)    # The block hash
            errs = []
            while len(data) > 0:
                # The entire operation must be consumed so that the
                # next byte will be the next operation tag.  Also, for
                # now, we stop after the first operation as we would need
                # to update the framework to deal with multiple operations.
                # We leave the loop in to suggest this later extension.
                otag = parse_bytes(data, 1)
                if self.type != "Unknown operation":
                    self.type = "Multiple operations not supported"
                elif otag == 0x06:                        # 0x06 is a ballot
                    self.pkh_type = parse_bytes(data, 1)
                    self.pkh = parse_bytes(data, 20)
                    self.period = parse_bytes(data, 4)
                    self.proposal = parse_bytes(data, 32)
                    vote = parse_bytes(data, 1)
                    if vote == 0x00:
                        self.type = "Ballot"
                        self.vote = 'yay'
                    elif vote == 0x01:
                        self.type = "Ballot"
                        self.vote = 'nay'
                    elif vote == 0x02:
                        self.type = "Ballot"
                        self.vote = 'pass'
                else:
                    errs.append(f"{otag}")
            if len(errs) > 0:
                self.type = "Unknown operation tags: {", ".join(errs)}"

        elif tag == 0x11:   # Tenderbake block
            self.type  = "Baking"
            self.level = parse_be_int(data)
            drop_bytes(data, 74)
            fitness_sz = parse_be_int(data)
            drop_bytes(data, fitness_sz - 4)
            self.round = parse_be_int(data)

        elif tag == 0x12:   # Tenderbake preendorsement
            self.type  = "Preendorsement"
            drop_bytes(data, 35)
            self.level = parse_be_int(data)
            self.round = parse_be_int(data)

        elif tag == 0x13:   # Tenderbake endorsement
            self.type  = "Endorsement"
            drop_bytes(data, 35)
            self.level = parse_be_int(data)
            self.round = parse_be_int(data)

        else:
            self.type = f"Unknown tag: {tag}"

        self.logstr = f"{self.chainid} {self.type}"
        if self.level is not None:
            self.logstr += f" at {self.level}/{self.round}"

    def get_hex_payload(self):
        return self.hex_payload

    def get_payload(self):
        return self.payload

    def get_hashed_payload(self):
        return blake2b(self.payload, digest_size=32).digest()

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
