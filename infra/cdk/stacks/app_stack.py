from aws_cdk import Stack
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from constructs import Construct


class AppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "Vpc", max_azs=2)
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ApiService",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(
                    "public.ecr.aws/docker/library/python:3.11-slim"
                ),
                container_port=8000,
            ),
        )

        sessions_table = dynamodb.Table(
            self,
            "MeetingSessions",
            partition_key=dynamodb.Attribute(
                name="sessionId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        events_table = dynamodb.Table(
            self,
            "MeetingEvents",
            partition_key=dynamodb.Attribute(
                name="sessionId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="tsSeq", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        sessions_table.grant_read_write_data(service.task_definition.task_role)
        events_table.grant_read_write_data(service.task_definition.task_role)
