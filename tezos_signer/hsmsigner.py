#
#

import logging
import threading

from PyKCS11 import CKA_CLASS, CKA_LABEL, CKM_ECDSA, CKO_PRIVATE_KEY, \
                    Mechanism, PyKCS11Lib

from tezos_signer import Signer

#
# We maintain a global seesion as many HSMs will prevent
# multiple logins from the same user at the same time,
# notably SoftHSMv2 which is used in our test framework.
# This is also a little more efficient and we do not currently
# have the ability to configure multiple HSMs in any case, so
# we are not losing any functionality...

session = None

def find_key(session, handle, filter=False):
    tmpl = [(CKA_CLASS, CKO_PRIVATE_KEY)]
    if filter:
        tmpl.append((CKA_LABEL, handle))
    objs = session.findObjects(tmpl)
    for o in objs:
        labels = session.getAttributeValue(o, [CKA_LABEL])
        labels.append(str(o.value()))
        if handle in labels:
            return o
    return None

class HsmSigner(Signer):
    def __init__(self, config, key):
        hsm_user = config.get_hsm_username()
        with open('hsm_passwd', 'r') as file:
            hsm_password = file.read().rstrip('\n')
        self.hsm_pin = f'{hsm_user}:{hsm_password}'
        self.hsm_libfile = config.get_hsm_lib()
        self.hsm_private_handle = key['signer_args'][0]
        self.hsm_slot = config.get_hsm_slot()
        self.key = key
        self.lock = threading.Lock()

        global session
        if session is None:
            pkcs11 = PyKCS11Lib()
            pkcs11.load(self.hsm_libfile)
            session = pkcs11.openSession(self.hsm_slot)
            session.login(self.hsm_pin)
        self.session = session

        self.key = find_key(self.session, self.hsm_private_handle, True)
        if self.key is None:
            self.key = find_key(self.session, self.hsm_private_handle)

        if self.key is None:
            raise(KeyError(f"Can't find key for {key['pkh']}"))

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
