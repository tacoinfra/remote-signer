import struct
import string
from tezos_rpc_client import TezosRPCClient

class Resigner:
    BLOCK_PREAMBLE = 1
    ENDORSEMENT_PREAMBLE = 2
    LEVEL_THRESHOLD: int = 16

    def __init__(self, payload, rpc_stub=None):
        self.payload = payload
        self.data = self.decode_block(self.payload)
        self.rpc_stub = rpc_stub

    @staticmethod
    def valid_block_format(blockdata):
        return all(c in string.hexdigits for c in blockdata)

    @staticmethod
    def decode_block(data):
        return Resigner.valid_block_format(data) and bytes.fromhex(data)

    def is_block(self):
        return self.data and list(self.data)[0] == self.BLOCK_PREAMBLE

    def is_endorsement(self):
        return list(self.data)[0] == self.ENDORSEMENT_PREAMBLE

    def get_block_level(self):
        str = self.data[1:5]
        return struct.unpack('>L', str)[0]

    def is_within_level_threshold(self):
        rpc = self.rpc_stub or TezosRPCClient()
        current_level = rpc.get_current_level()
        payload_level = self.get_block_level()
        return current_level < payload_level <= current_level + self.LEVEL_THRESHOLD


def lambda_handler(event, context):
    rs = Resigner(event)
    signature = ''
    if rs.is_valid_request():
        if rs.is_block() and rs.is_within_level_threshold():
            pass
        elif rs.is_endorsement():
            pass
        else:
            raise Exception('Invalid preamble.')
    else:
        raise Exception('Invalid request.')
    return {'signature': signature}
