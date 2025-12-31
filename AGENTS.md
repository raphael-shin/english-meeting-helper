# AGENTS.md

English Meeting Helper - 실시간 영어 회의 지원 AI 어시스턴트

## Project Context

자세한 가이드라인은 `.kiro/steering/` 디렉토리의 파일들을 참고하세요:
- `product.md` - 제품 개요 및 핵심 기능
- `tech.md` - 기술 스택 및 명령어
- `structure.md` - 프로젝트 구조
- `websocket-protocol.md` - WebSocket 이벤트/메시지 규약

## Quick Start

```bash
# 의존성 설치
npm install
pip install -r apps/api/requirements.txt

# 환경변수
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# 개발 서버 실행
npm run dev:web    # Frontend (localhost:5173)
npm run dev:api    # Backend (localhost:8000)

# 테스트
npm run test:web   # Vitest
npm run test:api   # pytest
```

## Code Style

### Frontend (TypeScript/React)
- TypeScript strict 모드 필수
- 함수형 컴포넌트 + React Hooks
- TailwindCSS로 스타일링
- ESLint + Prettier 규칙 준수

### Backend (Python/FastAPI)
- Python 3.11+
- Pydantic v2로 모델 정의
- 타입 힌트 필수
- async/await 우선 사용

## Architecture

- **Monorepo**: `apps/api`, `apps/web`, `packages/contracts`, `infra/cdk`
- **WebSocket**: 실시간 오디오 스트리밍 및 이벤트 처리
- **Adapter Pattern**: 외부 서비스(STT, Translation) 분리
- **Shared Contracts**: JSON Schema → TypeScript/Python 타입 생성
- **Providers**: AWS/OPENAI 지원 (GOOGLE는 미구현)

## Development Workflow
When adding a new feature or API:
1. **Define Schema**: Add/Update JSON Schema in `packages/contracts/schema/`.
2. **Generate Types**: Run `npm run contracts:generate` to update TS and Python types.
3. **Backend Implementation**: Implement logic in `apps/api/app/services` and endpoints in `apps/api/app/api`.
4. **Frontend Implementation**: Update UI in `apps/web` using the generated types.

## Directory Responsibilities
### Backend (`apps/api/app/`)
- `api/`: Route handlers (Controllers). Validate input, call services.
- `services/`: Business logic. Pure Python code, independent of HTTP.
- `core/`: Configuration, logging, dependencies (DI).
- `domain/`: Pydantic models, internal data structures.
- `ws/`: WebSocket connection handlers.

## Testing

```bash
npm run test:web              # Frontend (vitest)
npm run test:api              # Backend (pytest)
npm run test:cdk              # CDK 인프라 테스트
```

- 외부 서비스는 mock/fake로 테스트 (Backend는 `pytest-mock` 활용 권장)
- 코드 변경 시 관련 테스트 추가/수정

## Environment Setup

```bash
# Backend 환경변수
cp apps/api/.env.example apps/api/.env

# Frontend 환경변수 (선택)
cp apps/web/.env.example apps/web/.env
```

주요 환경변수:
- `PROVIDER_MODE` - AWS/OPENAI 선택 (GOOGLE 미구현)
- `AWS_REGION`, `AWS_PROFILE` - AWS 자격증명
- `OPENAI_API_KEY` - OPENAI 모드 필수
- `BEDROCK_TRANSLATION_FAST_MODEL_ID`, `BEDROCK_TRANSLATION_HIGH_MODEL_ID`, `BEDROCK_QUICK_TRANSLATE_MODEL_ID`
- `LLM_CORRECTION_ENABLED`, `LLM_CORRECTION_BATCH_SIZE`, `LLM_CORRECTION_INTERVAL_SECONDS`
- `VITE_API_BASE_URL`, `VITE_WS_BASE_URL` - API/WS 엔드포인트

## PR Guidelines

- 제목 형식: `[api|web|infra|contracts] 변경 내용`
- 커밋 전 lint/test 통과 확인
- 타입 변경 시 `npm run contracts:generate` 실행
