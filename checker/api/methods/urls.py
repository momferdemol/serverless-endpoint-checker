# checker/api/methods/urls_post.py

from typing import cast

from aws_cdk import Duration
from aws_cdk import aws_apigateway as apigtw
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk.aws_lambda_python_alpha import PythonLayerVersion
from aws_cdk.aws_logs import RetentionDays
from constructs import Construct
from typing_extensions import Self

from checker.settings import get_resource_name, get_settings

settings = get_settings()


class UrlsMethods(Construct):
    def __init__(
        self: Self,
        scope: Construct,
        id: str,
        api_root: apigtw.Resource,
        db: dynamodb.Table,
        layer: PythonLayerVersion,
    ) -> None:
        super().__init__(scope, id)

        self.api_root = api_root
        self.db = db
        self.layer = layer
        self.role = self._build_lambda_role()
        self.endpoint = self._build_api_endpoint()
        self.post_method = self._build_post_lambda_integration()
        self.get_method = self._build_get_lambda_integration()
        self.put_method = self._build_put_lambda_integration()

    def _build_lambda_role(self: Self) -> iam.Role:
        role: iam.Role = iam.Role(
            self,
            "role",
            role_name=get_resource_name("role", "-api"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "dynamodb_db": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "dynamodb:PutItem",
                                "dynamodb:GetItem",
                                "dynamodb:UpdateItem",
                                "dynamodb:Scan",
                            ],
                            resources=[self.db.table_arn],
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

    def _build_api_endpoint(self: Self) -> apigtw.Resource:
        return self.api_root.add_resource("urls")

    def _build_post_lambda_integration(self: Self) -> None:
        function: _lambda.Function = _lambda.Function(
            self,
            "post",
            function_name=get_resource_name("lambda", "-urls-post"),
            runtime=_lambda.Runtime.PYTHON_3_10,
            architecture=_lambda.Architecture.X86_64,
            code=_lambda.Code.from_asset(".build/lambdas"),
            handler="service.handlers.urls_post.main",
            layers=[self.layer],
            environment={
                "TABLE_NAME": self.db.table_name,
            },
            tracing=_lambda.Tracing.ACTIVE,
            retry_attempts=0,
            timeout=Duration.seconds(10),
            memory_size=128,
            role=cast(iam.IRole, self.role),
            log_retention=RetentionDays.ONE_DAY,
        )

        # POST /api/urls/
        self.endpoint.add_method(
            http_method="POST",
            integration=apigtw.LambdaIntegration(handler=cast(_lambda.IFunction, function)),
        )

    def _build_get_lambda_integration(self: Self) -> None:
        function: _lambda.Function = _lambda.Function(
            self,
            "get",
            function_name=get_resource_name("lambda", "-urls-get"),
            runtime=_lambda.Runtime.PYTHON_3_10,
            architecture=_lambda.Architecture.X86_64,
            code=_lambda.Code.from_asset(".build/lambdas"),
            handler="service.handlers.urls_get.main",
            layers=[self.layer],
            environment={
                "TABLE_NAME": self.db.table_name,
            },
            tracing=_lambda.Tracing.ACTIVE,
            retry_attempts=0,
            timeout=Duration.seconds(10),
            memory_size=128,
            role=cast(iam.IRole, self.role),
            log_retention=RetentionDays.ONE_DAY,
        )

        # GET /api/urls/
        self.endpoint.add_method(
            http_method="GET",
            integration=apigtw.LambdaIntegration(handler=cast(_lambda.IFunction, function)),
        )

    def _build_put_lambda_integration(self: Self) -> None:
        function: _lambda.Function = _lambda.Function(
            self,
            "put",
            function_name=get_resource_name("lambda", "-urls-put"),
            runtime=_lambda.Runtime.PYTHON_3_10,
            architecture=_lambda.Architecture.X86_64,
            code=_lambda.Code.from_asset(".build/lambdas"),
            handler="service.handlers.urls_put.main",
            layers=[self.layer],
            environment={
                "TABLE_NAME": self.db.table_name,
            },
            tracing=_lambda.Tracing.ACTIVE,
            retry_attempts=0,
            timeout=Duration.seconds(10),
            memory_size=128,
            role=cast(iam.IRole, self.role),
            log_retention=RetentionDays.ONE_DAY,
        )

        # Resource /api/urls/{id}
        urls_put = self.endpoint.add_resource("{id}")

        # PUT /api/urls/{id}
        urls_put.add_method(
            http_method="PUT",
            integration=apigtw.LambdaIntegration(handler=cast(_lambda.IFunction, function)),
        )
