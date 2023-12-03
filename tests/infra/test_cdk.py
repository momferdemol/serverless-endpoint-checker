# tests/infra/test_cdk.py

from aws_cdk import App, Environment
from aws_cdk.assertions import Template

from checker.settings import get_settings, get_stack_name
from checker.stack import Checker

settings = get_settings()


def test_synthesizes_stack_properly() -> None:
    app = App()

    stack = Checker(
        app,
        get_stack_name(),
        description="CDK synth test",
        env=Environment(account=settings.account, region=settings.region),
    )
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::DynamoDB::Table", 1)
    template.resource_count_is("AWS::IAM::Role", 2)
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)
    template.resource_count_is("AWS::Lambda::Function", 2)
