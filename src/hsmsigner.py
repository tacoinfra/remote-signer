#
#

import logging
from os import environ

from pyhsm.hsmclient import HsmClient
from pyhsm.hsmenums import HsmMech
from pyhsm.convert import hex_to_bytes

from pyblake2 import blake2b

from src.signer import Signer


class HsmSigner(Signer):
    def __init__(self, config):
        self.hsm_slot = config['hsm_slot']
        hsm_user = config['hsm_username']
        hsm_password = environ['HSM_PASSWORD']
        self.hsm_pin = f'{hsm_user}:{hsm_password}'
        self.hsm_libfile = config['hsm_lib']

    def sign(self, handle, payload):
        logging.debug(f'Signing with HSM client:')
        logging.debug(f'    Slot = {self.hsm_slot}')
        logging.debug(f'    lib = {self.hsm_libfile}')
        logging.debug(f'    handle = {handle}')
        with HsmClient(slot=self.hsm_slot, pin=self.hsm_pin,
                       pkcs11_lib=self.hsm_libfile) as c:
            hashed_data = blake2b(hex_to_bytes(payload),
                                  digest_size=32).digest()
            logging.debug(f'Hashed data to sign: {hashed_data}')
            sig = c.sign(handle=handle, data=hashed_data,
                         mechanism=HsmMech.ECDSA)

        logging.debug(f'Raw signature: {sig}')
        encoded_sig = Signer.b58encode_signature(sig)
        logging.debug(f'Base58-encoded signature: {encoded_sig}')
        return encoded_sig
