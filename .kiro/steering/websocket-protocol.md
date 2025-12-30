---
inclusion: manual
---

# WebSocket 프로토콜 명세

## 연결
- Endpoint: `/ws/v1/meetings/{sessionId}`
- 프로토콜: WSS (TLS)
- `sessionId`는 클라이언트가 생성하여 경로 파라미터로 전달

## 프레임 규칙
- Control/Event: JSON 텍스트 프레임
- Audio: 바이너리 프레임 (AWS: 16kHz mono PCM s16le, OpenAI: 24kHz mono PCM s16le)
- `ts`는 epoch milliseconds 기준
- `speaker`는 `"spk_1"` 형태의 문자열 식별자
- 단일 화자 모드에서는 모든 이벤트의 `speaker`를 `"spk_1"`로 고정합니다.

## 클라이언트 → 서버 (Control)

### session.start
```json
{
  "type": "session.start",
  "sampleRate": 16000,
  "format": "pcm_s16le",
  "lang": "en-US"
}
```
OpenAI 모드에서는 `sampleRate`를 `24000`으로 설정합니다.

### session.stop
```json
{ "type": "session.stop" }
```

### client.ping
```json
{ "type": "client.ping", "ts": 1735350000000 }
```

### suggestions.prompt
```json
{
  "type": "suggestions.prompt",
  "prompt": "회의 목적과 전달할 핵심 정보를 요약하세요."
}
```

### Audio (바이너리)
- 20~100ms 단위 청크
- AWS: 16kHz mono PCM s16le
- OpenAI: 24kHz mono PCM s16le

## 서버 → 클라이언트 (Event)

### server.pong
```json
{ "type": "server.pong", "ts": 1735350000000 }
```

### display.update (NEW)
```json
{
  "type": "display.update",
  "sessionId": "sess_123",
  "ts": 1735350000123,
  "confirmed": [
    {
      "id": "seg_41",
      "text": "So the next step is to review the budget.",
      "speaker": "spk_1",
      "startTime": 1735350000456,
      "endTime": 1735350001456,
      "isFinal": true,
      "llmCorrected": false,
      "segmentId": 41
    }
  ],
  "current": {
    "id": "seg_42",
    "text": "And then we need to",
    "speaker": "spk_1",
    "startTime": 1735350002000,
    "endTime": null,
    "isFinal": false,
    "llmCorrected": false,
    "segmentId": 42
  }
}
```
**Live 탭 표시용 이벤트:**
- `confirmed`: 확정된 자막 (최대 4개, FIFO)
- `current`: 현재 작성 중인 자막 (partial)
- 동일 `segmentId`로 progressive update 수행

### transcript.partial (Legacy)
```json
{
  "type": "transcript.partial",
  "sessionId": "sess_123",
  "speaker": "spk_1",
  "ts": 1735350000123,
  "text": "So the next step is",
  "segmentId": 41
}
```
**하위 호환용 이벤트** - `display.update`와 병행 발행

### transcript.final
```json
{
  "type": "transcript.final",
  "sessionId": "sess_123",
  "speaker": "spk_1",
  "ts": 1735350000456,
  "text": "So the next step is to review the budget.",
  "segmentId": 41
}
```
**Final 전사는 단일 segment로 처리** - 더 이상 chunking하지 않음

### transcript.corrected (Optional)
```json
{
  "type": "transcript.corrected",
  "sessionId": "sess_123",
  "segmentId": 42,
  "originalText": "So the next step is to reveiw the budget.",
  "correctedText": "So the next step is to review the budget."
}
```
**LLM 보정 결과** - `LLM_CORRECTION_ENABLED=true`일 때만 발행

### translation.final
```json
{
  "type": "translation.final",
  "sessionId": "sess_123",
  "sourceTs": 1735350000456,
  "segmentId": 41,
  "speaker": "spk_1",
  "sourceText": "So the next step is to review the budget.",
  "translatedText": "다음 단계는 예산을 검토하는 것입니다."
}
```

### translation.corrected (Optional)
```json
{
  "type": "translation.corrected",
  "sessionId": "sess_123",
  "segmentId": 42,
  "speaker": "spk_1",
  "sourceText": "So the next step is to review the budget.",
  "translatedText": "다음 단계는 예산을 검토하는 것입니다."
}
```
**보정된 텍스트의 재번역 결과** - LLM 보정 후 비동기 발행

### suggestions.update
```json
{
  "type": "suggestions.update",
  "sessionId": "sess_123",
  "ts": 1735350060000,
  "items": [
    { "en": "Could you clarify the budget owner?", "ko": "예산 담당자가 누구인지 명확히 해주실 수 있나요?" }
  ]
}
```

### error
```json
{
  "type": "error",
  "code": "TRANSCRIBE_STREAM_ERROR",
  "message": "Upstream streaming error",
  "retryable": true
}
```

## 에러 코드
- `TRANSCRIBE_STREAM_ERROR`: Transcribe 스트리밍 오류
- `BEDROCK_ERROR`: Bedrock 호출 오류
- `SESSION_NOT_FOUND`: 세션 없음
- `INVALID_MESSAGE`: 잘못된 메시지 형식

## 주요 변경사항 (2025-12-30)
1. **display.update 이벤트 추가**: Live 탭 전용 display buffer 관리
2. **단일 segment Final**: chunking 제거, Final은 하나의 완전한 문장
3. **Progressive partial updates**: 동일 segmentId 유지
4. **LLM correction 이벤트**: transcript.corrected, translation.corrected 추가
5. **Partial Result Stabilization**: AWS Transcribe "high" stability 적용
