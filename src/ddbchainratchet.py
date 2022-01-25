
import json
import boto3
import decimal
from botocore.exceptions import ClientError
import logging
import uuid

from werkzeug.exceptions import abort
from dyndbmutex.dyndbmutex import DynamoDbMutex, AcquireLockFailedError

from src.chainratchet import ChainRatchet

logging.getLogger('dyndbmutex').setLevel(logging.CRITICAL)

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
            logging.error("DynamoDB error during CreateItem: " +
                          err.response['Error']['Message'])
            abort(500, "DB error")
        else: 
            logging.debug("PutItem succeeded: " +
                          json.dumps(put_response, indent=4))
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
            logging.error("DynamoDB error during UpdateItem: " +
                          err.response['Error']['Message'])
            abort(500, "DB error")
        else:
            logging.debug("UpdateItem succeeded: " +
                          json.dumps(response, indent=4, cls=DecimalEncoder))
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
            logging.error("DynamoDB error during GetItem: " +
                          err.response['Error']['Message'])
            abort(500, "DB error")

        if 'Item' not in get_response:
            return self.CreateItem('type', sig_type, level, round)

        item = get_response['Item']
        logging.debug("GetItem succeeded: " +
                      json.dumps(get_response, indent=4, cls=DecimalEncoder))
        self.lastlevel = item['lastblock']
        if 'lastround' in item:
            self.lastround = item['lastround']
        else:
            self.lastround = 0

        logging.debug(f"Current sig is {self.lastlevel}/{self.lastround}")

        super().check(sig_type, level, round)

        return self.UpdateItem(sig_type, level, round)

    def check(self, sig_type, level=0, round=0):
        # This code acquires a mutex lock using:
        #      https://github.com/chiradeep/dyndb-mutex
        # generate a unique name for this process/thread
        my_name = str(uuid.uuid4()).split("-")[0]
        m = DynamoDbMutex(sig_type, holder=my_name, timeoutms=60 * 1000,
                          region_name=self.REGION)
        try:
            with m:
                return self.check_locked(sig_type, level, round)
        except AcquireLockFailedError:
            abort(503, "Failed to obtain DB lock")

