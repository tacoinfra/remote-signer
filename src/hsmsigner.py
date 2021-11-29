#
#

import logging
from os import environ

from pyhsm.hsmclient import HsmClient, HsmAttribute
from pyhsm.hsmenums import HsmMech
from pyhsm.convert import hex_to_bytes, bytes_to_hex

from pyblake2 import blake2b

from src.signer import Signer


class HsmSigner(Signer):
    def __init__(self, config):
        self.hsm_slot = config['hsm_slot']
        hsm_user = config['hsm_username']
        logging.info('HSM user is {}'.format(config['hsm_username']))
        logging.info('Attempting to read env var HSM_PASSWORD')
        hsm_password = environ['HSM_PASSWORD']
        self.hsm_pin = '{}:{}'.format(hsm_user, hsm_password)
        self.hsm_libfile = config['hsm_lib']
        logging.info('HSM lib is {}'.format(config['hsm_lib']))

    def sign(self, handle, payload):
        logging.info(f'Signing with HSM client:')
        logging.info(f'    Slot = {self.hsm_slot}')
        logging.info(f'    lib = {self.hsm_libfile}')
        logging.info(f'    handle = {handle}')
        with HsmClient(slot=self.hsm_slot, pin=self.hsm_pin,
                       pkcs11_lib=self.hsm_libfile) as c:
            hashed_data = blake2b(hex_to_bytes(payload),
                                  digest_size=32).digest()
            logging.info('Hashed data to sign: {}'.format(hashed_data))
            sig = c.sign(handle=handle, data=hashed_data,
                         mechanism=HsmMech.ECDSA)

        logging.info('Raw signature: {}'.format(sig))
        encoded_sig = Signer.b58encode_signature(sig)
        logging.info('Base58-encoded signature: {}'.format(encoded_sig))
        return encoded_sig