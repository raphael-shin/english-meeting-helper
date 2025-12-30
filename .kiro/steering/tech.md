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
- AWS SDK: Transcribe Streaming (with Partial Result Stabilization), Bedrock (Nova/Claude)
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
npm run test:web              # Frontend tests (vitest) - 15 tests
npm run test:api              # Backend tests (pytest) - 60 tests
npm run test:cdk              # CDK tests

# Build & Generate
npm run build:web             # Production build
npm run contracts:generate    # Regenerate TS/Python types from schemas

# CDK Deployment
cd infra/cdk && cdk deploy
```

## Environment Variables

### Backend (`apps/api/.env`)
**AWS Configuration:**
- `AWS_REGION` (default: ap-northeast-2)
- `AWS_PROFILE` (optional)

**Transcription:**
- `TRANSCRIBE_LANGUAGE_CODE` (default: en-US)
- `PROVIDER_MODE` (AWS or OPENAI)

**Translation Models:**
- `BEDROCK_TRANSLATION_FAST_MODEL_ID` (default: apac.anthropic.claude-haiku-4-5-20251001-v1:0)
- `BEDROCK_TRANSLATION_HIGH_MODEL_ID` (default: global.anthropic.claude-haiku-4-5-20251001-v1:0)
- `BEDROCK_QUICK_TRANSLATE_MODEL_ID` (default: apac.anthropic.claude-haiku-4-5-20251001-v1:0)
- `BEDROCK_CORRECTION_MODEL_ID` (default: apac.anthropic.claude-haiku-4-5-20251001-v1:0)

**OpenAI Configuration:**
- `OPENAI_API_KEY` (required for OPENAI mode)
- `OPENAI_STT_MODEL` (default: gpt-4o-transcribe)
- `OPENAI_TRANSLATION_MODEL` (default: gpt-4o-mini)
- `OPENAI_STT_LANGUAGE` (optional override)
- `OPENAI_COMMIT_INTERVAL_MS` (default: 1000)

**Google Configuration (Reserved):**
- `GOOGLE_PROJECT_ID`
- `GOOGLE_APPLICATION_CREDENTIALS`

**LLM Correction (Optional):**
- `LLM_CORRECTION_ENABLED` (default: false)
- `LLM_CORRECTION_BATCH_SIZE` (default: 5)
- `LLM_CORRECTION_INTERVAL_SECONDS` (default: 5)

**CORS:**
- `CORS_ORIGINS` (default: http://localhost:5173)

### Frontend (`apps/web/.env`)
- `VITE_API_BASE_URL` (default: http://localhost:8000)
- `VITE_WS_BASE_URL` (default: ws://localhost:8000)

## Key Technical Features
- **Partial Result Stabilization**: AWS Transcribe configured with "high" stability for faster finalization
- **Single Segment Finals**: No chunking - each Final transcript is one segment
- **Progressive Partial Updates**: Same segmentId maintained during partial streaming
- **Display Buffer**: Max 4 confirmed + 1 current segment in Live tab
- **Async Correction Queue**: Optional LLM-based correction with re-translation
