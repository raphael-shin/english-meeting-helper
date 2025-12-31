#!/bin/bash
set -e

echo "🚀 Deploying English Meeting Helper to AWS..."

# 1. Build web frontend
echo "📦 Building web frontend..."
cd apps/web
npx vite build
cd ../..

# 2. Deploy CDK stack
echo "☁️  Deploying CDK stack..."
cd infra/cdk
TYPEGUARD_DISABLE=1 cdk deploy --all --require-approval=never

echo "✅ Deployment complete!"
echo "🌐 Check CloudFront URL in the output above"
