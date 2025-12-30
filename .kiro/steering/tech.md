# Tech Stack & Commands

## Frontend (`apps/web`)
- React 18 + TypeScript (strict mode)
- Vite 5 for build/dev
- TailwindCSS for styling
- Vitest + React Testing Library for tests
- Web Audio API for mic capture (16kHz mono PCM)

## Backend (`apps/api`)
- Python 3.11+
- FastAPI + Uvicorn
- Pydantic v2 for models
- WebSocket for real-time audio/events
- AWS SDK: Transcribe Streaming, Bedrock (Nova/Claude)
- OpenAI SDK (alternative provider)

## Infrastructure (`infra/cdk`)
- AWS CDK v2 (Python)
- ECS Fargate + ALB
- DynamoDB (sessions/events tables)

## Shared Contracts (`packages/contracts`)
- JSON Schema definitions
- Auto-generated TypeScript and Python types

## Common Commands
```bash
# Install dependencies
npm install                    # Frontend + root
pip install -r apps/api/requirements.txt  # Backend

# Development
npm run dev:web               # Start frontend (localhost:5173)
npm run dev:api               # Start backend (localhost:8000)
docker-compose up             # Run both via Docker

# Testing
npm run test:web              # Frontend tests (vitest)
npm run test:api              # Backend tests (pytest)
npm run test:cdk              # CDK tests

# Build & Generate
npm run build:web             # Production build
npm run contracts:generate    # Regenerate TS/Python types from schemas

# CDK Deployment
cd infra/cdk && cdk deploy
```

## Environment Variables
Backend (`apps/api/.env`):
- `AWS_REGION`, `AWS_PROFILE`
- `BEDROCK_TRANSLATION_MODEL_ID`, `BEDROCK_QUICK_TRANSLATE_MODEL_ID`
- `TRANSCRIBE_LANGUAGE_CODE`
- `CORS_ORIGINS`

Frontend (`apps/web/.env`):
- `VITE_API_BASE_URL`, `VITE_WS_BASE_URL`
