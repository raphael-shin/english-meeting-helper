---
inclusion: manual
---

# AWS 서비스 연동 가이드

## AWS Transcribe Streaming
- 실시간 음성→텍스트 전사
- 언어: en-US (기본)
- 화자 분리(Diarization) 활성화 (최대 10명)
- 오디오 포맷: 16kHz mono PCM

### 사용 패턴
```python
# 어댑터 패턴으로 분리
class TranscribeAdapter:
    async def start_stream(self, session_id: str, config: TranscribeConfig) -> AsyncIterator[TranscriptEvent]:
        ...
    async def send_audio(self, chunk: bytes) -> None:
        ...
    async def stop_stream(self) -> None:
        ...
```

## AWS Bedrock (Nova 2 Lite / Claude Haiku)
- 실시간 번역(영→한): `apac.amazon.nova-2-lite-v1:0`
- 빠른 번역(한→영): `apac.anthropic.claude-haiku-4-5-20251001-v1:0`
- 질문 제안: Nova 2 Lite 사용 (영→한 번역 모델과 동일)
- 모델 ID는 환경 변수로 주입
  - `BEDROCK_TRANSLATION_MODEL_ID` (default: `apac.amazon.nova-2-lite-v1:0`)
  - `BEDROCK_QUICK_TRANSLATE_MODEL_ID` (default: `apac.anthropic.claude-haiku-4-5-20251001-v1:0`)

### 번역 프롬프트 예시
```
Translate the following English text to natural Korean:
"{text}"
Return only the translation, no explanation.
```

### 빠른 번역 프롬프트 예시 (한→영)
```
Translate the following Korean text to natural English:
"{text}"
Return only the translation, no explanation.
```

### 질문 제안 프롬프트 예시
```
Based on the meeting context below, suggest 3-5 relevant follow-up questions in English with Korean translations.
Context: {recent_transcripts}
```

### 비용 최적화
- 문장 배치 처리 (1-2문장 단위)
- 세션당 번역 in-flight 제한 (1개)
- 질문 제안: 미팅 진행 속도 기반(동일 화자 연속 3문장 또는 Transcribe 화자 라벨 변경 시 업데이트)

## DynamoDB

### meeting_sessions 테이블
- PK: `sessionId`
- Attributes: createdAt, endedAt, title, userId, settings

### meeting_events 테이블
- PK: `sessionId`
- SK: `ts#seq`
- Attributes: type, speaker, text, meta

## 인프라 (ECS Fargate)
- ALB: HTTPS 종료 + WebSocket 지원
- ECS Service 1개 (단일 컨테이너)
- Auto Scaling 설정 권장

## AWS Cognito (선택)
- 사용자 인증/인가 (JWT 기반)
- 프론트에서 로그인 후 토큰 발급, 백엔드에서 JWKS 검증

## S3 + CloudFront (선택)
- 회의 기록 아카이브 또는 정적 자산 캐싱
- 단일 서비스 운영 시에도 확장 옵션으로 유지

## ElastiCache/Redis (선택)
- 다중 인스턴스 WS 브로드캐스트/세션 상태 동기화
