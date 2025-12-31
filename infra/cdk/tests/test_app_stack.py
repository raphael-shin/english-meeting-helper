import aws_cdk as cdk
from aws_cdk import assertions

from stacks.app_stack import AppStack


def test_stack_resources() -> None:
    app = cdk.App()
    stack = AppStack(app, "TestStack")
    template = assertions.Template.from_stack(stack)

    # Core resources
    template.resource_count_is("AWS::ECS::Service", 1)
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)
    
    # IAM permissions for Bedrock and Transcribe
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                        "Effect": "Allow",
                    }),
                    assertions.Match.object_like({
                        "Action": ["transcribe:StartStreamTranscription", "transcribe:StartStreamTranscriptionWebSocket"],
                        "Effect": "Allow",
                    }),
                ])
            }
        }
    )
