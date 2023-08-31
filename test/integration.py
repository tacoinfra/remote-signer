import json
import logging
import sys
import unittest
from os import environ
from test.test_remote_signer import valid_sig_reqs
from unittest.mock import patch

import boto3
import botocore
from pyblake2 import blake2b
from pyhsm.convert import hex_to_bytes
from pyhsm.hsmclient import HsmClient
from pyhsm.hsmenums import HsmAttribute, HsmMech, HsmSymKeyGen

from signer import DEBUG, app, config
from src.hsmsigner import discover_handles

log = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(module)s %(levelname)s: %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)


class Integration(unittest.TestCase):
    @classmethod
    def create_table(cls):
        try:
            table = cls.dbresource.create_table(
                TableName=cls.table_name,
                KeySchema=[
                    {"AttributeName": "type", "KeyType": "HASH"},  # Partition_key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "type", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 10,
                    "WriteCapacityUnits": 10,
                },
            )

        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "ResourceInUseException":
                log.debug("Table already exists", exc_info=e)
            else:
                raise
        else:
            log.debug("Called create_table")
            table.wait_until_exists()
            log.info("Created table " + cls.table_name)
            try:
                cls.dbclient.update_time_to_live(
                    TableName=cls.table_name,
                    TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"},
                )
            except botocore.exceptions.ClientError as e:
                log.error("Error setting TTL on table", exc_info=e)
            return table

    @classmethod
    def get_table(cls):
        try:
            cls.dbclient.describe_table(TableName=cls.table_name)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return cls.create_table()
            else:
                raise
        else:
            log.info(f"found {cls.table_name}")
            return cls.dbresource.Table(cls.table_name)

    @classmethod
    def setUpClass(cls):
        cls.region_name = environ.get("REGION")
        cls.table_name = environ.get("DDB_TABLE")
        cls.endpoint_url = environ.get("BOTO3_ENDPOINT")
        cls.dbresource = boto3.resource(
            "dynamodb", region_name=cls.region_name, endpoint_url=cls.endpoint_url
        )
        cls.dbclient = boto3.client(
            "dynamodb", region_name=cls.region_name, endpoint_url=cls.endpoint_url
        )

    def setUp(self):
        self.table = self.get_table()

    def tearDown(self):
        self.table.delete()

    def test_softhsm_sign_bytes(self):

        hsm_slot = config["hsm_slot"]
        hsm_user = config["hsm_username"]
        hsm_password = environ["HSM_PASSWORD"]
        hsm_pin = f"{hsm_user}:{hsm_password}"
        hsm_libfile = config["hsm_lib"]

        with HsmClient(slot=hsm_slot, pin=hsm_pin, pkcs11_lib=hsm_libfile) as c:
            private_handle, public_handle = discover_handles(c)
            _bytes = hex_to_bytes("012346789abcdef0")
            hashed_data = blake2b(_bytes, digest_size=32).digest()
            key_hash = "tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW"
            sig = c.sign(
                handle=private_handle, data=hashed_data, mechanism=HsmMech.ECDSA
            )
            assert c.verify(
                handle=public_handle,
                data=hashed_data,
                signature=sig,
                mechanism=HsmMech.ECDSA,
            )

    def test_sin(self):
        with app.test_client() as client:
            for req in valid_sig_reqs[0:3]:
                data = f'"{req[4]}"'
                raw_response = client.post(
                    "/keys/tz3aTaJ3d7Rh4yXpereo4yBm21xrs4bnzQvW", data=data
                )
                self.assertEqual(raw_response.status, "200 OK")
                response = json.loads(raw_response.data.decode())
                self.assertIn("signature", response)
