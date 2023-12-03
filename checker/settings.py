# checker/settings.py

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    enivronment: str = Field("dev", alias="ENVIRONMENT")
    owner: str = Field("Momfer", alias="OWNER")
    component: str = Field("endpoint-checker", alias="COMPONENT")
    account: str = Field(alias="AWS_ACCOUNT")
    region: str = Field("eu-west-1", alias="AWS_REGION")

    model_config = SettingsConfigDict(env_file=".env")


def get_settings() -> Settings:
    settings = Settings()  # type: ignore
    return settings


def get_stack_name() -> str:
    settings = get_settings()
    prefix = f"{settings.enivronment[0]}-{settings.owner}"
    return f"{prefix}-stack-{settings.component}".lower()


def get_resource_name(resource: str, suffix: str) -> str:
    env = get_settings().enivronment[0]
    owner = get_settings().owner
    component = get_settings().component
    return f"{env}-{owner}-{resource}-{component}{suffix}".lower()
