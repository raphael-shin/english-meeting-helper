import aws_cdk as cdk
import os

from stacks.app_stack import AppStack

app = cdk.App()

# Force ap-northeast-2 region
region = "ap-northeast-2"
account = os.environ.get("CDK_DEFAULT_ACCOUNT")

print(f"[DEBUG] Deploying to region: {region}, account: {account}")

AppStack(
    app,
    "EnglishMeetingHelperStack",
    target_region=region,
    env=cdk.Environment(
        account=account,
        region=region,
    ),
)
app.synth()
