---
inclusion: fileMatch
fileMatchPattern: "apps/api/**/*.py"
---

# Backend 개발 가이드라인 (FastAPI)

## 디렉토리 구조
```
apps/api/app/
  main.py           # FastAPI 앱 진입점
  core/             # 설정, 로깅, 보안, DI
  api/              # REST 라우터 (/api/v1)
  ws/               # WebSocket 라우터 (/ws/v1)
  services/
    transcribe/     # AWS Transcribe 어댑터
    bedrock/        # AWS Bedrock 어댑터
    session/        # 세션/이벤트 저장
  domain/models/    # Pydantic 모델
```

## 코딩 규칙
- Python 3.11+ 사용
- Pydantic v2로 DTO/이벤트 모델 정의
- 타입 힌트 필수
- 비동기(async/await) 우선 사용
- 외부 의존성(Transcribe/Bedrock)은 어댑터 패턴으로 분리

## REST API 설계
- Prefix: `/api/v1`
- 세션: `POST /sessions`, `POST /sessions/{id}/stop`, `GET /sessions/{id}`
- 번역: `POST /translate/ko-en`
- Export: `GET /sessions/{id}/export?format=txt|json`

## WebSocket 설계
- Endpoint: `/ws/v1/meetings/{sessionId}`
- Control 메시지: JSON 텍스트 프레임
- Audio: 바이너리 프레임 (16kHz mono PCM s16le)

## 이벤트 타입
- `session.start`, `session.stop`
- `transcript.partial`, `transcript.final`
- `translation.final`
- `suggestions.update`
- `error`

## 테스트
- pytest + httpx (REST)
- 외부 서비스는 mock/fake로 테스트
- 통합 테스트로 WS 이벤트 흐름 검증

## 환경 변수
- `AWS_REGION`
- `BEDROCK_TRANSLATION_MODEL_ID` (default: apac.amazon.nova-2-lite-v1:0)
- `BEDROCK_QUICK_TRANSLATE_MODEL_ID` (default: apac.anthropic.claude-haiku-4-5-20251001-v1:0)
- `TRANSCRIBE_LANGUAGE_CODE` (default: en-US)
- `DDB_SESSIONS_TABLE`, `DDB_EVENTS_TABLE`
- `CORS_ORIGINS` (개발용)
