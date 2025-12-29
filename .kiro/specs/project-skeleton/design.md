# Design Document: Project Skeleton (SDD)

## Overview

English Meeting Helper 모노레포 스켈레톤 설계 문서입니다. 비즈니스 로직 구현 이전에 개발/테스트/배포 기반을 완비하는 것이 목표이며, `PRD v1.0` 및 `DESIGN`에서 정의한 단일 서버 모델(React/Vite SPA + FastAPI WS/REST, AWS Fargate/DynamoDB 등)을 따릅니다.

### 목표
- 모노레포 구조로 프론트엔드, 백엔드, 공유 패키지, 인프라를 통합 관리
- 각 프로젝트가 빌드·테스트 가능한 상태를 제공
- 로컬 개발(Docker/Compose)과 AWS 배포(CDK) 기반 마련
- 공유 스키마 기반 타입 생성(contracts)을 통한 일관된 인터페이스 확보

### 전제
- Node.js 20.x (`.nvmrc`), package manager 명시(npm@>=10 또는 pnpm@8)
- Python 3.11+, Poetry 또는 requirements.txt + lockfile
- TypeScript strict, Pydantic v2 적용

## Architecture

```
english-meeting-helper/
├── apps/
│   ├── api/                    # FastAPI 백엔드
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── api/            # REST 라우터 (/api/v1)
│   │   │   ├── ws/             # WS 라우터 (/ws/v1)
│   │   │   ├── services/       # 외부 연동 어댑터 placeholder
│   │   │   └── domain/models/  # Pydantic v2 DTO
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   ├── requirements.txt    # (Poetry export 또는 직접 관리 택1)
│   │   └── pytest.ini
│   └── web/                    # React 프론트엔드
│       ├── src/
│       │   ├── main.tsx
│       │   ├── app/
│       │   ├── components/
│       │   ├── features/
│       │   │   ├── meeting/
│       │   │   ├── translate/
│       │   │   └── suggestions/
│       │   ├── hooks/
│       │   └── lib/
│       ├── package.json
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       ├── tsconfig.json
│       └── vitest.config.ts
├── packages/
│   └── contracts/              # 공유 스키마
│       ├── schema/
│       │   └── health.json
│       ├── generated/
│       │   ├── ts/
│       │   └── py/
│       ├── package.json
│       └── scripts/
├── infra/
│   ├── cdk/
│   │   ├── app.py
│   │   ├── stacks/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── docker/
│   │   └── api.Dockerfile
│   └── README.md
├── docker-compose.yml          # 로컬 개발용 (api, web)
├── package.json                # 루트 workspace 설정
├── pyproject.toml | requirements.txt  # 루트 Python 관리(선택)
├── .gitignore
├── .nvmrc
└── README.md
```

## Components and Interfaces

### 1. 모노레포 루트 (Root)

루트 레벨에서 npm/pnpm workspaces를 사용하여 JS/TS 프로젝트를 관리하고, Python 프로젝트는 각 디렉터리에서 관리합니다. 필요 시 루트 `pyproject.toml` 또는 `requirements.txt`로 공용 Python 의존성을 정의할 수 있습니다. 공용 스크립트로 dev/test/build를 위임합니다.

```json
// package.json
{
  "name": "english-meeting-helper",
  "private": true,
  "packageManager": "npm@10",
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "dev:web": "npm run dev -w apps/web",
    "dev:api": "cd apps/api && uvicorn app.main:app --reload",
    "test:web": "npm run test -w apps/web",
    "test:api": "cd apps/api && pytest",
    "test:cdk": "cd infra/cdk && pytest",
    "contracts:generate": "npm run generate -w packages/contracts",
    "build:web": "npm run build -w apps/web"
  }
}
```

### 2. Web App (apps/web)

React + TypeScript + Vite 기반 프론트엔드입니다. TypeScript strict, TailwindCSS, ESLint/Prettier를 기본 제공합니다.

**주요 설정 파일:**
- `vite.config.ts`: Vite 빌드 설정
- `tailwind.config.js`: TailwindCSS 설정
- `vitest.config.ts`: Vitest 테스트 설정
- `tsconfig.json`: TypeScript 설정 (strict)
- `postcss.config.js`: Tailwind/PostCSS
- `.eslintrc.*` / `.prettierrc`: 코드 품질

