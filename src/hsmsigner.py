import logging
import threading
from os import environ

from pyblake2 import blake2b
from pyhsm.convert import hex_to_bytes
from pyhsm.hsmclient import HsmClient
from pyhsm.hsmenums import HsmAttribute, HsmMech

from src.signer import Signer


def discover_handles(c):
    h1, h2 = c.find_objects()
    if int.from_bytes(
        c.get_attribute_value(h1, attribute_type=HsmAttribute.PRIVATE),
        byteorder="little",
    ):
        return h1, h2
    else:
        return h2, h1


class HsmSigner(Signer):
    def __init__(self, config):
        self.hsm_slot = config["hsm_slot"]
        hsm_user = config["hsm_username"]
        hsm_password = environ["HSM_PASSWORD"]
        self.hsm_pin = f"{hsm_user}:{hsm_password}"
        self.hsm_libfile = config["hsm_lib"]
        self.lock = threading.Lock()

    def sign(self, handle, sigreq):
        logging.debug("Signing with HSM client:")
        logging.debug(f"    Slot = {self.hsm_slot}")
        logging.debug(f"    lib = {self.hsm_libfile}")
        logging.debug(f"    handle = {handle}")
        with self.lock:
            with HsmClient(
                slot=self.hsm_slot, pin=self.hsm_pin, pkcs11_lib=self.hsm_libfile
            ) as c:
                hashed_data = blake2b(
                    hex_to_bytes(sigreq.get_payload()), digest_size=32
                ).digest()
                logging.debug(f"Hashed data to sign: {hashed_data}")
                if environ.get("DEBUG", None):
                    """
                    with softhsm, pkcs11 returns different handles
                    in each session so we have to interrogate the API
                    every time:
                    """
                    private_handle, _public_handle = discover_handles(c)
                    handle = private_handle
                sig = c.sign(handle=handle, data=hashed_data, mechanism=HsmMech.ECDSA)

        logging.debug(f"Raw signature: {sig}")
        encoded_sig = Signer.b58encode_signature(sig)
        logging.debug(f"Base58-encoded signature: {encoded_sig}")
        return encoded_sig
