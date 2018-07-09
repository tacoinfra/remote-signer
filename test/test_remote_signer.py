#########################################################
# Written by Carl Youngblood, carl@blockscale.net
# Copyright (c) 2018 Blockscale LLC
# released under the MIT license
#########################################################

import unittest
from src.remote_signer import RemoteSigner


class TestRemoteSigner(unittest.TestCase):
    INVALID_PREAMBLE = '030000000000000002012c866bd675ad11475ea608dea4d9d166801f1725b207636363d55508aa07ba6f000000005b17b90d04683625c2445a4e9564bf710c5528fd99a7d150d2a2a323bc22ff9e2710da4f6d00000011000000010000000008000000000000000289b5a4e5e20c56512c64967dfa72e67c39166d5c48ad6884693c7d192e105c3b00058f7b73557941607800'
    VALID_BLOCK = '01000000000000028a0130009e2cb10ef25b54563989371653d9ba6545c475a1d583ac8b4a28583df98d000000005b29ab5c04ce84d452f0c4accfbb23f42e5a23e919152a40ee17b56a6e7f1b95cfd20d792c000000110000000100000000080000000000002ceb3306c828b082cf23d15de02f6d5b028652569bf794e74d7c839c50c7e82fc7810000e27015247d6713cd00'
    VALID_ENDORSEMENT = '029feab277d4b686c59365261c4210f21d916fbb09f5e47e092a14b94e39fab6190000000277'
    SIGNED_BLOCK = 'p2sigfqcE4b3NZwfmcoePgdFCvDgvUNa6DBp9h7SZ7wUE92cG3hQC76gfvistHBkFidj1Ymsi1ZcrNHrpEjPXQoQybAv6rRxke'
    PUBLIC_KEY = 'p2pk67jx4rEadFpbHdiPhsKxZ4KCoczLWqsEpNarWZ7WQ1SqKMf7JsS'
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
        rs = RemoteSigner(self.TEST_CONFIG, self.INVALID_PREAMBLE)
        self.assertFalse(rs.is_block())

    def test_identifies_valid_block_preamble(self):
        rs = RemoteSigner(self.TEST_CONFIG, self.VALID_BLOCK)
        self.assertTrue(rs.is_block())

    def test_identifies_valid_endorsement_preamble(self):
        rs = RemoteSigner(self.TEST_CONFIG, self.VALID_ENDORSEMENT)
        self.assertTrue(rs.is_endorsement())

    def test_decodes_block_level(self):
        rs = RemoteSigner(self.TEST_CONFIG, self.VALID_BLOCK)
        self.assertEqual(rs.get_block_level(), 650)

    def test_succeeds_if_level_less_than_block_to_sign(self):
        class DummyRPCClient:
            def get_current_level(self):
                return 649

        rs = RemoteSigner(self.TEST_CONFIG, self.VALID_BLOCK, DummyRPCClient())
        self.assertTrue(rs.is_within_level_threshold())

    def test_fails_if_level_equal_to_block_to_sign(self):
        class DummyRPCClient:
            def get_current_level(self):
                return 650

        rs = RemoteSigner(self.TEST_CONFIG, self.VALID_BLOCK, DummyRPCClient())
        self.assertFalse(rs.is_within_level_threshold())

    def test_succeeds_if_level_equal_to_endorsement_to_sign(self):
        class DummyRPCClient:
            def get_current_level(self):
                return 631

        rs = RemoteSigner(self.TEST_CONFIG, self.VALID_ENDORSEMENT, DummyRPCClient())
        self.assertTrue(rs.is_within_level_threshold())

    def test_succeeds_if_level_greater_than_endorsement_to_sign(self):
        class DummyRPCClient:
            def get_current_level(self):
                return 635

        rs = RemoteSigner(self.TEST_CONFIG, self.VALID_ENDORSEMENT, DummyRPCClient())
        self.assertTrue(rs.is_within_level_threshold())

    def test_signs_block(self):
        class DummyRPCClient:
            def get_current_level(self):
                return 649

        rs = RemoteSigner(self.TEST_CONFIG, self.VALID_BLOCK, DummyRPCClient())
        self.assertEqual(rs.sign(7, test_mode=True), self.SIGNED_BLOCK)


if __name__ == '__main__':
    unittest.main()
