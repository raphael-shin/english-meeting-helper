# AGENTS.md

English Meeting Helper - 실시간 영어 회의 지원 AI 어시스턴트

## Project Context

자세한 가이드라인은 `.kiro/steering/` 디렉토리의 파일들을 참고하세요:
- `product.md` - 제품 개요 및 핵심 기능
- `tech.md` - 기술 스택 및 명령어
- `structure.md` - 프로젝트 구조

## Quick Start

```bash
# 의존성 설치
npm install
pip install -r apps/api/requirements.txt

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

## Testing

```bash
npm run test:web              # Frontend (vitest)
npm run test:api              # Backend (pytest)
npm run test:cdk              # CDK 인프라 테스트
```

- 외부 서비스는 mock/fake로 테스트
- 코드 변경 시 관련 테스트 추가/수정

## Environment Setup

```bash
# Backend 환경변수
cp apps/api/.env.example apps/api/.env

# Frontend 환경변수 (선택)
cp apps/web/.env.example apps/web/.env
```

주요 환경변수:
- `AWS_REGION`, `AWS_PROFILE` - AWS 자격증명
- `VITE_API_BASE_URL`, `VITE_WS_BASE_URL` - API 엔드포인트

## PR Guidelines

- 제목 형식: `[api|web|infra|contracts] 변경 내용`
- 커밋 전 lint/test 통과 확인
- 타입 변경 시 `npm run contracts:generate` 실행
