# Requirements Document

## Introduction

English Meeting Helper 프론트엔드 구현 요구사항입니다. React + TypeScript 기반으로 실시간 음성 전사, 번역, 빠른 한→영 번역, AI 질문 제안 기능을 제공하는 웹 UI를 구현합니다. 백엔드 WebSocket 및 REST API와 연동하여 실시간 회의 지원 경험을 제공합니다.

## Glossary

- **Meeting_Panel**: 실시간 전사 및 번역 결과를 표시하는 메인 UI 컴포넌트
- **Quick_Translate**: 한국어 입력을 영어로 빠르게 번역하는 UI 컴포넌트
- **Suggestions_Panel**: AI가 제안하는 영어 질문을 표시하는 UI 컴포넌트
- **Audio_Capture**: 마이크 오디오를 캡처하여 WebSocket으로 전송하는 모듈
- **WebSocket_Client**: 백엔드 WebSocket 서버와 통신하는 클라이언트 모듈
- **Session**: 회의 세션을 나타내는 상태 단위 (sessionId로 식별)
- **Transcript**: 음성 전사 결과 (partial 또는 final)
- **Translation**: 전사된 영어 텍스트의 한국어 번역

## Requirements

### Requirement 1: 회의 세션 관리

**User Story:** As a user, I want to start and stop a meeting session, so that I can control when audio is captured and transcribed.

#### Acceptance Criteria

1. WHEN a user clicks the "Start Meeting" button, THE Meeting_Panel SHALL generate a client sessionId and initiate a WebSocket connection to `/ws/v1/meetings/{sessionId}`
2. WHEN the WebSocket connection is established, THE WebSocket_Client SHALL send a `session.start` control message with `sampleRate: 16000`, `format: "pcm_s16le"`, `lang: "en-US"`
3. AFTER sending `session.start`, THE Meeting_Panel SHALL mark the session as active and display a "session.start" confirmation (client-side status)
4. WHEN a user clicks the "Stop Meeting" button, THE WebSocket_Client SHALL send a `session.stop` control message, THE Meeting_Panel SHALL stop audio capture, and close the WebSocket connection gracefully
5. WHEN the WebSocket connection is closed, THE Meeting_Panel SHALL display a "session.stop" confirmation and clear the active session indicator (client-side status)
6. IF the WebSocket connection fails or is unexpectedly closed, THEN THE Meeting_Panel SHALL display an error message and offer a reconnect option
7. THE sessionId SHALL be generated on the client using `crypto.randomUUID()`; it MUST be lowercase and match `^[a-z0-9-]{36}$`
8. THE WebSocket_Client SHALL send `client.ping` every 15 seconds and record the round-trip time when receiving `server.pong`
9. IF no `server.pong` is received within 30 seconds, THEN THE Meeting_Panel SHALL show a connection error and offer reconnect
10. WHEN a reconnect is requested, THE WebSocket_Client SHALL create a new connection using a newly generated sessionId

### Requirement 2: 오디오 캡처 및 스트리밍

**User Story:** As a user, I want my microphone audio to be captured and streamed to the server, so that my speech can be transcribed in real-time.

#### Acceptance Criteria

1. WHEN a meeting session starts, THE Audio_Capture SHALL request microphone permission from the browser
2. IF microphone permission is denied, THEN THE Audio_Capture SHALL display an error message explaining the permission requirement
3. WHEN microphone access is granted, THE Audio_Capture SHALL capture audio at 16kHz sample rate in mono PCM s16le format
4. WHILE a meeting session is active, THE Audio_Capture SHALL stream 20-100ms binary audio chunks (no base64) to the WebSocket connection
5. WHEN a meeting session stops, THE Audio_Capture SHALL release the microphone resource

### Requirement 2A: 상단 전사 컨트롤 UI

**User Story:** As a user, I want quick access to start/stop transcription and microphone settings, so that I can control the session from the top bar.

#### Acceptance Criteria

1. THE Application SHALL place the Start/Stop transcription button at the top-right of the header
2. WHEN transcription is idle, THE button label SHALL be "Start transcribing"
3. WHEN transcription is active, THE button label SHALL be "Stop" and the visual style SHALL indicate a destructive action
4. WHILE transcription is active, THE header SHALL display a clear status indicator (text + simple visualizer such as dots/waves)
5. THE header SHALL include a settings button that opens microphone selection and test controls

### Requirement 3: 실시간 전사 표시

**User Story:** As a user, I want to see real-time transcription of the meeting audio, so that I can follow the conversation in text form.

#### Acceptance Criteria

1. WHEN a `transcript.partial` event is received, THE Meeting_Panel SHALL display the partial text with a visual indicator (e.g., italics or lighter color)
2. WHEN a `transcript.final` event is received, THE Meeting_Panel SHALL append the completed sentence to the history region and clear the matching live entry
3. THE Meeting_Panel SHALL split the transcript area into a live region and a history region with a 2:3 height ratio
4. THE live region SHALL show active partial transcripts and update in place as new partial events arrive (including partial updates emitted from final chunks)
5. THE history region SHALL display finalized sentence chunks in reverse chronological order (latest first) with speaker labels
6. WHILE transcripts are displayed, THE Meeting_Panel SHALL auto-scroll to show the latest transcript in each region
7. WHEN a transcript contains speaker information, THE Meeting_Panel SHALL display the speaker label alongside the text
8. WHEN transcript events include `ts`, THE Meeting_Panel SHALL treat it as epoch milliseconds and use it for ordering/association
9. IF a live partial transcript receives no updates for 10 seconds, THE Meeting_Panel SHALL remove it from the live region to prevent stale entries

