#!/usr/bin/env python

import json
import logging
import uuid
from datetime import datetime
from os import environ

from aws_lambda_typing.context import Context
from aws_lambda_typing.events import APIGatewayProxyEventV1
from boto3 import resource
from botocore.exceptions import ClientError
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table
from pydantic import BaseModel, ValidationError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Endpoint(BaseModel):
    id: str
    target_url: str
    is_active: bool
    created_at: int


def get_db_table_name() -> str:
    table_name = str(environ.get("TABLE_NAME"))
    logger.info(f"Loaded dynamodb table: {table_name}")
    return table_name


def get_db_resource(table_name: str) -> Table:
    logger.info(f"Opening connection to dynamodb table: {table_name}")
    dynamodb: DynamoDBServiceResource = resource("dynamodb")
    return dynamodb.Table(table_name)


def get_uuid() -> str:
    identifier = str(uuid.uuid4())
    logger.info(f"New identifier generated: {identifier}")
    return identifier


def get_unix_time() -> int:
    timestamp = int(datetime.utcnow().timestamp())
    logger.info(f"New timestamp generated: {timestamp}")
    return timestamp


def add_item(table_name: str, target_url: str) -> bool:
    try:
        entry = Endpoint(
            target_url=target_url,
            id=get_uuid(),
            is_active=True,
            created_at=get_unix_time(),
        )
        table: Table = get_db_resource(table_name)
        logger.info(f"Add item to dynamodb table with id: {entry.id}")
        table.put_item(Item=entry.model_dump())
        return True
    except (ClientError, ValidationError) as err:
        logger.error(f"Error: {err}")
        return False


def main(event: APIGatewayProxyEventV1, context: Context):
    if not event["body"]:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Body is missing from request"}),
        }

    data = json.loads(event["body"])
    table_name = get_db_table_name()

    if add_item(table_name, data["target_url"]):
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Successful"}),
        }

    else:
        return {
            "statusCode": 418,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Whoops! something went wrong"}),
        }
