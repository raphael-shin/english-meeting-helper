import aws_cdk as cdk
from aws_cdk import assertions

from stacks.app_stack import AppStack


def test_stack_resources() -> None:
    app = cdk.App()
    stack = AppStack(app, "TestStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::DynamoDB::Table", 2)
    template.resource_count_is("AWS::ECS::Service", 1)
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)
