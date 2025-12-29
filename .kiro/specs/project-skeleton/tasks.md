# Implementation Plan: Project Skeleton

## Overview

English Meeting Helper 모노레포 스켈레톤을 구성합니다. 모노레포 루트 설정부터 시작하여 각 프로젝트를 순차적으로 초기화하고, 테스트 환경을 구축한 후 문서화로 마무리합니다.

## Tasks

- [x] 1. 모노레포 루트 구조 설정
  - [x] 1.1 루트 package.json 생성 (npm workspaces 설정)
    - `apps/*`, `packages/*` 워크스페이스 설정 + packageManager 핀(npm@>=10 또는 pnpm@8)
    - 공용 스크립트 정의 (dev:web, dev:api, test:web, test:api, test:cdk, contracts:generate, build:web)
    - _Requirements: 1.1_
  - [x] 1.2 .gitignore 파일 생성
    - Node.js, Python, IDE 아티팩트 포함
    - _Requirements: 1.3_
  - [x] 1.3 .nvmrc 파일 생성
    - Node.js 20.x 버전 명시
    - _Requirements: 1.4_
  - [x] 1.4 루트 Python 의존성 파일 생성(선택)
    - pyproject.toml 또는 requirements.txt (Python 3.11+ 호환) 중 택1
    - _Requirements: 1.2_
  - [x] 1.5 필수 디렉터리 생성
    - `apps/api`, `apps/web`, `packages/contracts`, `infra`
    - _Requirements: 1.5_

- [x] 2. React 프론트엔드 스켈레톤 구성 (apps/web)
  - [x] 2.1 Vite + React + TypeScript 프로젝트 초기화
    - apps/web 디렉토리에 Vite 프로젝트 생성
    - vite.config.ts, tsconfig.json(strict) 설정
    - _Requirements: 2.1, 2.2_
  - [x] 2.2 TailwindCSS 설정
    - tailwind.config.js, postcss.config.js 생성
    - index.css에 Tailwind 디렉티브 추가
    - _Requirements: 2.3_
  - [x] 2.3 ESLint 및 Prettier 설정
    - .eslintrc.cjs, .prettierrc 생성
    - _Requirements: 2.6_
  - [x] 2.4 샘플 컴포넌트 및 디렉토리 구조 생성
    - main.tsx, App.tsx 작성
    - features/meeting, features/translate, features/suggestions, lib/, components/, hooks/ 디렉토리 생성
    - lib/ws.ts, lib/api.ts, lib/audio.ts stub 파일 생성(WS 자동 재연결 스텁)
    - _Requirements: 2.4_
  - [x] 2.5 Vitest 테스트 환경 설정
    - vitest.config.ts 생성
    - App.test.tsx 샘플 테스트 작성
    - _Requirements: 2.5_
  - [x] 2.6 빌드 스크립트 검증
    - `npm run build -w apps/web` 실행 성공
    - _Requirements: 2.7_

- [x] 3. Checkpoint - 프론트엔드 테스트 확인
  - `npm run test:web` 실행하여 테스트 통과 확인
  - 문제 발생 시 사용자에게 질문

- [x] 4. FastAPI 백엔드 스켈레톤 구성 (apps/api)
  - [x] 4.1 Python 프로젝트 초기화
    - apps/api 디렉토리에 pyproject.toml 생성
    - FastAPI, Uvicorn, Pydantic v2, httpx, websockets, pytest 의존성 추가
    - requirements.txt 생성(또는 Poetry export)
    - _Requirements: 3.1, 3.2, 3.5_
  - [x] 4.2 FastAPI 앱 및 디렉토리 구조 생성
    - app/main.py 작성 (app = FastAPI())
    - app/api/, app/ws/, app/services/, app/domain/models/ 디렉토리 생성
    - _Requirements: 3.1_
  - [x] 4.3 Health 엔드포인트 구현
    - GET /api/v1/health → {"status": "ok"}
    - _Requirements: 3.3_
  - [x] 4.4 WebSocket 엔드포인트 placeholder 구현
    - /ws/v1/meetings/{sessionId} 업그레이드/echo placeholder (101 응답)
    - _Requirements: 3.6_
  - [x] 4.5 pytest 테스트 환경 설정
    - pytest.ini 생성
    - tests/test_main.py 작성 (health, WebSocket 테스트)
    - _Requirements: 3.4_
  - [x]* 4.6 Property 1: Health Endpoint Consistency 테스트 작성
    - **Property 1: Health Endpoint Consistency**
    - pytest + hypothesis 사용
    - **Validates: Requirements 3.3**

