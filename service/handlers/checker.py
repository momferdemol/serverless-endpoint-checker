#!/usr/bin/env python

import json
import logging
from http.client import HTTPConnection
from os import environ
from urllib.parse import urlparse

from aws_lambda_typing.context import Context
from aws_lambda_typing.events import EventBridgeEvent
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


def scan_table(table_name: str) -> list[str]:
    table: Table = get_db_resource(table_name)
    response = table.scan(FilterExpression=Key("is_active").eq(True))

    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=Key("is_active").eq(True),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )

    urls: list[str] = []
    for item in response.get("Items", []):  # type: ignore
        urls.append(item["target_url"])  # type: ignore
    return urls


def endpoint_is_online(url: str, timeout: int = 3) -> bool:
    error = Exception("unknown error")
    parser = urlparse(url)
    host = parser.netloc or parser.path.split("/")[0]
    for port in (80, 443):
        connection = HTTPConnection(host=host, port=port, timeout=timeout)
        try:
            connection.request("HEAD", "/")
            return True
        except Exception as err:
            error = err
        finally:
            connection.close()
    raise error


def synchronous_check(urls: list[str]) -> None:
    for url in urls:
        error = ""
        try:
            result = endpoint_is_online(url)
        except Exception as err:
            result = False
            error = str(err)
        display_check_result(result, url, error)


def display_check_result(result: bool, url: str, error: str) -> None:
    if result:
        logger.info(f"The status of '{url}' is: OK ")
    else:
        logger.error(f"The status of '{url}' is: NOT OK \n '{error}' ")


def main(event: EventBridgeEvent, context: Context):
    try:
        table_name = get_db_table_name()
        urls = scan_table(table_name)
        synchronous_check(urls)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Success"}),
        }
    except ClientError as err:
        logger.error(f"Error: {err}")
        return {
            "statusCode": 418,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Whoops! something went wrong"}),
        }
