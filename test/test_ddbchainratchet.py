
import unittest
from test.common import run_two_key_test

from pytezos.crypto.key import Key

from tezos_signer.config import TacoinfraConfig


class TestRemoteSigner(unittest.TestCase):
    def test_local_and_ddbchainratchet(self):
        k1 = Key.generate(curve=b'p2', export=False)
        k2 = Key.generate(curve=b'p2', export=False)
        config = TacoinfraConfig(conf = {
            'aws_region': 'eu-west-1',
            'boto3_endpoint': 'http://dynamodb-local:8000',
            'chain_ratchet': 'dynamodb',
            'ddb_table': 'test',
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
