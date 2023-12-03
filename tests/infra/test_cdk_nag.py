# tests/infra/test_cdk_nag.py

from aws_cdk import App, Aspects, Environment
from aws_cdk.assertions import Annotations, Match
from aws_cdk.cx_api import SynthesisMessage
from cdk_nag import AwsSolutionsChecks, NagSuppressions

from checker.settings import get_settings, get_stack_name
from checker.stack import Checker

settings = get_settings()


def test_cdk_nag_stack() -> None:
    app = App()

    stack = Checker(
        app,
        get_stack_name(),
        description="CDK synth test",
        env=Environment(account=settings.account, region=settings.region),
    )
    Aspects.of(stack).add(AwsSolutionsChecks(verbose=True))
    NagSuppressions.add_stack_suppressions(
        stack=stack,
        suppressions=[
            {"id": "AwsSolutions-APIG3", "reason": "Do not need waf for non-production env"},
            {"id": "AwsSolutions-IAM5", "reason": "wildcard in policy acceptable for stack"},
            {"id": "AwsSolutions-L1", "reason": "lambda should be pinned to version"},
        ],
    )

    warnings = Annotations.from_stack(stack).find_warning(
        "*", Match.string_like_regexp("AwsSolutions-.*")
    )

    warning_findings = process_findings(warnings)
    if warning_findings:
        raise AssertionError("\n".join(map(str, warning_findings)))

    errors = Annotations.from_stack(stack).find_error(
        "*", Match.string_like_regexp("AwsSolutions-.*")
    )

    error_findings = process_findings(errors)
    if error_findings:
        raise AssertionError("\n".join(map(str, error_findings)))


def process_findings(findings: list[SynthesisMessage]) -> list[str]:
    process_findings: list[str] = []
    for finding in findings:
        if isinstance(finding.entry.data, str):
            process_findings.append(f"{finding.id} ==>\n{finding.entry.data}")
    return process_findings
