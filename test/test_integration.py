import json
import logging
import sys
from functools import partial
from os import environ
from test.test_remote_signer import valid_sig_reqs
from test.utils import get_table, is_docker
from unittest.mock import patch

import boto3
import pytest
from pyblake2 import blake2b
from pyhsm.convert import hex_to_bytes
from pyhsm.hsmclient import HsmClient
from pyhsm.hsmenums import HsmMech

from signer import DEBUG, app, config, cr, rs
from src.hsmsigner import discover_handles
from src.sigreq import SignatureReq

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

KEY = next(iter(config["keys"]))  # tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW


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

    def setup_method(self, _method):
        self.table = get_table(self.dbresource, self.dbclient, self.table_name)

    def teardown_method(self, _method):
        self.table.delete()

    def test_softhsm_signs_and_verifies_bytes(self):
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
        def get_item(sigreq):
            sig_type = f"{sigreq.get_type()}_{sigreq.get_chainid()}"
            r = self.table.get_item(Key={"type": sig_type}, ConsistentRead=True)
            return r.get("Item", None)

        for req in valid_sig_reqs[0:3] + valid_sig_reqs[5:]:  # 4 fails due to ratchet
            data = f'"{req[-1]}"'
            sigreq = SignatureReq(json.loads(data))
            assert sigreq.type == req[0]

            if sigreq.type == "Ballot":

                # sign success:
                with patch.object(
                    target=rs, attribute="policy", new={"voting": [sigreq.get_vote()]}
                ):
                    raw_response = client.post(f"/keys/{KEY}", data=data)
                    assert raw_response.status == "200 OK"
                    assert "signature" in raw_response.json

                # sign fail:
                with patch.object(cr, "check", return_value=None), patch.object(
                    target=rs, attribute="policy", new={"voting": []}
                ):
                    raw_response = client.post(f"/keys/{KEY}", data=data)
                    assert raw_response.status == "500 INTERNAL SERVER ERROR"

                continue

            # sign success:
            assert get_item(sigreq) is None
            raw_response = client.post(f"/keys/{KEY}", data=data)
            assert raw_response.status == "200 OK"
            assert "signature" in raw_response.json

            assert get_item(sigreq) is not None
            # {'type': 'Baking_NetXH12Aer3be93', 'lastblock': Decimal('650'), 'lastround': Decimal('0')}

            response = json.loads(raw_response.data.decode())
            assert "signature" in response

            assert sigreq.round == 0

            # sign failure:
            raw_response = client.post(f"/keys/{KEY}", data=data)
            assert raw_response.status == "410 GONE"
