# Design Document

## Overview

이 설계 문서는 멀티 프로바이더 STT/번역 아키텍처를 정의합니다. 기존 AWS 기반 구현을 유지하면서 OpenAI 프로바이더를 추가하고, Google은 향후 확장을 위한 인터페이스만 설계합니다.

핵심 설계 원칙:
- **Protocol 기반 추상화**: Python Protocol을 사용하여 프로바이더 독립적인 인터페이스 정의
- **Factory 패턴**: `PROVIDER_MODE` 환경 변수에 따라 적절한 구현체 생성
- **기존 코드 최소 변경**: WebSocket 핸들러와 API 엔드포인트는 Protocol만 의존
- **오디오 포맷 정합성**: 프로바이더별 요구사항(AWS 16kHz, OpenAI 24kHz)에 맞춘 리샘플링
- **OpenAI Realtime transcription 세션**: WebSocket 기반 입력 버퍼 + transcription 이벤트 기반 처리
- **프론트 리샘플링 우선**: OpenAI 모드에서는 프론트에서 24kHz PCM을 생성하고, 백엔드는 필요한 경우에만 리샘플링
- **Speaker 고정**: diarization 미지원 프로바이더는 `spk_1` 고정
- **Suggestion 유지**: 질문 제안은 항상 Bedrock 기반으로 유지

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
├─────────────────────────────────────────────────────────────────┤
│  WebSocket Handler (/ws/v1/meetings/{sessionId})                │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────┐    ┌─────────────────────┐                 │
│  │  STT_Protocol   │    │ Translation_Protocol │                 │
│  └────────┬────────┘    └──────────┬──────────┘                 │
│           │                        │                             │
│           ▼                        ▼                             │
│  ┌─────────────────────────────────────────────┐                │
│  │            Service Factory                   │                │
│  │  (creates services based on PROVIDER_MODE)   │                │
│  └─────────────────────────────────────────────┘                │
│           │                        │                             │
│     ┌─────┴─────┐            ┌─────┴─────┐                      │
│     ▼           ▼            ▼           ▼                      │
│  ┌──────┐  ┌────────┐   ┌──────┐  ┌────────┐                   │
│  │ AWS  │  │ OpenAI │   │ AWS  │  │ OpenAI │                   │
│  │ STT  │  │  STT   │   │Trans │  │ Trans  │                   │
│  └──────┘  └────────┘   └──────┘  └────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Provider Mode Enum

```python
from enum import Enum

class ProviderMode(str, Enum):
    AWS = "AWS"
    OPENAI = "OPENAI"
    GOOGLE = "GOOGLE"  # 향후 구현 예정
```

### 2. Normalized Transcript Result

프로바이더 독립적인 전사 결과 모델:

```python
from pydantic import BaseModel

class TranscriptResult(BaseModel):
    is_partial: bool
    text: str
    speaker: str = "spk_1"  # diarization 미지원 시 기본값
```

### 3. STT Service Protocol

```python
from typing import Protocol, AsyncIterator

class STTServiceProtocol(Protocol):
    async def start_stream(self, session_id: str) -> None:
        """오디오 스트리밍 세션 시작"""
        ...

    async def send_audio(self, audio_chunk: bytes) -> None:
        """오디오 청크 전송 (PCM s16le, 프로바이더별 샘플레이트 처리)"""
        ...

    async def stop_stream(self) -> None:
        """스트리밍 세션 종료"""
        ...

    def get_results(self) -> AsyncIterator[TranscriptResult]:
        """정규화된 전사 결과 스트림 반환"""
        ...
```

### 4. Translation Service Protocol

```python
from typing import Protocol

class TranslationServiceProtocol(Protocol):
    async def translate_en_to_ko(self, text: str) -> str:
        """영어 → 한국어 번역"""
        ...

    async def translate_ko_to_en(self, text: str) -> str:
        """한국어 → 영어 번역"""
        ...
```

### 5. Service Factory

```python
def create_stt_service(settings: Settings) -> STTServiceProtocol:
    match settings.provider_mode:
        case ProviderMode.AWS:
            return AWSSTTService(settings)
        case ProviderMode.OPENAI:
            return OpenAISTTService(settings)
        case ProviderMode.GOOGLE:
            raise NotImplementedError("Google STT is planned for future release")
        case _:
            raise ValueError(f"Unsupported provider: {settings.provider_mode}")

def create_translation_service(settings: Settings) -> TranslationServiceProtocol:
    match settings.provider_mode:
        case ProviderMode.AWS:
            return AWSTranslationService(settings)
        case ProviderMode.OPENAI:
            return OpenAITranslationService(settings)
        case ProviderMode.GOOGLE:
            raise NotImplementedError("Google Translation is planned for future release")
        case _:
            raise ValueError(f"Unsupported provider: {settings.provider_mode}")
```

