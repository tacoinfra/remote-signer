#
#

import logging
from os import environ
import threading

from pyhsm.hsmclient import HsmClient
from pyhsm.hsmenums import HsmMech

from pyblake2 import blake2b

from tezos_signer import Signer


class HsmSigner(Signer):
    def __init__(self, config):
        self.hsm_slot = config['hsm_slot']
        hsm_user = config['hsm_username']
        with open('hsm_passwd', 'r') as file:
            hsm_password = file.read().rstrip('\n')
        self.hsm_pin = f'{hsm_user}:{hsm_password}'
        self.hsm_libfile = config['hsm_lib']
        self.lock = threading.Lock()

    def sign(self, handle, sigreq):
        logging.debug(f'Signing with HSM client:')
        logging.debug(f'    Slot = {self.hsm_slot}')
        logging.debug(f'    lib = {self.hsm_libfile}')
        logging.debug(f'    handle = {handle}')
        with self.lock:
            with HsmClient(slot=self.hsm_slot, pin=self.hsm_pin,
                           pkcs11_lib=self.hsm_libfile) as c:
                hashed_data = blake2b(hex_to_bytes(sigreq.get_payload()),
                                      digest_size=32).digest()
                logging.debug(f'Hashed data to sign: {hashed_data}')
                sig = c.sign(handle=handle, data=hashed_data,
                             mechanism=HsmMech.ECDSA)

        logging.debug(f'Raw signature: {sig}')
        encoded_sig = Signer.b58encode_signature(sig)
        logging.debug(f'Base58-encoded signature: {encoded_sig}')
        return encoded_sig
