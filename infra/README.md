# Infrastructure

This directory contains deployment and container assets.

## Docker
- `infra/docker/api.Dockerfile`
- `infra/docker/web.Dockerfile`

Run the full stack from the repo root:
```bash
AWS_PROFILE=your-profile docker-compose up
```

## CDK (AWS)
- `infra/cdk`: AWS CDK v2 (Python)
- Config: `infra/cdk/cdk.context.json`

### Architecture
```
CloudFront (Single Distribution)
├─ / → S3 (Web Frontend)
├─ /api/* → ALB → Fargate (API)
└─ /ws/* → ALB → Fargate (WebSocket)
```

### Setup
```bash
cd infra/cdk
pip install -r requirements.txt
cdk bootstrap  # First time only
```

### Deploy

**1. Build Web Frontend**
```bash
cd apps/web
npx vite build
```

**2. Deploy Infrastructure**
```bash
cd infra/cdk
TYPEGUARD_DISABLE=1 cdk deploy --all --require-approval=never
```

**3. Get CloudFront URL**
```bash
# Output: CloudFrontURL
# Example: https://d1234567890.cloudfront.net
```

### Update Deployment
```bash
# Rebuild web with new changes
cd apps/web
npx vite build

# Redeploy (automatically uploads to S3 and invalidates CloudFront)
cd ../../infra/cdk
TYPEGUARD_DISABLE=1 cdk deploy --all --require-approval=never
```

### Destroy
```bash
cd infra/cdk
cdk destroy --all
```

### Notes
- ALB idle timeout: 3600s (60 minutes) for WebSocket support
- CloudFront restricts ALB access via Prefix List + Custom Header
- S3 bucket auto-deploys web assets on CDK deploy
- Region: `ap-northeast-2` (hardcoded in `app.py`)