## Data Models

### Settings 확장

```python
class Settings(BaseSettings):
    # Provider 선택
    provider_mode: ProviderMode = Field(
        default=ProviderMode.AWS,
        validation_alias="PROVIDER_MODE"
    )
    
    # 공통 설정
    transcribe_language_code: str = Field("en-US", validation_alias="TRANSCRIBE_LANGUAGE_CODE")
    transcribe_sample_rate: int = 16000
    transcribe_media_encoding: str = "pcm"
    
    # AWS 설정 (기존)
    aws_region: str = Field("ap-northeast-2", validation_alias="AWS_REGION")
    bedrock_translation_model_id: str = Field(...)
    bedrock_quick_translate_model_id: str = Field(...)
    
    # OpenAI 설정
    openai_api_key: str | None = Field(None, validation_alias="OPENAI_API_KEY")
    openai_stt_model: str = Field("gpt-4o-transcribe", validation_alias="OPENAI_STT_MODEL")
    openai_translation_model: str = Field("gpt-4o-mini", validation_alias="OPENAI_TRANSLATION_MODEL")
    openai_stt_language: str = Field("en", validation_alias="OPENAI_STT_LANGUAGE")
    openai_commit_interval_ms: int = Field(1000, validation_alias="OPENAI_COMMIT_INTERVAL_MS")
    
    # Google 설정 (향후 구현)
    google_project_id: str | None = Field(None, validation_alias="GOOGLE_PROJECT_ID")
    google_credentials_path: str | None = Field(None, validation_alias="GOOGLE_APPLICATION_CREDENTIALS")
```

### 언어 코드 매핑

```python
LANGUAGE_CODE_MAPPING = {
    "en-US": "en",
    "en-GB": "en",
    "ko-KR": "ko",
    "ja-JP": "ja",
}

def get_openai_language_code(aws_language_code: str) -> str:
    return LANGUAGE_CODE_MAPPING.get(aws_language_code, aws_language_code.split("-")[0])
```

## Provider Implementations

### AWS STT Service (기존 리팩토링)

```python
class AWSSTTService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = TranscribeStreamingClient(region=settings.aws_region)
        self._stream = None
        self._result_queue: asyncio.Queue[TranscriptResult] = asyncio.Queue()

    async def start_stream(self, session_id: str) -> None:
        self._stream = await self.client.start_stream_transcription(
            language_code=self.settings.transcribe_language_code,
            media_sample_rate_hz=self.settings.transcribe_sample_rate,
            media_encoding=self.settings.transcribe_media_encoding,
            show_speaker_label=True,
        )
        asyncio.create_task(self._process_results())

    async def _process_results(self) -> None:
        """AWS TranscriptEvent를 TranscriptResult로 변환"""
        async for event in self._stream.output_stream:
            result = self._normalize_event(event)
            if result:
                await self._result_queue.put(result)

    def _normalize_event(self, event) -> TranscriptResult | None:
        # AWS 이벤트를 정규화된 TranscriptResult로 변환
        ...

    async def get_results(self) -> AsyncIterator[TranscriptResult]:
        while True:
            result = await self._result_queue.get()
            yield result
```

### OpenAI STT Service

Realtime transcription 세션은 입력 오디오 버퍼를 커밋할 때 전사가 시작됩니다. 실시간성(<2초)을 위해 VAD 자동 커밋 대신 일정 간격으로 버퍼를 커밋하는 전략을 사용하며, `turn_detection`은 비활성화합니다.
프론트는 OpenAI 모드에서 24kHz PCM을 전송하고, 백엔드는 `session.start.sampleRate` 값으로 입력 샘플레이트를 갱신해 필요 시에만 리샘플링합니다.

