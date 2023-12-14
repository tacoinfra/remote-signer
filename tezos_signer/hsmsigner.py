#
#

import logging
import threading
from os import environ

from pyhsm.hsmclient import HsmClient
from pyhsm.hsmenums import HsmMech

from tezos_signer import Signer


class HsmSigner(Signer):
    def __init__(self, config, key):
        hsm_user = config.get_hsm_username()
        with open('hsm_passwd', 'r') as file:
            hsm_password = file.read().rstrip('\n')
        self.hsm_pin = f'{hsm_user}:{hsm_password}'
        self.hsm_libfile = config.get_hsm_lib()
        self.hsm_private_handle = int(key['signer_args'][0])
        self.hsm_slot = config.get_hsm_slot()
        self.key = key
        self.lock = threading.Lock()

    def sign(self, sigreq):
        logging.debug(f'Signing with HSM client:')
        logging.debug(f'    Slot = {self.hsm_slot}')
        logging.debug(f'    lib = {self.hsm_libfile}')
        logging.debug(f'    private_handle = {self.hsm_private_handle}')
        with self.lock:
            with HsmClient(slot=self.hsm_slot, pin=self.hsm_pin,
                           pkcs11_lib=self.hsm_libfile) as c:
                hashed_data = sigreq.get_hashed_payload()
                logging.debug(f'Hashed data to sign: {hashed_data}')
                sig = c.sign(handle=self.hsm_private_handle, data=hashed_data,
                             mechanism=HsmMech.ECDSA)

        logging.debug(f'Raw signature: {sig}')
        encoded_sig = Signer.b58encode_signature(sig)
        logging.debug(f'Base58-encoded signature: {encoded_sig}')
        return encoded_sig
