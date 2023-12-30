
import os
import unittest
from test.common import INVALID_PREAMBLE, run_two_key_test, sig_reqs

from asn1crypto.core import OctetString
from PyKCS11 import *
from pytezos.crypto.key import Key

from tezos_signer.config import TacoinfraConfig
from tezos_signer.sigreq import SignatureReq


class TestRemoteSigner(unittest.TestCase):
    def create_hsm_keys(self, hsm_lib, hsm_slot, hsm_pin ):
        pkcs11 = PyKCS11Lib()
        pkcs11.load(hsm_lib)
        session = pkcs11.openSession(hsm_slot,
                                     CKF_SERIAL_SESSION|CKF_RW_SESSION)
        session.login(hsm_pin)

        mech = PyKCS11.Mechanism(PyKCS11.CKM_EC_KEY_PAIR_GEN, None)
        pubTmpl = [
            (PyKCS11.CKA_TOKEN, True),
            (PyKCS11.CKA_PRIVATE, False),
            (PyKCS11.CKA_VERIFY, True),
            (PyKCS11.CKA_EC_PARAMS,
             b'\x06\x08\x2a\x86\x48\xce\x3d\x03\x01\x07') # OID for prime256v1
        ]
        privTmpl = [
            (PyKCS11.CKA_TOKEN, True),
            (PyKCS11.CKA_PRIVATE, True),
            (PyKCS11.CKA_SIGN, True),
        ]

        ret = []
        for i in [1, 2]:
            tmpPubTmpl = pubTmpl 
            tmpPrivTmpl = privTmpl 
            label = os.urandom(8).hex()
            tmpPubTmpl.append((PyKCS11.CKA_LABEL, f"{label}-{i}"))
            tmpPrivTmpl.append((PyKCS11.CKA_LABEL, f"{label}-{i}"))
            (pub, priv) = session.generateKeyPair(tmpPubTmpl, tmpPrivTmpl, mech)

            val = session.getAttributeValue(pub, [PyKCS11.CKA_EC_POINT])[0]
            ec_point_data = bytes(val)
            ec_point = OctetString.load(ec_point_data).native
            x_coordinate = ec_point[1:33]
            if ec_point[64] % 2 == 0:
                compressed = b'\x02' + x_coordinate
            else:
                compressed = b'\x03' + x_coordinate
            k = Key.from_public_point(compressed, b'p2')
            ret.append(k)
            ret.append(f"{label}-{i}")

        session.logout()
        session.closeSession()
        return ret

    def test_hsm_and_mockery(self):
        hsm_user = 'resigner'
        hsm_thing = '1234'
        hsm_pin = f"{hsm_user}:{hsm_thing}"
        hsm_lib = '/usr/lib64/libsofthsm2.so'

        with open('/home/ec2-user/hsm_slot', 'r') as file:
            hsm_slot = int(file.read().rstrip('\n'))

        (pub1, priv1, pub2, priv2) = self.create_hsm_keys(hsm_lib, hsm_slot,
                                                          hsm_pin)

        with self.assertRaises(KeyError):
            config = TacoinfraConfig(conf = {
                'hsm_username': hsm_user,
                'hsm_password': hsm_thing,
                'hsm_lib': hsm_lib,
                'hsm_slot': hsm_slot,
                'chain_ratchet': 'mockery',
                'keys': [
                    f"{pub1.public_key()}:pkcs11_hsm:bad-label-1",
                    f"{pub2.public_key()}:pkcs11_hsm:bad-label-2",
                ],
            })

        config = TacoinfraConfig(conf = {
            'hsm_username': hsm_user,
            'hsm_password': hsm_thing,
            'hsm_lib': hsm_lib,
            'hsm_slot': hsm_slot,
            'chain_ratchet': 'mockery',
            'keys': {
                pub1.public_key(): {
                    "signer": "pkcs11_hsm",
                    "signer_args": [ priv1 ],
                },
                pub2.public_key_hash(): {
                    "public_key": pub2.public_key(),
                    "signer": "pkcs11_hsm",
                    "signer_args": [ priv2 ],
                },
            },
            'policy': {
                'baking': 1,
                'voting': ['pass'],
            }
        })

        pkh1 = pub1.public_key_hash()
        pkh2 = pub2.public_key_hash()
        run_two_key_test(config, pkh1, pkh2)


if __name__ == '__main__':
    unittest.main()
