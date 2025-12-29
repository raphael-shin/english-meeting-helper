# Requirements Document: Backend Implementation

## Introduction

English Meeting Helper 백엔드 구현 요구사항 문서입니다. FastAPI 기반으로 실시간 음성 전사(AWS Transcribe Streaming), 실시간 번역(AWS Bedrock Nova 2 Lite), 빠른 한→영 번역(Claude Haiku), AI 질문 제안 기능을 구현합니다.

## Glossary

- **API_Server**: FastAPI 기반 백엔드 서버
- **Transcribe_Service**: AWS Transcribe Streaming을 래핑하는 서비스 어댑터
- **Translation_Service**: AWS Bedrock을 통한 번역 서비스 어댑터
- **Suggestion_Service**: 회의 맥락 기반 질문 제안 서비스
- **WebSocket_Handler**: 실시간 오디오 스트리밍 및 이벤트 처리 핸들러
- **Session**: 하나의 회의 세션 (인메모리 관리)
- **Transcript**: 음성에서 변환된 텍스트
- **PCM_Audio**: 16kHz mono signed 16-bit little-endian 오디오 포맷

## Requirements

### Requirement 1: AWS 자격증명 설정

**User Story:** As a developer, I want the backend to use AWS temporary credentials, so that I can securely access AWS services without hardcoding access keys.

#### Acceptance Criteria

1. THE API_Server SHALL use AWS SDK default credential chain for authentication
2. WHEN running locally, THE API_Server SHALL use credentials from AWS CLI profile or environment variables (AWS_PROFILE, AWS_REGION)
3. WHEN deployed to AWS, THE API_Server SHALL use IAM role credentials provided by the execution environment
4. THE API_Server SHALL NOT require AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY to be explicitly configured

### Requirement 2: 실시간 음성 전사 (AWS Transcribe Streaming)

**User Story:** As a user, I want my English speech to be transcribed in real-time, so that I can see what is being said during the meeting.

#### Acceptance Criteria

1. WHEN a WebSocket connection is established to `/ws/v1/meetings/{sessionId}`, THE WebSocket_Handler SHALL accept the connection and initialize a transcription session
2. WHEN binary audio frames (PCM 16kHz mono s16le) are received, THE Transcribe_Service SHALL stream them to AWS Transcribe Streaming
3. THE API_Server SHALL receive audio in 20~100ms chunk sizes for low-latency streaming
4. THE Transcribe_Service SHALL use language code `en-US` for English transcription
5. WHEN AWS Transcribe returns partial results, THE WebSocket_Handler SHALL send a `transcript.partial` event to the client
6. WHEN AWS Transcribe returns final results, THE WebSocket_Handler SHALL append them to a sentence buffer and emit `transcript.final` events only for completed sentence chunks
7. THE API_Server SHALL achieve transcription latency of less than 2 seconds from audio input to transcript output

### Requirement 3: 실시간 영→한 번역

**User Story:** As a user, I want the transcribed English text to be translated to Korean in real-time, so that I can understand the meeting content.

#### Acceptance Criteria

1. WHEN a `transcript.final` event (sentence chunk) is generated, THE Translation_Service SHALL translate the English text to Korean
2. THE Translation_Service SHALL use AWS Bedrock with model `apac.amazon.nova-2-lite-v1:0` for English to Korean translation
3. WHEN translation is complete, THE WebSocket_Handler SHALL send a `translation.final` event to the client
4. THE API_Server SHALL achieve translation latency of less than 3 seconds from transcript to translation output
5. THE Translation_Service SHALL detect sentence boundaries using `.`, `!`, `?` and buffer 1-2 sentence chunks for translation
6. WHEN a `transcript.partial` contains a complete sentence boundary, THE WebSocket_Handler SHALL emit a `translation.final` event for that sentence
7. WHEN no hard sentence boundary is detected, THE WebSocket_Handler SHOULD emit interim translations based on soft boundaries (e.g., `,`, `;`, `:` or connective words) and time/length thresholds to keep updates responsive

### Requirement 4: 빠른 한→영 번역 (REST API)

**User Story:** As a user, I want to quickly translate my Korean text to English, so that I can prepare what to say in the meeting.

#### Acceptance Criteria

1. WHEN a POST request is made to `/api/v1/translate/ko-en` with Korean text, THE Translation_Service SHALL translate it to English
2. THE Translation_Service SHALL use AWS Bedrock with model `apac.anthropic.claude-haiku-4-5-20251001-v1:0` for Korean to English translation
3. THE API_Server SHALL return the translated English text in the response body
4. IF the input text is empty or invalid, THEN THE API_Server SHALL return HTTP 400 with an error message

