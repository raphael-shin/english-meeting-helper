# English Meeting Helper - 프로젝트 개요

## 제품 설명
실시간 영어 회의 지원 웹 기반 AI 어시스턴트. 음성 전사, 번역, 빠른 영작, AI 질문 제안 기능 제공.

## 핵심 기능 (MVP)
- P0: 실시간 음성 전사 (영어, <2초 지연)
- P0: 실시간 번역 (영→한, <3초 지연)
- P0: 빠른 한→영 번역
- P1: AI 질문 제안

## 기술 스택
- Frontend: React + TypeScript + Vite + TailwindCSS + Web Audio API
- Backend: Python 3.11+ + FastAPI + Uvicorn + WebSocket
- AWS: Transcribe Streaming, Bedrock (Nova 2 Lite / Claude Haiku), DynamoDB (옵션: Cognito, S3, CloudFront, ElastiCache)

## 모노레포 구조
```
apps/
  api/          # FastAPI 백엔드
  web/          # React 프론트엔드
packages/
  contracts/    # 공유 스키마 (JSON Schema → TS/Python 생성)
infra/          # Docker, AWS CDK/Terraform
```

## 운영 모델 요약
- 단일 컨테이너/서비스에서 정적 웹 서빙 + API/WS 제공
- WebSocket 기반 실시간 오디오 스트리밍 중심
