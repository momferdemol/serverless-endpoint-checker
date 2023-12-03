# canary_infra/app.py

from aws_cdk import App, Environment

from checker.settings import get_settings, get_stack_name
from checker.stack import Checker

settings = get_settings()

app = App()

stack = Checker(
    app,
    get_stack_name(),
    description="Endpoint Checker",
    env=Environment(account=settings.account, region=settings.region),
)

app.synth()
