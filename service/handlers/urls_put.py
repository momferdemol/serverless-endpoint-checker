#!/usr/bin/env python

import json
import logging
from os import environ

from aws_lambda_typing.context import Context
from aws_lambda_typing.events import APIGatewayProxyEventV1
from boto3 import resource
from botocore.exceptions import ClientError
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_db_table_name() -> str:
    table_name = str(environ.get("TABLE_NAME"))
    logger.info(f"Loaded dynamodb table: {table_name}")
    return table_name


def get_db_resource(table_name: str) -> Table:
    logger.info(f"Opening connection to dynamodb table: {table_name}")
    dynamodb: DynamoDBServiceResource = resource("dynamodb")
    return dynamodb.Table(table_name)


def update_item(table_name: str, id: str, is_active: bool) -> bool:
    try:
        table: Table = get_db_resource(table_name)
        logger.info(f"Update item in dynamodb table with id: {id}")
        table.update_item(
            Key={"id": id},
            UpdateExpression="""SET
                is_active = :is_active""",
            ExpressionAttributeValues={":is_active": is_active},
        )
        return True
    except ClientError as err:
        logger.error(f"Error: {err}")
        return False


def main(event: APIGatewayProxyEventV1, context: Context):
    if not event["pathParameters"]:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Id is missing from request"}),
        }

    if not event["body"]:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Body is missing from request"}),
        }

    id = event["pathParameters"]["id"]
    data = json.loads(event["body"])
    table_name = get_db_table_name()

    if update_item(table_name, id, data["is_active"]):
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