```python
import asyncio
import websockets
import json
import struct

class OpenAISTTService:
    REALTIME_API_URL = "wss://api.openai.com/v1/realtime"
    # Realtime WS 모델은 gpt-4o-transcribe 사용
    
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._result_queue: asyncio.Queue[TranscriptResult] = asyncio.Queue()
        self._running = False
        self._partial_by_item: dict[str, str] = {}
        self._last_commit_ts: float = 0.0
        # 기본은 프론트 24kHz 입력, 필요 시 session.start로 갱신
        self._input_sample_rate = 24000

    async def start_stream(self, session_id: str) -> None:
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        self._ws = await websockets.connect(
            f"{self.REALTIME_API_URL}?model={self.settings.openai_stt_model}",
            extra_headers=headers,
        )
        
        # 세션 설정 (transcription 전용)
        await self._ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "type": "transcription",
                "audio": {
                    "input": {
                        "format": {
                            "type": "audio/pcm",
                            "rate": 24000,
                        },
                        "transcription": {
                            "model": self.settings.openai_stt_model,
                            "language": self.settings.openai_stt_language,
                        },
                        "turn_detection": None,
                    }
                }
            }
        }))
        
        self._running = True
        asyncio.create_task(self._receive_loop())

    async def send_audio(self, audio_chunk: bytes) -> None:
        if not self._ws:
            return
        
        # 프론트에서 24kHz를 생성하고, 백엔드는 필요 시에만 리샘플링
        resampled = audio_chunk
        if self._input_sample_rate != 24000:
            resampled = self._resample_16k_to_24k(audio_chunk)
        
        # Base64 인코딩하여 전송
        import base64
        audio_b64 = base64.b64encode(resampled).decode()
        await self._ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_b64,
        }))
        await self._maybe_commit_buffer()

    async def _maybe_commit_buffer(self) -> None:
        now = asyncio.get_running_loop().time()
        if now - self._last_commit_ts < self.settings.openai_commit_interval_ms / 1000:
            return
        self._last_commit_ts = now
        if self._ws:
            await self._ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

    def _resample_16k_to_24k(self, audio_16k: bytes) -> bytes:
        """16kHz PCM을 24kHz PCM으로 리샘플링 (선형 보간)"""
        samples_16k = struct.unpack(f"<{len(audio_16k)//2}h", audio_16k)
        # 1.5배 업샘플링 (16000 * 1.5 = 24000)
        if not samples_16k:
            return b""
        out_len = int(len(samples_16k) * 3 / 2)
        samples_24k = []
        for j in range(out_len):
            pos = j * 2 / 3
            i = int(pos)
            frac = pos - i
            left = samples_16k[i]
            right = samples_16k[i + 1] if i + 1 < len(samples_16k) else samples_16k[i]
            sample = int(left * (1 - frac) + right * frac)
            samples_24k.append(sample)
        return struct.pack(f"<{len(samples_24k)}h", *samples_24k)

    async def _receive_loop(self) -> None:
        """WebSocket 메시지 수신 및 처리"""
        while self._running and self._ws:
            try:
                msg = await self._ws.recv()
                data = json.loads(msg)
                
                if data["type"] == "conversation.item.input_audio_transcription.delta":
                    item_id = data.get("item_id", "")
                    delta = data.get("delta") or ""
                    if item_id:
                        self._partial_by_item[item_id] = self._partial_by_item.get(item_id, "") + delta
                        await self._result_queue.put(TranscriptResult(
                            is_partial=True,
                            text=self._partial_by_item[item_id],
                            speaker="spk_1",
                        ))
                elif data["type"] == "conversation.item.input_audio_transcription.completed":
                    item_id = data.get("item_id", "")
                    transcript = data.get("transcript") or ""
                    if item_id and item_id in self._partial_by_item:
                        self._partial_by_item.pop(item_id, None)
                    await self._result_queue.put(TranscriptResult(
                        is_partial=False,
                        text=transcript,
                        speaker="spk_1",
                    ))
                elif data["type"] == "conversation.item.input_audio_transcription.failed":
                    raise RuntimeError("OpenAI transcription failed")
            except websockets.ConnectionClosed:
                break

    async def stop_stream(self) -> None:
        self._running = False
        if self._ws:
            await self._ws.close()

    async def get_results(self) -> AsyncIterator[TranscriptResult]:
        while self._running or not self._result_queue.empty():
            try:
                result = await asyncio.wait_for(self._result_queue.get(), timeout=0.1)
                yield result
            except asyncio.TimeoutError:
                continue
```

### OpenAI Translation Service

```python
from openai import AsyncOpenAI

class OpenAITranslationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def translate_en_to_ko(self, text: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.settings.openai_translation_model,
            messages=[
                {"role": "system", "content": "You are a translator. Translate English to natural Korean. Return only the translation."},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()

    async def translate_ko_to_en(self, text: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.settings.openai_translation_model,
            messages=[
                {"role": "system", "content": "You are a translator. Translate Korean to natural English. Return only the translation."},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip()
```

## Directory Structure