**디렉토리 구조:**
```
apps/web/
├── src/
│   ├── main.tsx           # 엔트리 포인트
│   ├── app/               # 레이아웃/페이지
│   ├── features/
│   │   ├── meeting/       # 전사 패널 placeholder
│   │   ├── translate/     # 빠른 번역 placeholder
│   │   └── suggestions/   # 질문 제안 placeholder
│   ├── lib/
│   │   ├── ws.ts          # WS 클라이언트 stub(자동 재연결)
│   │   ├── api.ts         # REST 클라이언트 stub
│   │   └── audio.ts       # 마이크 캡처/리샘플 stub
│   ├── components/        # 공용 UI
│   ├── hooks/
│   ├── App.tsx            # 루트 컴포넌트
│   ├── App.test.tsx       # 테스트 파일
│   └── index.css          # TailwindCSS 임포트
├── index.html
├── package.json
├── vite.config.ts
├── vitest.config.ts
├── tailwind.config.js
├── postcss.config.js
└── tsconfig.json
```

**기능 요구 정렬:**
- `npm run build -w apps/web` 성공
- `npm test`/`npm run test -w apps/web` → Vitest 통과
- `npm run lint`/`npm run format` 제공

### 3. API Server (apps/api)

FastAPI + Uvicorn 기반 백엔드입니다.

**주요 설정 파일:**
- `pyproject.toml`: Python 의존성 및 프로젝트 설정
- `pytest.ini`: pytest 설정

**디렉토리 구조:**
```
apps/api/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI 앱 정의
│   ├── api/               # REST 라우터 (/api/v1)
│   ├── ws/                # WebSocket 라우터 (/ws/v1)
│   ├── services/          # 외부 연동 어댑터 placeholder
│   └── domain/models/     # Pydantic v2 DTO
├── tests/
│   ├── __init__.py
│   └── test_main.py       # API/WS 테스트
├── pyproject.toml
├── requirements.txt       # (선택) Poetry export 또는 직접 관리
└── pytest.ini
```

**API 엔드포인트:**
- `GET /api/v1/health`: 헬스체크 (`{"status": "ok"}`)
- `WebSocket /ws/v1/meetings/{sessionId}`: 업그레이드/echo placeholder (101)

**기능 요구 정렬:**
- `uvicorn app.main:app --reload` 실행 시 오류 없이 기동
- `pytest` 통과 (httpx/AsyncClient 헬스체크, WS 업그레이드 테스트 포함)
- 의존성: FastAPI, Uvicorn, Pydantic v2, httpx, websockets, pytest

### 4. Contracts Package (packages/contracts)

JSON Schema를 기반으로 TypeScript와 Python 타입을 생성합니다.

**디렉토리 구조:**
```
packages/contracts/
├── schema/
│   └── health.json        # 샘플 스키마
├── generated/
│   ├── ts/
│   │   └── health.ts
│   └── py/
│       └── health.py
├── scripts/
│   ├── generate-ts.js     # TypeScript 생성 스크립트
│   └── generate-py.js     # Python 생성 스크립트
└── package.json
```

**생성 도구:**
- TypeScript: `json-schema-to-typescript`
- Python: `datamodel-code-generator`

### 5. CDK Infrastructure (infra/cdk)

Python CDK를 사용한 AWS 인프라 정의입니다.

**디렉토리 구조:**
```
infra/cdk/
├── app.py                 # CDK 앱 엔트리
├── stacks/
│   ├── __init__.py
│   └── app_stack.py       # 메인 스택
├── tests/
│   ├── __init__.py
│   └── test_app_stack.py  # 스택 테스트
├── pyproject.toml
├── cdk.json
└── requirements.txt
```

**초기 스택 구성 (placeholder):**
- ECS Fargate Service(단일 컨테이너) + ALB 리스너(HTTPS/WS)
- DynamoDB 테이블 2개 (sessions/events) 키 스키마 placeholder
- IAM 역할/로그 설정
- `cdk synth` 합성 테스트

### 6. Docker Configuration (infra/docker)

로컬 개발을 위한 Docker 설정입니다.

