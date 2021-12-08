
from __future__ import print_function # Python 2/3 compatibility
import json
import boto3
import os
import time
import decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import logging
import uuid

from dyndbmutex.dyndbmutex import DynamoDbMutex

from src.chainratchet import ChainRatchet


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

class DDBChainRatchet(ChainRatchet):

    def __init__(self, ddb_region, ddb_table):
        self.REGION = ddb_region
        self.DDB_TABLE = ddb_table
        self.dynamodb = boto3.resource('dynamodb', region_name=self.REGION)
        self.table = self.dynamodb.Table(self.DDB_TABLE)

    def CreateItem(self, keyname, key, level, round):
        try:
            put_response = self.table.put_item(
                Item={
                    keyname: key,
                    'lastblock': level,
                    'lastround': round
                }
            )
        except ClientError as err:
            logging.error(err.response['Error']['Message'])
            return False
        else: 
            logging.info("PutItem succeeded:")
            logging.info(json.dumps(put_response, indent=4))
            return True

    def UpdateItem(self, key, level, round):
        try:
            response = self.table.update_item(
                Key={
                    'type': key
                },
                UpdateExpression="set lastblock = :l, lastround = :r",
                ExpressionAttributeValues={
                    ':l': level,
                    ':r': round
                },
                ReturnValues="UPDATED_NEW"
            )
        except ClientError as err:
            logging.error(err.response['Error']['Message'])
            return False
        else:
            logging.info("UpdateItem succeeded:")
            logging.info(json.dumps(response, indent=4, cls=DecimalEncoder))
            return True

    def check_locked(self, sig_type, level=0, round=0):
        try:
            get_response = self.table.get_item(
                Key={
                    'type': sig_type
                },
                ConsistentRead=True
            )
        except ClientError as err:
            logging.error(err.response['Error']['Message'])
            return False

        if 'Item' not in get_response:
            return self.CreateItem('type', sig_type, level, round)

        item = get_response['Item']
        logging.info("GetItem succeeded:")
        logging.info(json.dumps(get_response, indent=4, cls=DecimalEncoder))
        self.lastlevel = item['lastblock']
        if 'lastround' in item:
            self.lastround = item['lastround']
        else:
            self.lastround = 0
        logging.info(f"Current sig is {self.lastlevel}/{self.lastround}")
        if not super().check(sig_type, level, round):
            logging.error("Signature has already been generated for this block, exiting to prevent double "+ sig_type)
            return False
        else:
            if self.UpdateItem(sig_type, level, round):
                return True

            logging.error(sig_type + " signature for block number " + str(level) + " has not already been generated, but the update failed")
            return False

    def check(self, sig_type, level=0, round=0):
        # This code acquires a mutex lock using:
        #      https://github.com/chiradeep/dyndb-mutex
        # generate a unique name for this process/thread
        my_name = str(uuid.uuid4()).split("-")[0]
        m = DynamoDbMutex(sig_type, holder=my_name, timeoutms=60 * 1000,
                          region_name=self.REGION)
        with m:
            return self.check_locked(sig_type, level, round)
