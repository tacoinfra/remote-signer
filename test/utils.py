import logging
from pathlib import Path

import botocore

log = logging.getLogger(__name__)


def is_docker():
    """
    True if running in docker.
    """
    cgroup = Path("/proc/self/cgroup")
    return (
        Path("/.dockerenv").is_file()
        or cgroup.is_file()
        and "docker" in cgroup.read_text()
    )


def create_table(dbresource, dbclient, table_name):
    """
    Create a dynamodb table.
    """
    try:
        table = dbresource.create_table(
            TableName=table_name,
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
        log.info("Created table " + table_name)
        try:
            dbclient.update_time_to_live(
                TableName=table_name,
                TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"},
            )
        except botocore.exceptions.ClientError as e:
            log.error("Error setting TTL on table", exc_info=e)
        return table


def get_table(dbresource, dbclient, table_name):
    """
    Get a dynamodb table, creating if doesn't exist.
    """
    try:
        dbclient.describe_table(TableName=table_name)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return create_table(dbresource, dbclient, table_name)
        else:
            raise
    else:
        log.info(f"found {table_name}")
        return dbresource.Table(table_name)
