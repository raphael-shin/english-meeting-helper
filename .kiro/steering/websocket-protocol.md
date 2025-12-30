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

### transcript.partial
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
`transcript.final` 이벤트는 문장 경계(`.`, `!`, `?`) 기준으로 완성된 문장(또는 1~2문장 청크)만 전달합니다. AWS Transcribe의 final 결과가 들어와도 문장이 완료되지 않은 경우에는 `transcript.partial`만 갱신될 수 있습니다.

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
> `translation.final` 이벤트는 partial 전사에 대한 임시 번역 업데이트로도 전송될 수 있습니다.

### translation.corrected
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
> `translation.corrected`는 LLM 보정 이후의 텍스트를 다시 번역한 결과를 비동기 갱신하는 이벤트입니다.

### suggestions.update (P1)
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
