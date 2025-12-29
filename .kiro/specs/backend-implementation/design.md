# Design Document: Backend Implementation

## Overview

English Meeting Helper 백엔드 설계 문서입니다. FastAPI 기반으로 실시간 음성 전사, 번역, AI 질문 제안 기능을 구현합니다. AWS Transcribe Streaming과 Bedrock을 활용하며, 임시 자격증명 기반으로 동작합니다.

### 핵심 설계 원칙
- **어댑터 패턴**: 외부 AWS 서비스(Transcribe, Bedrock)를 어댑터로 분리하여 테스트 용이성 확보
- **비동기 우선**: asyncio 기반 비동기 처리로 실시간 스트리밍 성능 최적화
- **이벤트 기반**: WebSocket을 통한 실시간 이벤트 전달
- **임시 자격증명**: AWS SDK 기본 credential chain 사용 (access key 미사용)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Server                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  REST API   │  │  WebSocket  │  │      Core Config        │  │
│  │  /api/v1    │  │  /ws/v1     │  │  (Settings, Logging)    │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘  │
│         │                │                                      │
│  ┌──────┴────────────────┴──────────────────────────────────┐   │
│  │                    Service Layer                         │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │   │
│  │  │  Transcribe  │ │  Translation │ │    Suggestion    │  │   │
│  │  │   Service    │ │   Service    │ │     Service      │  │   │
│  │  └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘  │   │
│  └─────────┼────────────────┼──────────────────┼────────────┘   │
│            │                │                  │                │
│  ┌─────────┴────────────────┴──────────────────┴────────────┐   │
│  │                    AWS SDK (boto3)                       │   │
│  │         Default Credential Chain (임시 자격증명)           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ AWS Transcribe│   │   AWS Bedrock   │   │   AWS Bedrock   │
│   Streaming   │   │  Nova 2 Lite    │   │  Claude Haiku   │
│   (en-US)     │   │  (영→한 번역)     │   │  (한→영 번역)    │
└───────────────┘   └─────────────────┘   └─────────────────┘
```

### 디렉토리 구조

```
apps/api/app/
├── __init__.py
├── main.py                    # FastAPI 앱 진입점
├── core/
│   ├── __init__.py
│   ├── config.py              # 환경 설정 (Pydantic Settings)
│   └── logging.py             # 로깅 설정
├── api/
│   ├── __init__.py
│   ├── health.py              # GET /api/v1/health
│   └── translate.py           # POST /api/v1/translate/ko-en
├── ws/
│   ├── __init__.py
│   └── meetings.py            # WebSocket /ws/v1/meetings/{sessionId}
├── services/
│   ├── __init__.py
│   ├── transcribe.py          # AWS Transcribe Streaming 어댑터
│   ├── bedrock.py             # AWS Bedrock 어댑터
│   └── suggestion.py          # 질문 제안 서비스
└── domain/
    ├── __init__.py
    └── models/
        ├── __init__.py
        ├── events.py          # WebSocket 이벤트 모델
        ├── translate.py       # 번역 요청/응답 모델
        └── session.py         # 세션 모델
```

## Components and Interfaces

### 1. Core Configuration (app/core/config.py)

Pydantic Settings를 사용한 환경 설정 관리입니다.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AWS 설정
    aws_region: str = "ap-northeast-2"
    
    # Transcribe 설정
    transcribe_language_code: str = "en-US"
    transcribe_sample_rate: int = 16000
    transcribe_media_encoding: str = "pcm"
    
    # Bedrock 모델 설정
    bedrock_translation_model_id: str = "apac.amazon.nova-2-lite-v1:0"
    bedrock_quick_translate_model_id: str = "apac.anthropic.claude-haiku-4-5-20251001-v1:0"
    
    # CORS 설정
    cors_origins: list[str] = ["http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### 2. Transcribe Service (app/services/transcribe.py)

AWS Transcribe Streaming을 래핑하는 비동기 어댑터입니다.

```python
from typing import AsyncIterator, Protocol
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

