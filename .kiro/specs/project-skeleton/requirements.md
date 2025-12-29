# Requirements Document

## Introduction

English Meeting Helper 프로젝트의 초기 스켈레톤 구성을 위한 요구사항입니다. 실제 비즈니스 로직 구현이 아닌, 모노레포 구조 설정, 기술 스택 초기화, 테스트 환경 구축, AWS CDK 인프라 기반 마련을 목표로 합니다.

## Scope & Assumptions

- 기준 문서: PRD v1.0(2025-12-28) 및 DESIGN 문서의 아키텍처 결정사항(React/Vite SPA + FastAPI 단일 서버, AWS Fargate + DynamoDB 등)
- 범위: 스켈레톤/부트스트랩 수준(비즈니스 로직, 실서비스 인프라 최적화는 포함하지 않음)
- 언어/버전: Node.js 20.x, Python 3.11+
- 패키지 관리자: npm(or pnpm) / Poetry(or pip) 중 하나를 명시적으로 선택하고 lockfile을 포함

## Glossary

- **Monorepo**: 여러 프로젝트(apps, packages, infra)를 단일 저장소에서 관리하는 구조
- **Web_App**: React + TypeScript + Vite 기반 프론트엔드 애플리케이션
- **API_Server**: Python + FastAPI 기반 백엔드 서버
- **Contracts_Package**: 프론트엔드와 백엔드 간 공유되는 스키마 정의 패키지
- **CDK_Infrastructure**: Python 기반 AWS CDK 인프라 코드
- **Test_Runner**: 각 프로젝트의 테스트 실행 환경

## Requirements

### Requirement 1: 모노레포 루트 구조 설정

**User Story:** As a 개발자, I want 모노레포 루트 구조가 설정되어 있기를, so that 여러 프로젝트를 일관된 방식으로 관리할 수 있다.

#### Acceptance Criteria

1. THE Monorepo SHALL have a root package.json with workspace configuration for `apps/*` and `packages/*`, and SHALL pin the package manager (e.g., `"packageManager": "npm@>=10"` or pnpm@8)
2. THE Monorepo SHALL have a root Python dependency file (pyproject.toml with Poetry or requirements.txt) compatible with Python 3.11+
3. THE Monorepo SHALL have a .gitignore covering Node.js, Python, and IDE artifacts
4. THE Monorepo SHALL have an .nvmrc specifying Node.js 20.x
5. THE Monorepo root SHALL include directories `apps/api`, `apps/web`, `packages/contracts`, `infra`

### Requirement 2: React 프론트엔드 스켈레톤 구성

**User Story:** As a 프론트엔드 개발자, I want React + TypeScript + Vite 프로젝트가 초기화되어 있기를, so that 즉시 개발을 시작할 수 있다.

#### Acceptance Criteria

1. WHEN the Web_App is initialized, THE Web_App SHALL be located at `apps/web`
2. THE Web_App SHALL use Vite with React + TypeScript plugins and a strict TypeScript config
3. THE Web_App SHALL have TailwindCSS configured (PostCSS/tailwind.config.js present) and verified via `npm run dev` rendering base styles
4. THE Web_App SHALL include a sample page/component that renders without runtime errors and lives under `src/features/` (e.g., meeting/translate/suggestions placeholders)
5. WHEN running `npm test` in `apps/web`, THE Test_Runner SHALL execute Vitest tests successfully
6. THE Web_App SHALL have ESLint and Prettier configured with npm scripts (e.g., `npm run lint`, `npm run format`)
7. WHEN running `npm run build` in `apps/web`, THE build SHALL succeed

### Requirement 3: FastAPI 백엔드 스켈레톤 구성

**User Story:** As a 백엔드 개발자, I want FastAPI 프로젝트가 초기화되어 있기를, so that API 개발을 즉시 시작할 수 있다.

#### Acceptance Criteria

