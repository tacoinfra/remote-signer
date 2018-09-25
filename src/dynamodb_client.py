#########################################################
# Written by Luke Youngblood, luke@blockscale.net
# Copyright (c) 2018 Blockscale LLC
# released under the MIT license
#########################################################

from __future__ import print_function # Python 2/3 compatibility
import json
import boto3
import os
import time
import decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import logging

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

class DynamoDBClient:

    def __init__(self, ddb_region, ddb_table, sig_type, level):
        self.REGION = ddb_region
        self.DDB_TABLE = ddb_table
        self.dynamodb = boto3.resource('dynamodb', region_name=self.REGION)
        self.table = self.dynamodb.Table(self.DDB_TABLE)
        self.sig_type = sig_type
        self.level = level

    def CreateItem(self, keyname, key, value):
        try:
            put_response = self.table.put_item(
                Item={
                    keyname: key,
                    'lastblock': value
                }
            )
        except ClientError as err:
            logging.error(err.response['Error']['Message'])
            return False
        else: 
            logging.info("PutItem succeeded:")
            logging.info(json.dumps(put_response, indent=4))
            return True

    def UpdateItem(self, key, value):
        try:
            response = self.table.update_item(
                Key={
                    'type': key
                },
                UpdateExpression="set lastblock = :d",
                ExpressionAttributeValues={
                    ':d': value
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

    def check_double_signature(self):
        try:
            get_response = self.table.get_item(
                Key={
                    'type': self.sig_type
                },
                ConsistentRead=True
            )
        except ClientError as err:
            logging.error(err.response['Error']['Message'])
            safe_to_sign = False
        else: # get_item didn't fail, but did we get an item?
            try:
              item = get_response['Item']
            except KeyError: # if get_response is empty, create an item in table
                if self.CreateItem('type', self.sig_type, self.level):
                    safe_to_sign = True
                else:
                    safe_to_sign = False
            else:
                logging.info("GetItem succeeded:")
                logging.info(json.dumps(get_response, indent=4, cls=DecimalEncoder))
                blocknum = get_response['Item']['lastblock']
                logging.info("Current block height is " + str(blocknum))
                if self.level <= blocknum:
                    logging.error("Signature has already been generated for this block, exiting to prevent double "+self.sig_type)
                    safe_to_sign = False
                else:
                    if self.UpdateItem(self.sig_type, self.level):
                        safe_to_sign = True
                    else:
                        logging.error(self.sig_type + " signature for block number " + str(self.level) + " has not already been generated, but the update failed")
                        safe_to_sign = False
        return safe_to_sign
