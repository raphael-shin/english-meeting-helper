from aws_cdk import Stack, Duration, CfnOutput, SecretValue, RemovalPolicy
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct
import aws_cdk as cdk


class AppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, target_region: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC with private subnets
        vpc = ec2.Vpc(self, "Vpc", max_azs=2, nat_gateways=1)
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        # ECR Repository for application image
        repository = ecr.Repository(
            self,
            "AppRepository",
            repository_name="english-meeting-helper",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            empty_on_delete=True,  # Updated from autoDeleteImages
        )

        # Custom header secret for CloudFront → ALB validation
        custom_header_secret = secretsmanager.Secret(
            self,
            "CustomHeaderSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"header":"X-Custom-Secret"}',
                generate_string_key="value",
                exclude_punctuation=True,
            ),
        )

        # Fargate service with PUBLIC ALB (CloudFront accessible)
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ApiService",
            cluster=cluster,
            cpu=1024,  # 1 vCPU
            memory_limit_mib=2048,  # 2 GB
            desired_count=1,
            public_load_balancer=True,  # Public ALB for CloudFront access
            health_check_grace_period=Duration.seconds(60),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    directory="../../",  # infra/cdk -> project root
                    file="infra/docker/api.Dockerfile",
                    platform=ecr_assets.Platform.LINUX_AMD64,  # Force AMD64 for Fargate
                ),
                container_port=8000,
                environment={
                    "AWS_REGION": target_region,
                    "PROVIDER_MODE": "AWS",
                    "TRANSCRIBE_LANGUAGE_CODE": "en-US",
                    "BEDROCK_TRANSLATION_FAST_MODEL_ID": "apac.anthropic.claude-haiku-4-5-20251001-v1:0",
                    "BEDROCK_TRANSLATION_HIGH_MODEL_ID": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
                    "BEDROCK_QUICK_TRANSLATE_MODEL_ID": "apac.anthropic.claude-haiku-4-5-20251001-v1:0",
                    "BEDROCK_CORRECTION_MODEL_ID": "apac.anthropic.claude-haiku-4-5-20251001-v1:0",
                },
            ),
        )

        # Configure ALB health check to use correct endpoint
        service.target_group.configure_health_check(
            path="/api/v1/health",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
        )

        # ALB idle timeout for WebSocket (60 minutes)
        cfn_load_balancer = service.load_balancer.node.default_child
        cfn_load_balancer.add_property_override(
            "LoadBalancerAttributes",
            [
                {
                    "Key": "idle_timeout.timeout_seconds",
                    "Value": "3600",
                }
            ],
        )

        # CloudFront Managed Prefix List IDs by region
        # https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/LocationsOfEdgeServers.html
        cloudfront_prefix_lists = {
            "us-east-1": "pl-3b927c52",
            "us-east-2": "pl-b6a144df",
            "us-west-1": "pl-4ea04527",
            "us-west-2": "pl-82a045eb",
            "ap-northeast-1": "pl-58a04531",
            "ap-northeast-2": "pl-22a6434b",
            "ap-south-1": "pl-9aa247f3",
            "ap-southeast-1": "pl-31a34658",
            "ap-southeast-2": "pl-b8a742d1",
            "eu-central-1": "pl-a3a144ca",
            "eu-west-1": "pl-4fa04526",
            "eu-west-2": "pl-93a247fa",
            "sa-east-1": "pl-5da64334",
        }
        
        prefix_list_id = cloudfront_prefix_lists.get(target_region)
        if not prefix_list_id:
            raise ValueError(f"CloudFront prefix list not found for region {target_region}")
        
        cloudfront_prefix_list = ec2.Peer.prefix_list(prefix_list_id)
        service.load_balancer.connections.allow_from(
            cloudfront_prefix_list,
            ec2.Port.tcp(80),
            "Allow CloudFront",
        )

        # Grant Bedrock permissions
        service.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    f"arn:aws:bedrock:{target_region}::foundation-model/*",
                    # Cross-region inference profiles (global.*, apac.*, etc.)
                    f"arn:aws:bedrock:{target_region}:{self.account}:inference-profile/*",
                ],
            )
        )

        # Grant Transcribe permissions
        service.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "transcribe:StartStreamTranscription",
                    "transcribe:StartStreamTranscriptionWebSocket",
                ],
                resources=["*"],
            )
        )

        # S3 bucket for web frontend
        web_bucket = s3.Bucket(
            self,
            "WebBucket",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # CloudFront Distribution with multiple origins
        alb_origin = origins.LoadBalancerV2Origin(
            service.load_balancer,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
            custom_headers={
                "X-Custom-Secret": custom_header_secret.secret_value_from_json(
                    "value"
                ).unsafe_unwrap(),
            },
        )

        # S3 Origin for web frontend
        s3_origin = origins.S3BucketOrigin.with_origin_access_control(web_bucket)

        distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            additional_behaviors={
                "/api/*": cloudfront.BehaviorOptions(
                    origin=alb_origin,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
                "/ws/*": cloudfront.BehaviorOptions(
                    origin=alb_origin,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
            },
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                )
            ],
            comment="English Meeting Helper (Web + API)",
        )

        # Deploy web frontend to S3 automatically
        web_deployment = s3deploy.BucketDeployment(
            self,
            "WebDeployment",
            sources=[s3deploy.Source.asset("../../apps/web/dist")],
            destination_bucket=web_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        # Outputs
        CfnOutput(
            self,
            "CloudFrontURL",
            value=f"https://{distribution.distribution_domain_name}",
            description="CloudFront Distribution URL (Web + API)",
        )
        CfnOutput(
            self,
            "WebBucketName",
            value=web_bucket.bucket_name,
            description="S3 Bucket for Web Frontend",
        )
        CfnOutput(
            self,
            "DistributionId",
            value=distribution.distribution_id,
            description="CloudFront Distribution ID",
        )
        CfnOutput(
            self,
            "CustomHeaderSecretArn",
            value=custom_header_secret.secret_arn,
            description="Custom Header Secret ARN (for ALB validation)",
        )