### Requirement 4: 실시간 번역 표시

**User Story:** As a user, I want to see Korean translations of the English transcripts, so that I can understand the meeting content in my native language.

#### Acceptance Criteria

1. WHEN a `translation.final` event is received, THE Meeting_Panel SHALL display the Korean translation below or alongside the corresponding English transcript
2. WHEN displaying translations, THE Meeting_Panel SHALL visually distinguish translations from original transcripts (e.g., different color or indentation)
3. WHEN a translation is displayed, THE Meeting_Panel SHALL associate it with its source transcript using the `sourceTs` field (epoch ms)
4. IF multiple translations share the same `sourceTs`, THE Meeting_Panel SHALL stack them under the same source transcript in received order
5. IF a translation arrives for a partial transcript (draft update), THE Meeting_Panel SHALL replace the draft translation for that partial transcript with the latest one
6. Draft translations SHOULD render in the live region alongside partial transcripts
7. IF a matching transcript cannot be found, THE Meeting_Panel SHALL still display the translation in chronological order by received `ts`

### Requirement 5: 빠른 한→영 번역

**User Story:** As a user, I want to quickly translate Korean text to English, so that I can prepare responses during the meeting.

#### Acceptance Criteria

1. WHEN a user enters Korean text in the Quick_Translate input field, THE Quick_Translate SHALL enable the translate button
2. WHEN a user clicks the translate button or presses Enter, THE Quick_Translate SHALL send a POST request to `/api/v1/translate/ko-en` with JSON body `{ "text": "<korean>" }`
3. WHEN a translation response is received, THE Quick_Translate SHALL display `translatedText` from `{ "translatedText": "<english>" }` in the output area
4. WHILE a translation request is in progress, THE Quick_Translate SHALL display a loading indicator and disable the input
5. IF the translation request fails, THEN THE Quick_Translate SHALL display an error message
6. WHEN a user clicks the copy button, THE Quick_Translate SHALL copy the translated text to the clipboard and show a confirmation
7. IF the API returns HTTP 400, THEN THE Quick_Translate SHALL display the error message from `detail`

### Requirement 6: AI 질문 제안

**User Story:** As a user, I want to see AI-suggested questions based on the meeting context, so that I can participate more effectively.

#### Acceptance Criteria

1. WHEN a `suggestions.update` event is received, THE Suggestions_Panel SHALL display the suggested questions (up to 5 items)
2. WHEN displaying suggestions, THE Suggestions_Panel SHALL show both English and Korean versions (if available)
3. WHEN a user clicks on a suggestion, THE Suggestions_Panel SHALL copy the English text to the clipboard
4. WHEN new suggestions arrive, THE Suggestions_Panel SHALL replace the previous suggestions with the new ones
5. WHILE no suggestions are available, THE Suggestions_Panel SHALL display a placeholder message

### Requirement 6.1: AI Suggestions Prompt

**User Story:** As a user, I want to provide a system prompt for AI suggestions, so that the suggested questions better align with my meeting goals.

#### Acceptance Criteria

1. WHEN a user updates the suggestions prompt and clicks Apply, THE client SHALL send a `suggestions.prompt` control message over WebSocket
2. IF the WebSocket is not connected, THEN the client SHALL queue the prompt and apply it once connected
3. THE prompt input SHOULD explain the expected content (meeting goals, constraints, key points)

### Requirement 7: 에러 처리 및 표시

**User Story:** As a user, I want to see clear error messages when something goes wrong, so that I can understand and potentially resolve issues.

#### Acceptance Criteria

1. WHEN an `error` event is received via WebSocket, THE Meeting_Panel SHALL display the error message to the user
2. WHEN an error is retryable (based on `retryable` field), THE Meeting_Panel SHALL offer a retry option
3. WHEN a network error occurs, THE Meeting_Panel SHALL display a connection error message
4. WHEN displaying errors, THE Meeting_Panel SHALL use appropriate visual styling (e.g., red color, warning icon)
5. WHEN an error is displayed, THE Meeting_Panel SHALL allow the user to dismiss it
6. THE client SHALL handle the following error codes at minimum: `TRANSCRIBE_STREAM_ERROR`, `BEDROCK_ERROR`, `INVALID_MESSAGE`, `SESSION_NOT_FOUND`

### Requirement 8: 반응형 레이아웃

**User Story:** As a user, I want the application to work well on different screen sizes, so that I can use it on various devices.

#### Acceptance Criteria

1. WHEN the viewport width is 768px or greater, THE Application SHALL display Meeting_Panel, Quick_Translate, and Suggestions_Panel in a three-column layout
2. WHEN the viewport width is less than 768px, THE Application SHALL stack the panels vertically
3. WHILE the layout changes, THE Application SHALL maintain readability and usability of all components
4. THE Application SHALL use TailwindCSS utility classes for responsive styling

### Requirement 9: 접근성

**User Story:** As a user with accessibility needs, I want the application to be accessible, so that I can use it with assistive technologies.

#### Acceptance Criteria

1. THE Application SHALL provide appropriate ARIA labels for all interactive elements
2. THE Application SHALL support keyboard navigation for all interactive elements
3. WHEN displaying status changes (e.g., session start/stop, new transcript), THE Application SHALL announce them to screen readers using ARIA live regions
4. THE Application SHALL maintain sufficient color contrast ratios (WCAG AA compliance)
