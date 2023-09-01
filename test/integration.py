import json
import logging
import sys
from functools import partial
from os import environ
from test.test_remote_signer import valid_sig_reqs
from test.utils import get_table, is_docker

import boto3
import pytest
from pyblake2 import blake2b
from pyhsm.convert import hex_to_bytes
from pyhsm.hsmclient import HsmClient
from pyhsm.hsmenums import HsmMech

from signer import DEBUG, app, config
from src.hsmsigner import discover_handles

log = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(module)s %(levelname)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

# guard
if ("softhsm" not in config["hsm_lib"]) or (not DEBUG) or (not is_docker()):
    raise ValueError(
        "integration tests only run against softhsm in DEBUG mode in docker"
    )


def build_client(config):
    hsm_slot = config["hsm_slot"]
    hsm_user = config["hsm_username"]
    hsm_password = environ["HSM_PASSWORD"]
    hsm_pin = f"{hsm_user}:{hsm_password}"
    hsm_libfile = config["hsm_lib"]
    return partial(HsmClient, slot=hsm_slot, pin=hsm_pin, pkcs11_lib=hsm_libfile)


SoftHsmClient = build_client(config)


@pytest.fixture()
def client():
    return app.test_client()


@pytest.fixture()
def hsm_client():
    return app.test_client()


class TestIntegration:
    @classmethod
    def setup_class(cls):
        cls.region_name = environ.get("REGION")
        cls.table_name = environ.get("DDB_TABLE")
        cls.endpoint_url = environ.get("BOTO3_ENDPOINT")
        cls.dbresource = boto3.resource(
            "dynamodb", region_name=cls.region_name, endpoint_url=cls.endpoint_url
        )
        cls.dbclient = boto3.client(
            "dynamodb", region_name=cls.region_name, endpoint_url=cls.endpoint_url
        )

    @classmethod
    def teardown_class(cls):
        print("Runs at end of class")

    def setup_method(self, _method):
        self.table = get_table(self.dbresource, self.dbclient, self.table_name)

    def teardown_method(self, _method):
        self.table.delete()

    def test_softhsm_sign_bytes(self):
        with SoftHsmClient() as c:
            private_handle, public_handle = discover_handles(c)
            _bytes = hex_to_bytes("012346789abcdef0")
            hashed_data = blake2b(_bytes, digest_size=32).digest()
            sig = c.sign(
                handle=private_handle, data=hashed_data, mechanism=HsmMech.ECDSA
            )
            assert c.verify(
                handle=public_handle,
                data=hashed_data,
                signature=sig,
                mechanism=HsmMech.ECDSA,
            )

    def test_post(self, client):
        for req in valid_sig_reqs[0:3]:
            data = f'"{req[4]}"'
            raw_response = client.post(
                "/keys/tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW", data=data
            )
            assert raw_response.status == "200 OK"
            response = json.loads(raw_response.data.decode())
            assert "signature" in response