class TranscribeServiceProtocol(Protocol):
    async def start_stream(self, session_id: str) -> None: ...
    async def send_audio(self, audio_chunk: bytes) -> None: ...
    async def stop_stream(self) -> None: ...
    def get_results(self) -> AsyncIterator[TranscriptEvent]: ...

class TranscribeService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = TranscribeStreamingClient(region=settings.aws_region)
        self._stream = None
        self._handler = None
    
    async def start_stream(self, session_id: str) -> None:
        """Transcribe 스트리밍 세션 시작"""
        self._stream = await self.client.start_stream_transcription(
            language_code=self.settings.transcribe_language_code,
            media_sample_rate_hz=self.settings.transcribe_sample_rate,
            media_encoding=self.settings.transcribe_media_encoding,
        )
    
    async def send_audio(self, audio_chunk: bytes) -> None:
        """오디오 청크 전송 (20-100ms 단위)"""
        if self._stream:
            await self._stream.input_stream.send_audio_event(audio_chunk=audio_chunk)
    
    async def stop_stream(self) -> None:
        """스트리밍 세션 종료"""
        if self._stream:
            await self._stream.input_stream.end_stream()
```

### 3. Bedrock Service (app/services/bedrock.py)

AWS Bedrock을 통한 번역 서비스 어댑터입니다.

```python
import boto3
from typing import Protocol

class BedrockServiceProtocol(Protocol):
    async def translate_en_to_ko(self, text: str) -> str: ...
    async def translate_ko_to_en(self, text: str) -> str: ...

class BedrockService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    
    async def translate_en_to_ko(self, text: str) -> str:
        """영어 → 한국어 번역 (Nova 2 Lite)"""
        prompt = f"Translate the following English text to Korean. Only output the translation, nothing else.\n\nEnglish: {text}\n\nKorean:"
        
        response = await self._invoke_model(
            model_id=self.settings.bedrock_translation_model_id,
            prompt=prompt
        )
        return response.strip()
    
    async def translate_ko_to_en(self, text: str) -> str:
        """한국어 → 영어 번역 (Claude Haiku)"""
        prompt = f"Translate the following Korean text to natural English. Only output the translation, nothing else.\n\nKorean: {text}\n\nEnglish:"
        
        response = await self._invoke_model(
            model_id=self.settings.bedrock_quick_translate_model_id,
            prompt=prompt
        )
        return response.strip()
```

### 4. Suggestion Service (app/services/suggestion.py)

회의 맥락 기반 질문 제안 서비스입니다.

```python
class SuggestionService:
    def __init__(self, bedrock_service: BedrockService, settings: Settings):
        self.bedrock = bedrock_service
        self.settings = settings
        self.min_transcripts_for_suggestion = 3
    
    async def generate_suggestions(
        self, transcripts: list[dict[str, str]], system_prompt: str | None = None
    ) -> list[dict[str, str | None]]:
        """회의 맥락 + 시스템 프롬프트 기반 영어 질문 5개 제안 (영/한)"""
        if len(transcripts) < self.min_transcripts_for_suggestion:
            return []
        
        context = "\n".join(item["text"] for item in transcripts[-10:])  # 최근 10개 전사 사용
        system_prompt = system_prompt or ""
        prompt = f"""Use the system prompt below to guide the suggestions.
System prompt:
{system_prompt}

Based on the following meeting transcript, suggest 5 relevant English questions with Korean translations.

Meeting transcript:
{context}

Provide each line in the format: English | Korean. Do not add numbering or bullet points."""
        
        response = await self.bedrock._invoke_model(
            model_id=self.settings.bedrock_translation_model_id,
            prompt=prompt
        )
        
        items = []
        for line in response.strip().split("\n"):
            if not line.strip():
                continue
            if "|" in line:
                en, ko = line.split("|", 1)
                items.append({"en": en.strip(), "ko": ko.strip()})
            else:
                items.append({"en": line.strip(), "ko": None})
        return items[:5]  # 최대 5개
```

### 5. WebSocket Handler (app/ws/meetings.py)

실시간 오디오 스트리밍 및 이벤트 처리 핸들러입니다.

```python
from fastapi import WebSocket, WebSocketDisconnect
from app.domain.models.events import (
    SessionStartEvent, SessionStopEvent,
    TranscriptPartialEvent, TranscriptFinalEvent,
    TranslationFinalEvent, SuggestionsUpdateEvent, ErrorEvent
)

