#
#

import logging
import threading

from PyKCS11 import CK_OBJECT_HANDLE, CKF_RW_SESSION, CKF_SERIAL_SESSION, \
                    CKM_ECDSA, Mechanism, PyKCS11Lib

from tezos_signer import Signer

#
# We maintain a global seesion as many HSMs will prevent
# multiple logins from the same user at the same time,
# notably SoftHSMv2 which is used in our test framework.
# This is also a little more efficient and we do not currently
# have the ability to configure multiple HSMs in any case, so
# we are not losing any functionality...

session = None

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

        global session
        if session is None:
            pkcs11 = PyKCS11Lib()
            pkcs11.load(self.hsm_libfile)
            session = pkcs11.openSession(self.hsm_slot,
                                         CKF_SERIAL_SESSION|CKF_RW_SESSION)
            session.login(self.hsm_pin)
        self.session = session

        self.key = CK_OBJECT_HANDLE(self.session)
        self.key.assign(self.hsm_private_handle)

    def sign(self, sigreq):
        logging.debug(f'Signing with HSM client:')
        logging.debug(f'    Slot = {self.hsm_slot}')
        logging.debug(f'    lib = {self.hsm_libfile}')
        logging.debug(f'    private_handle = {self.hsm_private_handle}')
        #
        # XXXrcd: we continue to use a lock because it was necessary
        #         when we were using py-hsm.  We are not sure we needed
        #         it due to bugs in py-hsm or the underlying PKCS#11
        #         library.  Although we strongly suspect the former, we
        #         have not had time to test our hypothesis.
        with self.lock:
            sig = self.session.sign(self.key, sigreq.get_hashed_payload(),
                                    Mechanism(CKM_ECDSA, None))
            sig = bytes(sig)
            logging.debug(f'Raw signature: {sig}')
            encoded_sig = Signer.b58encode_signature(sig)
            logging.debug(f'Base58-encoded signature: {encoded_sig}')
            return encoded_sig
