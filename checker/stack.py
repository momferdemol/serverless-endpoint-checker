from aws_cdk import Environment, Stack, Tags
from constructs import Construct
from typing_extensions import Self, TypedDict, Unpack

from checker.rest_api import RestApi
from checker.settings import get_settings

settings = get_settings()


class Kwargs(TypedDict):
    env: Environment
    description: str


class Checker(Stack):
    def __init__(self: Self, scope: Construct, id: str, **kwargs: Unpack[Kwargs]) -> None:
        super().__init__(scope, id, **kwargs)

        self.api = RestApi(self, id="restapi")

        Tags.of(self).add("createdBy", settings.owner)
