# English Meeting Helper

## Overview
English Meeting Helper는 실시간 영어 회의를 지원하는 웹 애플리케이션입니다. Live/History 탭 전사 UI, 2문장 단위 캡션/번역, 빠른 한→영 번역, AI 질문 제안을 제공합니다.

## Key Features
- Live/History 탭 기반 전사 UI (partial/final 표시, Live는 최근 확정 자막 일부 유지)
- 영어 → 한국어 실시간 번역 (partial은 2문장 단위 캡션 기준)
- Quick Translate (한국어 → 영어)
- AI Suggestions (회의 맥락 + 사용자 프롬프트 기반, 카드 내 Settings에서 프롬프트 조정)
- 마이크 설정 및 전사 시작/중단 컨트롤

## Directory Map
- `apps/web`: React + TypeScript + Vite + TailwindCSS
- `apps/api`: FastAPI + WebSocket
- `packages/contracts`: JSON Schema 기반 타입 생성
- `infra/cdk`: AWS CDK v2 (Python)
- `infra/docker`: Dockerfile (API)

## Prerequisites
- Node.js 20.x (`.nvmrc`)
- npm@>=10
- Python 3.11+
- AWS 자격증명 (Bedrock + Transcribe 권한)

## Local Development
### 1) Dependencies
```bash
npm install
```

Backend 의존성은 다음 중 하나로 설치합니다.

Option A) venv + pip
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
```

Option B) Poetry
```bash
cd apps/api
poetry install
```

### 1-1) Environment setup
```bash
# Backend
cp apps/api/.env.example apps/api/.env

# Frontend (optional)
cp apps/web/.env.example apps/web/.env
```

### 2) Run API
```bash
npm run dev:api
```

Poetry를 사용하는 경우:
```bash
cd apps/api
poetry run uvicorn app.main:app --reload
```

### 3) Run Web
```bash
npm run dev:web
```

### 4) Docker Compose
```bash
docker-compose up
```

## Local Testing (Backend + Frontend)
### 1) Start backend API
```bash
npm run dev:api
```

### 2) Start frontend web
```bash
npm run dev:web
```

### 3) Open the app
- `http://localhost:5173`

### 4) Run tests
```bash
npm run test:api
npm run test:web
```

### Notes
- 실시간 전사/번역은 AWS 자격증명이 필요합니다. 로컬에서 실제 기능을 확인하려면 `AWS_REGION`과 `AWS_PROFILE`(또는 환경 변수 기반 자격증명)을 설정하세요.
- Bedrock 모델 ID는 리전에 따라 유효해야 합니다.
- Live 자막은 partial TTL(기본 25초) 이후 제거되며, 확정 자막은 최신 일부만 Live에 유지됩니다.
- Transcribe diarization은 비활성화되어 화자 라벨이 표시되지 않습니다.

### Environment Variables
#### Backend (`apps/api/.env`)
- `AWS_REGION` (default: ap-northeast-2)
- `AWS_PROFILE` (optional)
- `TRANSCRIBE_LANGUAGE_CODE` (default: en-US)
- `BEDROCK_TRANSLATION_MODEL_ID` (default: apac.amazon.nova-2-lite-v1:0)
- `BEDROCK_QUICK_TRANSLATE_MODEL_ID` (default: apac.anthropic.claude-haiku-4-5-20251001-v1:0)
- `CORS_ORIGINS` (default: http://localhost:5173)

#### Frontend (`apps/web/.env`)
- `VITE_API_BASE_URL` (default: http://localhost:8000)
- `VITE_WS_BASE_URL` (default: ws://localhost:8000)

## Tests / Build / Generate
```bash
npm run test:web
npm run test:api
npm run test:cdk
npm run contracts:generate
npm run build:web
```

## AWS Deployment (CDK)
```bash
cd infra/cdk
cdk bootstrap
cdk synth
cdk deploy
```

자세한 내용은 `infra/README.md`를 참고하세요.