class MeetingSession:
    def __init__(self, session_id: str):
        self.session_id = session_id  # client-provided sessionId
        self.transcripts: list[dict[str, str]] = []
        self.translations: list[dict[str, str]] = []
        self.sentence_buffer: str = ""
        self.last_speaker: str | None = None
        self.finals_since_suggestion: int = 0
        self.consecutive_speaker_finals: int = 0
    
    def add_transcript(self, speaker: str, text: str, is_final: bool) -> tuple[str | None, bool]:
        """전사 추가 및 문장 경계 감지 (. ! ?)"""
        speaker_changed = self.last_speaker is not None and speaker != self.last_speaker
        if is_final:
            self.sentence_buffer += " " + text
            # 문장 경계 감지 (., !, ?)
            if any(self.sentence_buffer.rstrip().endswith(p) for p in [".", "!", "?"]):
                complete_sentence = self.sentence_buffer.strip()
                self.sentence_buffer = ""
                self.transcripts.append({"speaker": speaker, "text": complete_sentence})
                self.finals_since_suggestion += 1
                if speaker_changed:
                    self.consecutive_speaker_finals = 1
                else:
                    self.consecutive_speaker_finals += 1
                self.last_speaker = speaker
                return complete_sentence, speaker_changed
        return None, speaker_changed

    def should_update_suggestions(self, speaker_changed: bool) -> bool:
        return self.consecutive_speaker_finals >= 3 or speaker_changed

    def mark_suggestions_sent(self) -> None:
        self.finals_since_suggestion = 0
        self.consecutive_speaker_finals = 0

async def meeting_websocket(
    websocket: WebSocket,
    session_id: str,
    transcribe_service: TranscribeService,
    bedrock_service: BedrockService,
    suggestion_service: SuggestionService
):
    await websocket.accept()
    session = MeetingSession(session_id)
    
    try:
        await transcribe_service.start_stream(session_id)
        await websocket.send_json(SessionStartEvent(sessionId=session_id).model_dump())
        
        # 병렬 처리: 오디오 수신 + Transcribe 결과 처리
        async with asyncio.TaskGroup() as tg:
            tg.create_task(handle_audio_input(websocket, transcribe_service))
            tg.create_task(handle_transcribe_results(
                websocket, session, transcribe_service, 
                bedrock_service, suggestion_service
            ))
    
    except WebSocketDisconnect:
        pass
    finally:
        await transcribe_service.stop_stream()
        await websocket.send_json(SessionStopEvent(sessionId=session_id).model_dump())
```

`handle_transcribe_results` 내부에서 `transcript.final` 처리 시, Transcribe diarization의 `speaker` 라벨 변화(연속된 `transcript.final`의 speaker 변경)를 감지하고, `session.should_update_suggestions(...)` 조건을 평가하여 동일 화자 연속 3문장 또는 화자 라벨 변경 시점에 `suggestions.update`를 전송합니다.

추가로 `transcript.partial` 처리 시에는 문장 경계(`.`, `!`, `?`)가 감지되면 즉시 번역을 시도하며, 경계가 없더라도 쉼표/접속사 등 소프트 경계와 시간/길이 임계값을 기반으로 임시 번역 업데이트를 전송합니다. 최종 `transcript.final` 수신 시에는 완성된 문장 청크를 기준으로 번역을 다시 생성하여 UI가 정렬되도록 합니다. 문장 버퍼는 화자별로 유지되며, 문장이 끝나지 않은 경우에는 `transcript.partial`만 갱신됩니다.

### 6. REST API - Translate (app/api/translate.py)

빠른 한→영 번역 REST 엔드포인트입니다.

```python
from fastapi import APIRouter, HTTPException
from app.domain.models.translate import TranslateRequest, TranslateResponse

router = APIRouter(prefix="/api/v1")