- [x] 5. Checkpoint - 백엔드 테스트 확인
  - `npm run test:api` 실행하여 테스트 통과 확인
  - 문제 발생 시 사용자에게 질문

- [x] 6. 공유 스키마 패키지 구성 (packages/contracts)
  - [x] 6.1 패키지 초기화
    - packages/contracts 디렉토리에 package.json 생성
    - json-schema-to-typescript, datamodel-code-generator 의존성 추가
    - _Requirements: 4.1_
  - [x] 6.2 JSON Schema 정의
    - schema/health.json 생성
    - _Requirements: 4.2_
  - [x] 6.3 TypeScript 생성 스크립트 작성
    - scripts/generate-ts.js 작성
    - _Requirements: 4.3_
  - [x] 6.4 Python 생성 스크립트 작성
    - scripts/generate-py.js 작성
    - _Requirements: 4.4_
  - [x] 6.5 생성 스크립트 실행 및 검증
    - `npm run contracts:generate` 실행
    - generated/ts/, generated/py/ 파일 생성 확인
    - _Requirements: 4.5_
  - [x]* 6.6 Property 2: Schema Generation Round-Trip 테스트 작성
    - **Property 2: Schema Generation Round-Trip**
    - 생성된 TypeScript/Python 파일 파싱 검증
    - **Validates: Requirements 4.5**

- [x] 7. Checkpoint - 스키마 생성 확인
  - `npm run contracts:generate` 실행하여 생성 확인
  - 문제 발생 시 사용자에게 질문

- [x] 8. AWS CDK 인프라 스켈레톤 구성 (infra/cdk)
  - [x] 8.1 CDK 프로젝트 초기화
    - infra/cdk 디렉토리에 pyproject.toml, cdk.json 생성
    - aws-cdk-lib, constructs, pytest 의존성 추가
    - _Requirements: 5.1, 5.2_
  - [x] 8.2 CDK 앱 및 스택 정의
    - app.py 작성
    - stacks/app_stack.py 작성 (ECS Fargate + ALB + DynamoDB sessions/events placeholder)
    - _Requirements: 5.3_
  - [x] 8.3 CDK 테스트 작성
    - tests/test_app_stack.py 작성
    - _Requirements: 5.5_
  - [ ]* 8.4 Property 3: CDK Synthesis Validity 테스트 작성
    - **Property 3: CDK Synthesis Validity**
    - cdk synth 실행 및 CloudFormation 템플릿 검증
    - **Validates: Requirements 5.4**

- [x] 9. Checkpoint - CDK 테스트 확인
  - `npm run test:cdk` 실행하여 테스트 통과 확인
  - 문제 발생 시 사용자에게 질문

- [x] 10. Docker 개발 환경 구성
  - [x] 10.1 API Dockerfile 작성
    - infra/docker/api.Dockerfile 생성 (requirements.txt 또는 Poetry export 기반 설치)
    - _Requirements: 6.1_
  - [x] 10.2 docker-compose.yml 작성
    - 루트에 docker-compose.yml 생성
    - api(8000), web(5173) 서비스 정의, 환경변수(API_BASE_URL, WS_BASE_URL)
    - 볼륨 마운트 설정 (hot-reload)
    - _Requirements: 6.2, 6.3, 6.4_

- [x] 11. 프로젝트 문서화
  - [x] 11.1 README.md 작성
    - 프로젝트 개요 및 디렉터리 맵
    - 로컬 개발 환경(Node/Python 버전, 패키지 관리자, env) 설정 방법
    - AWS 배포 방법(CDK)
    - 테스트/빌드/생성 명령(web/api/contracts/cdk)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [x] 11.2 infra/README.md 작성
    - CDK 배포 상세 가이드
    - _Requirements: 7.3_

- [ ] 12. Final Checkpoint - 전체 테스트 확인
  - 모든 테스트 통과 확인 (web, api, cdk)
  - docker-compose up 실행 가능 확인
  - README 절차대로 web dev 서버 및 /api/v1/health 호출 가능 확인
  - 문제 발생 시 사용자에게 질문

## Notes

- `*` 표시된 태스크는 선택적이며, 빠른 MVP를 위해 건너뛸 수 있습니다
- 각 태스크는 특정 요구사항을 참조하여 추적 가능합니다
- Checkpoint에서 테스트 실패 시 이전 태스크를 수정합니다
- Property 테스트는 해당 기능 구현 직후에 배치하여 조기에 오류를 발견합니다
