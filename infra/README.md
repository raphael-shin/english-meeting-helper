# Infrastructure (CDK)

## Prerequisites
- Python 3.11+
- AWS CDK v2 CLI (`npm i -g aws-cdk`)
- AWS credentials configured (`aws configure`)

## Setup
```bash
cd infra/cdk
poetry install  # or: pip install -r requirements.txt
cdk bootstrap
```

## Synthesize
```bash
cd infra/cdk
cdk synth
```

## Deploy
```bash
cd infra/cdk
cdk deploy
```

## Notes
- This stack is a placeholder for ECS Fargate + ALB + DynamoDB (sessions/events).
- Update resource definitions before production use.
