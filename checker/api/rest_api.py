# checker/api/rest_api.py

from typing import cast

from aws_cdk import CfnOutput, Duration, RemovalPolicy
from aws_cdk import aws_apigateway as apigtw
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_scheduler as scheduler
from aws_cdk.aws_lambda_python_alpha import PythonLayerVersion
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct
from typing_extensions import Self

from checker.api.methods.urls import UrlsMethods
from checker.db import Database
from checker.settings import get_resource_name, get_settings

settings = get_settings()


class RestApi(Construct):
    def __init__(self: Self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)

        self.api_db = Database(self, id="database")
        self.layer = self._build_common_layer()
        self.rest_api = self._build_api_gtw()
        self.api_root = self._build_api_root()
        self.urls = UrlsMethods(
            self, id="logic", api_root=self.api_root, db=self.api_db.table, layer=self.layer
        )
        self.service_role = self._build_lambda_role_service()
        self.service = self._build_service_lambda()
        self.scheduler_role = self._build_scheduler_role()
        self.scheduler = self._build_scheduler()

    def _build_common_layer(self: Self) -> PythonLayerVersion:
        common: PythonLayerVersion = PythonLayerVersion(
            self,
            "common",
            entry=".build/common_layer",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
            compatible_architectures=[_lambda.Architecture.X86_64],
            description="Enpoint checker library",
            layer_version_name=get_resource_name("lambda", "layer"),
            removal_policy=RemovalPolicy.DESTROY,
        )

        return common

    def _build_api_gtw(self: Self) -> apigtw.RestApi:
        rest_api: apigtw.RestApi = apigtw.RestApi(
            self,
            "apigtw",
            rest_api_name="Rest API",
            description="This service handles /api requests",
            deploy_options=apigtw.StageOptions(
                stage_name=settings.enivronment, throttling_rate_limit=2, throttling_burst_limit=10
            ),
            cloud_watch_role=False,
        )
        CfnOutput(self, id="RestApiUrl", value=rest_api.url).override_logical_id("RestApiURL")

        return rest_api

    def _build_api_root(self: Self) -> apigtw.Resource:
        return self.rest_api.root.add_resource("api").add_resource("v1")

    def _build_lambda_role_service(self: Self) -> iam.Role:
        role: iam.Role = iam.Role(
            self,
            "service-role",
            role_name=get_resource_name("role", "-service"),
            assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
            inline_policies={
                "scheduler": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "foo:bar",
                                "foo:bar",
                            ],
                            resources=[self.api_db.table.table_arn],
                            effect=iam.Effect.ALLOW,
                        )
                    ]
                ),
                "cloudwatch_logs": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=["*"],
                            effect=iam.Effect.ALLOW,
                        )
                    ]
                ),
            },
        )

        return role

    def _build_service_lambda(self: Self) -> _lambda.Function:
        function: _lambda.Function = _lambda.Function(
            self,
            "service",
            function_name=get_resource_name("lambda", "-service"),
            runtime=_lambda.Runtime.PYTHON_3_10,
            architecture=_lambda.Architecture.X86_64,
            code=_lambda.Code.from_asset(".build/lambdas"),
            handler="service.handlers.urls_get.main",
            layers=[self.layer],
            environment={
                "TABLE_NAME": self.api_db.table.table_arn,
            },
            tracing=_lambda.Tracing.ACTIVE,
            retry_attempts=0,
            timeout=Duration.seconds(10),
            memory_size=128,
            role=cast(iam.IRole, self.service_role),
            log_retention=RetentionDays.ONE_DAY,
        )

        return function

    def _build_scheduler_role(self: Self) -> iam.Role:
        role: iam.Role = iam.Role(
            self,
            "scheduler-role",
            role_name=get_resource_name("role", "-scheduler"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "dynamodb_db": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:Scan",
                            ],
                            resources=[self.api_db.table.table_arn],
                            effect=iam.Effect.ALLOW,
                        )
                    ]
                ),
                "cloudwatch_logs": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=["*"],
                            effect=iam.Effect.ALLOW,
                        )
                    ]
                ),
            },
        )

        return role

    def _build_scheduler(self: Self) -> scheduler.CfnSchedule:
        schedule: scheduler.CfnSchedule = scheduler.CfnSchedule(
            self,
            "scheduler",
            name=get_resource_name("event", "-scheduler"),
            description="Schedule to check endpoints",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            schedule_expression="rate(1 minute)",
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.service.function_arn,
                role_arn=self.scheduler_role.role_arn,
            ),
        )

        return schedule