@router.post("/translate/ko-en", response_model=TranslateResponse)
async def translate_ko_to_en(
    request: TranslateRequest,
    bedrock_service: BedrockService = Depends(get_bedrock_service)
) -> TranslateResponse:
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        translated = await bedrock_service.translate_ko_to_en(request.text)
        return TranslateResponse(translated_text=translated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BEDROCK_ERROR: {str(e)}")
```

## Data Models

### WebSocket 이벤트 모델 (app/domain/models/events.py)

```python
from pydantic import BaseModel, Field
from typing import Literal
import time

def now_ms() -> int:
    return int(time.time() * 1000)

class BaseEvent(BaseModel):
    ts: int = Field(default_factory=now_ms)

class SessionStartEvent(BaseEvent):
    type: Literal["session.start"] = "session.start"
    sessionId: str

class SessionStopEvent(BaseEvent):
    type: Literal["session.stop"] = "session.stop"
    sessionId: str

class TranscriptPartialEvent(BaseEvent):
    type: Literal["transcript.partial"] = "transcript.partial"
    sessionId: str
    speaker: str
    text: str

class TranscriptFinalEvent(BaseEvent):
    type: Literal["transcript.final"] = "transcript.final"
    sessionId: str
    speaker: str
    text: str

class TranslationFinalEvent(BaseEvent):
    type: Literal["translation.final"] = "translation.final"
    sessionId: str
    sourceTs: int
    speaker: str
    sourceText: str
    translatedText: str

class SuggestionItem(BaseModel):
    en: str
    ko: str | None = None

class SuggestionsUpdateEvent(BaseEvent):
    type: Literal["suggestions.update"] = "suggestions.update"
    sessionId: str
    items: list[SuggestionItem]

class ErrorEvent(BaseEvent):
    type: Literal["error"] = "error"
    code: str  # TRANSCRIBE_STREAM_ERROR, BEDROCK_ERROR, INVALID_MESSAGE, SESSION_NOT_FOUND
    message: str
    retryable: bool | None = None
```

### 번역 요청/응답 모델 (app/domain/models/translate.py)

```python
from pydantic import BaseModel, Field

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)

class TranslateResponse(BaseModel):
    translated_text: str
```

### 세션 모델 (app/domain/models/session.py)

```python
from pydantic import BaseModel, Field
from datetime import datetime

class Session(BaseModel):
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    transcripts: list[dict[str, str]] = Field(default_factory=list)
    translations: list[dict[str, str]] = Field(default_factory=list)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Transcript Event Emission

*For any* transcript result received from AWS Transcribe, the WebSocket_Handler SHALL emit `transcript.partial` for partial results. Final results SHALL be buffered and `transcript.final` SHALL be emitted only when a complete sentence chunk is formed.

**Validates: Requirements 2.5, 2.6**

### Property 2: Translation Flow Integrity

*For any* `transcript.final` event generated (sentence chunk), the Translation_Service SHALL produce a translation and the WebSocket_Handler SHALL emit a `translation.final` event containing both the original text and translated text. *For any* partial transcript that contains a complete sentence boundary, the handler SHALL emit an interim `translation.final` event for that sentence.

**Validates: Requirements 3.1, 3.3, 3.6**

### Property 3: Sentence Boundary Detection

*For any* text containing sentence-ending punctuation (`.`, `!`, `?`), the WebSocket_Handler SHALL detect sentence boundaries and pass 1-2 sentence chunks to the Translation_Service. *For any* partial transcript without a hard boundary, the handler SHOULD emit interim translations using soft boundary cues and time/length thresholds.

**Validates: Requirements 3.5, 3.7**

### Property 4: Empty Input Validation

*For any* input text that is empty or consists only of whitespace characters, the `/api/v1/translate/ko-en` endpoint SHALL return HTTP 400 status code with an error message.

**Validates: Requirements 4.4**

### Property 5: Suggestion Generation Threshold

*For any* session with 3 or more final transcripts accumulated, the Suggestion_Service SHALL generate up to 5 contextually relevant English questions (optionally with Korean translations) and emit a `suggestions.update` event when the same speaker produces 3 consecutive `transcript.final` events or the Transcribe diarization speaker label changes. If a session-level suggestions prompt is set, it SHALL be applied to the generation prompt.