```
apps/api/app/services/
├── __init__.py
├── stt/
│   ├── __init__.py          # STTServiceProtocol, TranscriptResult, create_stt_service
│   ├── aws.py               # AWSSTTService
│   └── openai.py            # OpenAISTTService
├── translation/
│   ├── __init__.py          # TranslationServiceProtocol, create_translation_service
│   ├── aws.py               # AWSTranslationService (기존 BedrockService 리팩토링)
│   └── openai.py            # OpenAITranslationService
├── suggestion.py            # SuggestionService (Bedrock 유지)
├── bedrock.py               # 삭제 예정 (translation/aws.py로 이동)
└── transcribe.py            # 삭제 예정 (stt/aws.py로 이동)
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Provider Mode Validation

*For any* string value provided as `PROVIDER_MODE`, the Settings SHALL accept only "AWS", "OPENAI", or "GOOGLE", and SHALL raise a validation error for any other value.

**Validates: Requirements 1.1, 1.3, 7.4**

### Property 2: Service Factory Correctness

*For any* valid Provider_Mode (AWS or OPENAI), the Service_Factory SHALL create the corresponding STT and Translation service implementations. Specifically:
- AWS → AWSSTTService, AWSTranslationService
- OPENAI → OpenAISTTService, OpenAITranslationService

**Validates: Requirements 7.1, 7.2**

### Property 3: Protocol Conformance

*For any* STT or Translation service implementation, the implementation SHALL have all methods defined in the corresponding Protocol interface with matching signatures.

**Validates: Requirements 2.7, 3.3**

### Property 4: Audio Resampling Correctness

*For any* 16kHz PCM audio input (backend fallback), the resampling function SHALL produce 24kHz PCM output where:
- Output sample count = Input sample count × 1.5
- Output maintains audio integrity (no clipping, proper interpolation)

**Validates: Requirements 5.5, 9.2**

### Property 5: Language Code Mapping

*For any* AWS-style language code (e.g., "en-US", "ko-KR"), the mapping function SHALL produce a valid ISO-639-1 code (e.g., "en", "ko").

**Validates: Requirements 8.5, 9.3**

### Property 6: TranscriptResult Structure

*For any* TranscriptResult instance, it SHALL contain `is_partial` (bool), `text` (str), and `speaker` (str) fields. When speaker diarization is unavailable (OpenAI provider), `speaker` SHALL always be "spk_1".

**Validates: Requirements 2.5, 2.6, 5.6**

### Property 7: Provider-specific Validation

*For any* Provider_Mode selection, the Settings SHALL validate that all required fields for that provider are configured:
- AWS: `aws_region` must be set
- OPENAI: `openai_api_key` must be set

**Validates: Requirements 8.4, 4.5, 5.9**

## Error Handling

### Configuration Errors

| Error Condition | Error Type | Message |
|----------------|------------|---------|
| Invalid PROVIDER_MODE | ValidationError | "provider_mode must be one of: AWS, OPENAI, GOOGLE" |
| Missing OPENAI_API_KEY when OPENAI mode | ValidationError | "openai_api_key is required when provider_mode is OPENAI" |
| Missing AWS credentials when AWS mode | RuntimeError | "AWS credentials not configured" |
| GOOGLE mode selected | NotImplementedError | "Google provider is planned for future release" |

### Runtime Errors

| Error Condition | Error Type | Message |
|----------------|------------|---------|
| STT stream not started | RuntimeError | "STT stream not started" |
| WebSocket connection failed | ConnectionError | "Failed to connect to OpenAI Realtime API" |
| OpenAI transcription failed event | RuntimeError | "OpenAI transcription failed" |
| Translation API error | TranslationError | "Translation failed: {details}" |

## Testing Strategy

### Unit Tests

- Settings validation with various PROVIDER_MODE values
- Service Factory creates correct service types
- Language code mapping for all supported codes
- TranscriptResult model validation

### Property-Based Tests

Property-based testing will use `hypothesis` library for Python:

1. **Provider Mode Validation**: Generate random strings and verify only valid modes are accepted
2. **Audio Resampling**: Generate random 16kHz PCM audio and verify 24kHz output properties
3. **Language Code Mapping**: Generate AWS-style language codes and verify ISO-639-1 output
4. **TranscriptResult Structure**: Generate random TranscriptResult instances and verify field presence

### Integration Tests

- AWS STT service with mock Transcribe client
- OpenAI STT service with mock WebSocket
- Translation services with mock API responses
- End-to-end WebSocket flow with different providers

### Test Configuration

```python
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*

# Property-based test settings
hypothesis_profile = default
```

Each property test will run minimum 100 iterations and be tagged with:
```python
# Feature: multi-provider-stt-translation, Property N: {property_text}
```
