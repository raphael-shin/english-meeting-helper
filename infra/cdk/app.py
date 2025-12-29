import aws_cdk as cdk

from stacks.app_stack import AppStack

app = cdk.App()
AppStack(app, "EnglishMeetingHelperStack")
app.synth()
