
import re
import unittest
from test.common import INVALID_PREAMBLE, run_two_key_test, sig_reqs

from pytezos.crypto.key import Key
from werkzeug.exceptions import BadRequest

from tezos_signer.config import TacoinfraConfig
from tezos_signer.sigreq import SignatureReq


class TestRemoteSigner(unittest.TestCase):
    def test_identifies_invalid_block_preamble(self):
        with self.assertRaises(BadRequest):
            SignatureReq("12125097571a7678f897098f8790g18234")
        got = SignatureReq(INVALID_PREAMBLE)
        self.assertNotIn(got.type, ['Ballot', 'Baking',
                                    'Endorsement', 'Preendorsement'])

    def test_sigreq_parsing(self):
        for req in sig_reqs:
            got = SignatureReq(req[-1])
            self.assertEqual(req[1], got.type)
            self.assertEqual(req[2], got.chainid)

            if got.type == 'Ballot':
                self.assertEqual(req[3], got.vote)
                continue

            self.assertEqual(req[3], got.level)
            self.assertEqual(req[4], got.round)

    def test_local_and_mockery(self):
        k1 = Key.generate(curve=b'p2', export=False)
        k2 = Key.generate(curve=b'p2', export=False)
        config = TacoinfraConfig(conf = {
            'chain_ratchet': 'mockery',
            'keys': [ k1.secret_key(), k2.secret_key() ],
            'policy': {
                'baking': 1,
                'voting': ['pass'],
            }
        })

        pkh1 = k1.public_key_hash()
        pkh2 = k2.public_key_hash()
        run_two_key_test(config, pkh1, pkh2)


if __name__ == '__main__':
    unittest.main()