**api.Dockerfile (infra/docker/api.Dockerfile):**
```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY apps/api/requirements.txt apps/api/requirements.txt
# Poetry 사용 시: poetry export -f requirements.txt -o apps/api/requirements.txt 후 빌드
RUN pip install --no-cache-dir -r apps/api/requirements.txt
COPY apps/api app/api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml (루트):**
```yaml
services:
  api:
    build:
      context: .
      dockerfile: infra/docker/api.Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./apps/api:/app/app
    environment:
      - ENV=development
  web:
    image: node:20
    working_dir: /workspace
    command: ["npm", "run", "dev", "-w", "apps/web", "--", "--host", "0.0.0.0", "--port", "5173"]
    ports:
      - "5173:5173"
    volumes:
      - ./:/workspace
    environment:
      - API_BASE_URL=http://localhost:8000/api/v1
      - WS_BASE_URL=ws://localhost:8000/ws/v1
```

## Data Models

### Health Response Schema

```json
// packages/contracts/schema/health.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "HealthResponse",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["ok", "error"]
    }
  },
  "required": ["status"]
}
```

**Generated TypeScript:**
```typescript
export interface HealthResponse {
  status: "ok" | "error";
}
```

**Generated Python:**
```python
from pydantic import BaseModel
from typing import Literal

class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

대부분의 요구사항이 파일 존재 여부나 설정 확인과 같은 예제 기반 테스트에 해당합니다. 다음은 속성 기반 테스트로 검증할 수 있는 핵심 속성들입니다:

### Property 1: Health Endpoint Consistency

*For any* valid HTTP GET request to the `/api/v1/health` endpoint, the API_Server SHALL return a JSON response with status "ok" and HTTP status code 200.

**Validates: Requirements 3.3**

### Property 2: Schema Generation Round-Trip

*For any* valid JSON Schema definition in `packages/contracts/schema`, running the generation scripts SHALL produce syntactically valid TypeScript and Python files that can be parsed without errors.

**Validates: Requirements 4.5**

### Property 3: CDK Synthesis Validity

*For any* valid CDK stack definition in infra/cdk, running `cdk synth` SHALL produce a valid CloudFormation template that passes CloudFormation template validation.

**Validates: Requirements 5.4**

## Error Handling

### API Server Errors
- 잘못된 엔드포인트 요청: 404 Not Found 반환
- 서버 내부 오류: 500 Internal Server Error 반환
- WebSocket 연결 실패: 적절한 에러 메시지와 함께 연결 종료

### Build/Test Errors
- 의존성 설치 실패: 명확한 에러 메시지 출력
- 테스트 실패: 실패한 테스트 케이스 상세 정보 출력
- CDK synth 실패: CloudFormation 검증 오류 상세 출력

### Schema Generation Errors
- 잘못된 JSON Schema: 파싱 에러 메시지 출력
- 생성 스크립트 실패: 어떤 스키마에서 실패했는지 명시

## Testing Strategy

### 테스트 프레임워크

| 프로젝트 | 테스트 프레임워크 | 속성 기반 테스트 |
|---------|-----------------|----------------|
| apps/web | Vitest | - |
| apps/api | pytest | pytest + hypothesis |
| infra/cdk | pytest | - |
| packages/contracts | Node.js scripts | - |

### 단위 테스트 (Unit Tests)

**apps/web:**
- 컴포넌트 렌더링 테스트
- 빌드 설정 검증

**apps/api:**
- 엔드포인트 응답 테스트
- WebSocket 연결 테스트

**infra/cdk:**
- 스택 리소스 존재 여부 테스트
- CloudFormation 템플릿 검증

### 속성 기반 테스트 (Property-Based Tests)

**apps/api:**
- Property 1: Health endpoint가 항상 일관된 응답을 반환하는지 검증
- pytest + hypothesis를 사용하여 다양한 요청 조건에서 테스트

**packages/contracts:**
- Property 2: 스키마 생성 스크립트가 유효한 코드를 생성하는지 검증

**infra/cdk:**
- Property 3: CDK synth가 유효한 CloudFormation을 생성하는지 검증

### 테스트 실행 명령

```bash
# 전체 테스트/생성 (루트)
npm run test:web
npm run test:api
npm run test:cdk
npm run contracts:generate

# 개별 테스트/빌드
cd apps/web && npm test && npm run build
cd apps/api && pytest
cd infra/cdk && pytest && cdk synth
```

### 테스트 설정

- 각 속성 기반 테스트는 최소 100회 반복 실행
- 테스트 태그 형식: `Feature: project-skeleton, Property N: [property_text]`