1. WHEN the API_Server is initialized, THE API_Server SHALL be located at `apps/api`
2. THE API_Server SHALL use FastAPI with Uvicorn as the ASGI server and SHALL expose an app entrypoint (e.g., `app/main.py` with `app = FastAPI()`)
3. THE API_Server SHALL have a health check endpoint at `GET /api/v1/health` returning `{"status": "ok"}`
4. THE API_Server SHALL have a WebSocket endpoint placeholder at `/ws/v1/meetings/{sessionId}` that upgrades successfully (101) and echoes/acknowledges messages
5. WHEN running `pytest` in `apps/api`, THE Test_Runner SHALL execute tests successfully (including a health-check test using httpx/AsyncClient)
6. THE API_Server SHALL have `pyproject.toml` (Poetry) or requirements.txt managing dependencies (FastAPI, Uvicorn, Pydantic v2, httpx, pytest, websockets)
7. WHEN running `uvicorn app.main:app`, THE server SHALL start without errors

### Requirement 4: 공유 스키마 패키지 구성

**User Story:** As a 풀스택 개발자, I want 프론트엔드와 백엔드가 공유하는 스키마가 정의되어 있기를, so that 타입 안전성을 보장할 수 있다.

#### Acceptance Criteria

1. WHEN the Contracts_Package is initialized, THE Contracts_Package SHALL be located at `packages/contracts`
2. THE Contracts_Package SHALL contain JSON Schema definitions under `packages/contracts/schema/`
3. THE Contracts_Package SHALL have scripts to generate TypeScript types into `packages/contracts/generated/ts`
4. THE Contracts_Package SHALL have scripts to generate Python Pydantic v2 models into `packages/contracts/generated/py`
5. WHEN running the generation scripts, THE Contracts_Package SHALL produce valid TypeScript and Python files that can be imported by `apps/web` and `apps/api` respectively

### Requirement 5: AWS CDK 인프라 스켈레톤 구성

**User Story:** As a DevOps 엔지니어, I want AWS CDK 인프라 코드가 초기화되어 있기를, so that AWS 리소스를 코드로 관리할 수 있다.

#### Acceptance Criteria

1. WHEN the CDK_Infrastructure is initialized, THE CDK_Infrastructure SHALL be located at `infra`
2. THE CDK_Infrastructure SHALL use Python (CDK v2) and a pyproject.toml/requirements.txt for dependencies
3. THE CDK_Infrastructure SHALL have a basic stack definition with placeholders reflecting the target architecture (e.g., ECS Fargate service, ALB, DynamoDB tables for sessions/events)
4. WHEN running `cdk synth`, THE CDK_Infrastructure SHALL generate valid CloudFormation templates without errors
5. THE CDK_Infrastructure SHALL have pytest tests for the CDK constructs (at least stack synthesis smoke test)

### Requirement 6: Docker 개발 환경 구성

**User Story:** As a 개발자, I want Docker 기반 로컬 개발 환경이 구성되어 있기를, so that 일관된 개발 환경에서 작업할 수 있다.

#### Acceptance Criteria

1. THE Monorepo SHALL have a Dockerfile for the API_Server at `infra/docker/api.Dockerfile` (multi-stage build ready for production)
2. THE Monorepo SHALL have a docker-compose.yml for local development including services for `api` (FastAPI) and `web` (Vite dev server or static serve)
3. WHEN running `docker-compose up`, THE API_Server SHALL be accessible at `http://localhost:8000` and the Web_App dev server (if enabled) at its configured port
4. THE docker-compose.yml SHALL include volume mounts for hot-reload during development and shall wire environment variables for API/Web to communicate (e.g., `API_BASE_URL`, `WS_BASE_URL`)

### Requirement 7: 프로젝트 문서화

**User Story:** As a 신규 개발자, I want 프로젝트 설정 및 실행 방법이 문서화되어 있기를, so that 빠르게 온보딩할 수 있다.

#### Acceptance Criteria

1. THE Monorepo SHALL have a README.md at the root with project overview and directory map
2. THE README.md SHALL include local development setup instructions (Node/Python versions, package managers, env vars)
3. THE README.md SHALL include AWS deployment instructions referencing the CDK stack
4. THE README.md SHALL include test execution commands for each project (web/api/contracts/cdk)
5. WHEN following the README.md instructions, a new developer SHALL be able to run the project locally (web dev server + API health check) and run the test suites
