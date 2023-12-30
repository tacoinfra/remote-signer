
import logging

import boto3
from botocore.exceptions import ClientError
from werkzeug.exceptions import abort

from tezos_signer import ChainRatchet


class DDBChainRatchet(ChainRatchet):

    def __init__(self, config):
        self.REGION = config.get_aws_region()
        kwargs = {"region_name":self.REGION}
        url = config.get_boto3_endpoint()
        if url is not None:
            kwargs.update({"endpoint_url": url})
        self.dynamodb = boto3.resource('dynamodb', **kwargs)
        self.table = self.dynamodb.Table(config.get_ddb_table())

    def check(self, sig_type, level=0, round=0):
        try:
            self.table.put_item(
                Item={
                    'sig_type': sig_type,
                    'lastblock': level,
                    'lastround': round,
                },
                ConditionExpression=
                    "attribute_not_exists(sig_type) OR " +
                        "(lastblock < :l OR " +
                            "( lastblock = :l AND lastround < :r)" +
                        ")",
                ExpressionAttributeValues={
                    ':l': level,
                    ':r': round
                }
            )
        except ClientError as err:
            code = err.response['Error']['Code']
            if code == "ConditionalCheckFailedException":
                abort(410, "Ratchet will not sign: " + 
                      err.response['Error']['Message'])
            logging.error("DynamoDB error during UpdateItem: " +
                          err.response['Error']['Message'])
            abort(500, "DB error")
