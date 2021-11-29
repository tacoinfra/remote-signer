
import re
import struct
import unittest

import bitcoin

from src.sigreq import SignatureReq
from src.validatesigner import ValidateSigner
from src.signer import Signer
from src.chainratchet import ChainRatchet, MockChainRatchet


def eatwhite(str):
    return re.sub(r"\s+", "", str)

# results in p2sig prefix when encoded with base58 (p2sig(98)):
P256_SIG= struct.unpack('>L', b'\x36\xF0\x2C\x34')[0]
RAW_SIGNED_BLOCK = b'0123456789012345678901'
SIGNED_BLOCK = bitcoin.bin_to_b58check(RAW_SIGNED_BLOCK, magicbyte=P256_SIG)

#
# Here's a quick invalid block that we'll make sure that we don't process:

INVALID_PREAMBLE = eatwhite("""
        030000000000000002012c866bd675ad11475ea608dea4d9d166801f1725b2076363
        63d55508aa07ba6f000000005b17b90d04683625c2445a4e9564bf710c5528fd99a7
        d150d2a2a323bc22ff9e2710da4f6d00000011000000010000000008000000000000
        000289b5a4e5e20c56512c64967dfa72e67c39166d5c48ad6884693c7d192e105c3b
        00058f7b73557941607800""")

#
# Here we provide a list of valid blocks over which we shall iterate:
# They are each a tuple of the expected results:
#         (type, chainid, level)

valid_sig_reqs = [
      ("Baking", "NetXH12Aer3be93", 650, eatwhite("""
        01000000000000028a0130009e2cb10ef25b54563989371653d9ba6545c475a1d583
        ac8b4a28583df98d000000005b29ab5c04ce84d452f0c4accfbb23f42e5a23e91915
        2a40ee17b56a6e7f1b95cfd20d792c00000011000000010000000008000000000000
        2ceb3306c828b082cf23d15de02f6d5b028652569bf794e74d7c839c50c7e82fc781
        0000e27015247d6713cd00"""))

    , ("Endorsement", "NetXjkQyBJ9VYHe", 631, eatwhite("""
        029feab277d4b686c59365261c4210f21d916fbb09f5e47e092a14b94e39fab61900
        00000277"""))
]


class MockHsmSigner:
    def client():
        return self

    def sign(self, handle=None, data=None, mechanism=None):
        return Signer.b58encode_signature(RAW_SIGNED_BLOCK)


class TestRemoteSigner(unittest.TestCase):
    TEST_CONFIG = {
        'hsm_username': 'resigner',
        'hsm_slot': 1,
        'hsm_lib': '/opt/cloudhsm/lib/libcloudhsm_pkcs11.so',
        'node_addr': 'http://node.internal:8732',
        'keys': {
            'tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW': {
                'public_key': 'p2pk67jx4rEadFpbHdiPhsKxZ4KCoczLWqsEpNarWZ7WQ1SqKMf7JsS',
                'private_handle': 7,
                'public_handle': 9
            }
        }
    }

    def test_identifies_invalid_block_preamble(self):
        with self.assertRaises(Exception):
            rs = ValidateSigner(self.TEST_CONFIG,
                                ratchet=MockChainRatchet(0),
                                hsm=MockHsmSigner())
            rs.sign(7, INVALID_PREAMBLE)

    def test_list_sigreqs(self):
        for req in valid_sig_reqs:
            #
            # First we test if we are successfully parsing the blocks:
            got = SignatureReq(req[3])
            self.assertEqual(req[0], got.type)
            self.assertEqual(req[1], got.chainid)
            self.assertEqual(req[2], got.level)

            #
            # Now, let's test mock signing.  Note, we only have one
            # valid signature in the MockHsmSigner, but we are mainly
            # testing to ensure that we are denied when we double bake:

            rs = ValidateSigner(self.TEST_CONFIG,
                                ratchet=MockChainRatchet(got.level-1),
                                subsigner=MockHsmSigner())
            self.assertEqual(rs.sign(7, req[3]), SIGNED_BLOCK)

            #
            # And now, for a failure:

            with self.assertRaises(Exception):
                    rs = ValidateSigner(self.TEST_CONFIG,
                                        ratchet=MockChainRatchet(got.level),
                                        subsigner=MockHsmSigner())
                    rs.sign(7, req[3])


if __name__ == '__main__':
    unittest.main()
