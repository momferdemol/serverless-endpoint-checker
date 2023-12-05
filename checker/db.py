from aws_cdk import CfnOutput, RemovalPolicy
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct
from typing_extensions import Self


class Database(Construct):
    def __init__(self: Self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        self.table: dynamodb.Table = self._build_db_table()

    def _build_db_table(self: Self) -> dynamodb.Table:
        table = dynamodb.Table(
            self,
            "table",
            table_name="endpoint-checker-table",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY,
        )
        CfnOutput(self, id="DbTableName", value=table.table_name).override_logical_id("DbTableName")

        return table