**Validates: Requirements 5.1, 5.3, 5.4, 5.6**

### Property 6: Event Structure Validity

*For any* event sent through WebSocket, the event SHALL be valid JSON containing at minimum: `type` (event type string), `ts` (epoch milliseconds), and event-specific payload fields. Error events SHALL additionally contain `code` and `message` fields.

**Validates: Requirements 6.1, 6.3, 6.5**

### Property 7: Session State Accumulation

*For any* transcript or translation added to a session, the Session SHALL store and accumulate these items, and the accumulated count SHALL equal the number of items added.

**Validates: Requirements 7.2**

### Property 8: Invalid Message Handling

*For any* WebSocket message that does not conform to the expected format (invalid JSON for control messages, or unexpected message type), the WebSocket_Handler SHALL emit an `error` event with code `INVALID_MESSAGE`.

**Validates: Requirements 9.3**

## Error Handling

### Transcribe 오류
- **TRANSCRIBE_STREAM_ERROR**: AWS Transcribe 연결 실패 또는 스트리밍 오류
  - WebSocket `error` 이벤트로 클라이언트에 전달
  - 세션 리소스 정리 후 연결 종료

### Bedrock 오류
- **BEDROCK_ERROR**: AWS Bedrock API 호출 실패
  - REST API: HTTP 500 응답 + 에러 메시지
  - WebSocket: `error` 이벤트로 전달, 세션은 유지

### 메시지 오류
- **INVALID_MESSAGE**: 잘못된 형식의 WebSocket 메시지
  - `error` 이벤트로 전달, 세션은 유지
  - 클라이언트가 재시도 가능

### 세션 오류
- **SESSION_NOT_FOUND**: 존재하지 않는 세션 ID
  - `error` 이벤트로 전달 후 연결 종료

### 일반 오류
- 예상치 못한 오류 발생 시 로깅 후 generic 에러 메시지 반환
- 민감한 정보(스택 트레이스 등)는 클라이언트에 노출하지 않음

## Testing Strategy

### 테스트 프레임워크

| 구성요소 | 테스트 프레임워크 | 속성 기반 테스트 |
|---------|-----------------|----------------|
| REST API | pytest + httpx | pytest + hypothesis |
| WebSocket | pytest + websockets | pytest + hypothesis |
| Services | pytest | pytest + hypothesis |

### 단위 테스트 (Unit Tests)

**Services:**
- TranscribeService: 스트림 시작/종료, 오디오 전송 (mocked AWS)
- BedrockService: 번역 호출, 모델 ID 검증 (mocked AWS)
- SuggestionService: 질문 생성 로직, 임계값 검증

**API Endpoints:**
- Health endpoint 응답 검증
- Translate endpoint 요청/응답 검증
- 에러 케이스 (빈 입력, 서비스 오류)

**WebSocket:**
- 연결 수립/종료
- 이벤트 전송 형식 검증
- 에러 이벤트 전송

### 속성 기반 테스트 (Property-Based Tests)

**Property 1: Transcript Event Emission**
- 다양한 partial/final 결과에 대해 올바른 이벤트 타입 emit 검증

**Property 3: Sentence Boundary Detection**
- 다양한 문장 조합에 대해 경계 감지 정확성 검증

**Property 4: Empty Input Validation**
- 다양한 빈/공백 문자열에 대해 400 응답 검증

**Property 6: Event Structure Validity**
- 모든 이벤트 타입에 대해 필수 필드 존재 검증

**Property 7: Session State Accumulation**
- 다양한 transcript/translation 추가에 대해 누적 정확성 검증

**Property 8: Invalid Message Handling**
- 다양한 잘못된 메시지 형식에 대해 INVALID_MESSAGE 에러 검증

### 통합 테스트

- WebSocket 연결 → 오디오 전송 → 전사 → 번역 → 제안 전체 흐름
- AWS 서비스는 LocalStack 또는 moto로 모킹

### 테스트 설정

```python
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*

# hypothesis 설정
hypothesis_profile = ci
```

- 각 속성 기반 테스트는 최소 100회 반복 실행
- 테스트 태그 형식: `Feature: backend-implementation, Property N: [property_text]`