### Requirement 5: AI 질문 제안

**User Story:** As a user, I want AI to suggest relevant English questions based on the meeting context, so that I can participate more actively in the discussion.

#### Acceptance Criteria

1. WHEN sufficient meeting context is accumulated (3+ final transcripts), THE Suggestion_Service SHALL generate question suggestions
2. THE Suggestion_Service SHALL use AWS Bedrock with model `apac.amazon.nova-2-lite-v1:0` for generating suggestions
3. THE Suggestion_Service SHALL generate up to 5 contextually relevant English questions
4. WHEN suggestions are generated, THE WebSocket_Handler SHALL send a `suggestions.update` event to the client
5. THE suggestions SHALL be updated based on meeting pace, such as when either (a) the Transcribe diarization speaker label changes between consecutive `transcript.final` events or (b) the same speaker label produces 3 consecutive `transcript.final` events since the last suggestion update
6. WHEN a `suggestions.prompt` control message is received, THE WebSocket_Handler SHALL persist the prompt for the session and apply it to subsequent suggestion generation

### Requirement 6: WebSocket 이벤트 프로토콜

**User Story:** As a frontend developer, I want a well-defined WebSocket event protocol, so that I can properly handle real-time updates.

#### Acceptance Criteria

1. THE WebSocket_Handler SHALL use JSON text frames for control messages and events
2. THE WebSocket_Handler SHALL use binary frames for audio data (client → server only)
3. WHEN sending events, THE WebSocket_Handler SHALL include event type, `ts` (epoch milliseconds), and payload
4. THE WebSocket_Handler SHALL support the following event types: `session.start`, `session.stop`, `transcript.partial`, `transcript.final`, `translation.final`, `suggestions.update`, `error`
5. WHEN an error occurs, THE WebSocket_Handler SHALL send an `error` event with error code and message

### Requirement 7: 세션 관리 (인메모리)

**User Story:** As a user, I want my meeting session to be managed properly, so that transcripts and translations are associated correctly.

#### Acceptance Criteria

1. WHEN a WebSocket connection is established to `/ws/v1/meetings/{sessionId}`, THE API_Server SHALL create an in-memory session bound to the client-provided `sessionId`
2. THE Session SHALL store accumulated transcripts and translations for the duration of the connection
3. WHEN the WebSocket connection is closed, THE API_Server SHALL clean up the session resources
4. THE API_Server SHALL support only one active session per WebSocket connection

### Requirement 8: Health Check 엔드포인트

**User Story:** As an operator, I want a health check endpoint, so that I can monitor the API server status.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/v1/health`, THE API_Server SHALL return HTTP 200 with `{"status": "ok"}`
2. THE health endpoint SHALL be available without authentication

### Requirement 9: 에러 처리

**User Story:** As a user, I want clear error messages when something goes wrong, so that I can understand and resolve issues.

#### Acceptance Criteria

1. IF AWS Transcribe connection fails, THEN THE WebSocket_Handler SHALL send an `error` event with code `TRANSCRIBE_STREAM_ERROR`
2. IF AWS Bedrock request fails, THEN THE API_Server SHALL return an appropriate error response (REST) or `error` event (WebSocket) with code `BEDROCK_ERROR`
3. IF a client sends an invalid control message or payload, THEN THE WebSocket_Handler SHALL send an `error` event with code `INVALID_MESSAGE`
4. IF the requested sessionId is not found or invalid, THEN THE WebSocket_Handler SHALL send an `error` event with code `SESSION_NOT_FOUND`
5. IF WebSocket connection is interrupted, THEN THE API_Server SHALL gracefully clean up resources
6. WHEN an unexpected error occurs, THE API_Server SHALL log the error details and return a generic error message to the client

### Requirement 10: 환경 설정

**User Story:** As a developer, I want configurable environment variables, so that I can customize the backend behavior for different environments.

#### Acceptance Criteria

1. THE API_Server SHALL read `AWS_REGION` environment variable (default: `ap-northeast-2`)
2. THE API_Server SHALL read `TRANSCRIBE_LANGUAGE_CODE` environment variable (default: `en-US`)
3. THE API_Server SHALL read `BEDROCK_TRANSLATION_MODEL_ID` environment variable (default: `apac.amazon.nova-2-lite-v1:0`)
4. THE API_Server SHALL read `BEDROCK_QUICK_TRANSLATE_MODEL_ID` environment variable (default: `apac.anthropic.claude-haiku-4-5-20251001-v1:0`)
5. THE API_Server SHALL read `CORS_ORIGINS` environment variable for CORS configuration
