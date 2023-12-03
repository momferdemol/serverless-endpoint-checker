#!/usr/bin/env python

import json
import logging
from os import environ
from typing import Any

from aws_lambda_typing.context import Context
from aws_lambda_typing.events import APIGatewayProxyEventV1
from boto3 import resource
from boto3.dynamodb.conditions import Key
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


def scan_table(table_name: str) -> list[dict[str, Any]]:
    table: Table = get_db_resource(table_name)
    response = table.scan(FilterExpression=Key("is_active").eq(True))

    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=Key("is_active").eq(True),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )

    records: list[dict[str, Any]] = []
    for item in response.get("Items", []):  # type: ignore
        created_at = int(item["created_at"])
        records.append(
            {
                "id": item["id"],
                "target_url": item["target_url"],
                "is_active": item["is_active"],
                "created_at": created_at,
            }
        )

    return records


def main(event: APIGatewayProxyEventV1, context: Context):
    try:
        table_name = get_db_table_name()
        records = scan_table(table_name)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": records}),
        }
    except ClientError as err:
        logger.error(f"Error: {err}")
        return {
            "statusCode": 418,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Whoops! something went wrong"}),
        }
