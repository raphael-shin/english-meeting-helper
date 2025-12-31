# English Meeting Helper

Real-time English meeting assistant for Korean speakers. Live transcription, EN→KO translation, Quick Translate (KO→EN), AI speaking suggestions, and on-demand meeting summary (Markdown).

## Key Features
- Live/History transcript UI with partial + final updates
- Context-aware EN→KO translation + Quick Translate (KO→EN)
- AI Suggestions panel with prompt control
- Meeting Summary (Markdown: 5-line summary, key points, optional action items)

## Screenshots
*(Add screenshots of the Meeting Panel, Settings, and Summary view here)*

## Monorepo Layout
- `apps/web`: React + TypeScript + Vite + Tailwind
- `apps/api`: FastAPI + WebSocket
- `packages/contracts`: JSON Schema → TS/Python types
- `infra/cdk`: AWS CDK (Python)
- `infra/docker`: Dockerfiles

## Local Development
### 0) Prerequisites
- Node.js 18+
- Python 3.11+

### 1) Dependencies
```bash
npm install
pip install -r apps/api/requirements.txt
```

### 2) Environment
```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env   # optional
```

### 3) Run
```bash
npm run dev:api
npm run dev:web
```

## Docker Compose
Prerequisites:
- `~/.aws/credentials` configured (or `AWS_PROFILE` set)
- `apps/api/.env` created

```bash
AWS_PROFILE=your-profile docker-compose up
```

Services:
- API: `http://localhost:8000`
- Web: `http://localhost:5173`

## Tests
```bash
npm run test:web
npm run test:api
npm run test:cdk
```

## AWS Deployment

### Prerequisites
- AWS CLI configured with credentials
- Node.js and Python 3.11+ installed
- CDK bootstrapped in target region

### CDK Context Configuration

Before deploying, create `infra/cdk/cdk.context.json` with your Bedrock model settings:

```bash
cp infra/cdk/cdk.context.json.example infra/cdk/cdk.context.json
```

**Configuration options:**

| Key | Description | Example |
|-----|-------------|---------|
| `bedrock.translationFastModelId` | Fast translation model (partial text) | `global.amazon.nova-lite-v1:0` |
| `bedrock.translationHighModelId` | High-quality translation model (final text) | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| `bedrock.quickTranslateModelId` | Quick Translate KO→EN model | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |

> **Note**: Use `global.*` prefix for cross-region inference. Available models depend on your AWS account's Bedrock access.

### Deploy to AWS

**Quick Deploy (Recommended)**
```bash
./deploy.sh
```

**Manual Deploy**

**1. Build Web Frontend**
```bash
cd apps/web
npx vite build
```

**2. Deploy with CDK**
```bash
cd infra/cdk
pip install -r requirements.txt
TYPEGUARD_DISABLE=1 cdk deploy --all --require-approval=never
```

> **Note**: `TYPEGUARD_DISABLE=1` is required due to a type checking issue in CDK's BucketDeployment with typeguard library.

**3. Access Application**
```bash
# CloudFront URL will be in the output
# Example: https://d1234567890.cloudfront.net
```

### Architecture
```
CloudFront (Single Distribution)
├─ / → S3 (Web Frontend)
├─ /api/* → ALB → Fargate (API)
└─ /ws/* → ALB → Fargate (WebSocket)
```

**Resources:**
- Fargate: 1 vCPU, 2 GB RAM
- ALB: Public with CloudFront Prefix List restriction
- S3: Static web hosting
- CloudFront: Global CDN with custom domain support
- Region: `ap-northeast-2` (Seoul)

See `infra/README.md` for detailed deployment instructions.

## Configuration (Quick)
- Provider mode: `PROVIDER_MODE=AWS|OPENAI`
- WebSocket: `/ws/v1/meetings/{sessionId}`
- API: `/api/v1`

See `apps/api/.env.example` for full backend settings and `apps/web/.env.example` for frontend.

## Docs
- Product/UX: `.kiro/steering/product.md`
- Architecture: `.kiro/steering/structure.md`
- Tech stack: `.kiro/steering/tech.md`
- WebSocket protocol: `.kiro/steering/websocket-protocol.md`
- Infra: `infra/README.md`

## Troubleshooting
- **Audio Issues**: Ensure your browser has permission to access the microphone.
- **API Errors**: Check if `PROVIDER_MODE` and API keys (AWS/OpenAI) are correctly set in `.env`.
- **WebSocket Disconnects**: Verify the `VITE_WS_BASE_URL` matches your backend URL.
