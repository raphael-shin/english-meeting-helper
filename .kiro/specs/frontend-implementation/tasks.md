# Implementation Plan: Frontend Implementation

## Overview

English Meeting Helper 프론트엔드 구현 계획입니다. React + TypeScript + TailwindCSS 기반으로 실시간 회의 지원 UI를 구현합니다. 타입 정의부터 시작하여 lib 모듈, 커스텀 훅, 컴포넌트 순서로 점진적으로 구현합니다.

## Tasks

- [x] 1. 타입 정의 및 프로젝트 설정
  - [x] 1.1 WebSocket 이벤트 타입 정의 (types/events.ts)
    - BaseEvent, ServerPongEvent 정의
    - TranscriptPartialEvent, TranscriptFinalEvent 정의
    - TranslationFinalEvent, SuggestionItem, SuggestionsUpdateEvent 정의
    - ErrorEvent 및 WebSocketEvent 유니온 타입 정의
    - SessionStartMessage, SessionStopMessage, ClientPingMessage 정의
    - ClientControlMessage 유니온 타입 정의
    - _Requirements: 1.2, 1.8, 3.1, 3.2, 4.1, 6.1, 7.1_

  - [x] 1.2 fast-check 테스트 라이브러리 설치
    - devDependencies에 fast-check 추가
    - _Requirements: Testing Strategy_

- [x] 2. Lib 모듈 구현
  - [x] 2.1 WebSocket 클라이언트 구현 (lib/ws.ts)
    - MeetingWsClient 클래스 구현
    - connect, reconnect, sendAudio, sendControl, disconnect 메서드
    - keepalive ping/pong (15s ping, 30s pong timeout)
    - ws/http 스킴 변환 로직
    - 이벤트 파싱 및 핸들러 호출
    - _Requirements: 1.1, 1.3, 1.5, 1.8, 1.9, 1.10_

  - [ ]* 2.2 Write property test for WebSocket event parsing
    - **Property 9: WebSocket Event Type Discrimination**
    - **Validates: Requirements 1.8, 3.1, 3.2, 4.1, 6.1, 7.1**

  - [x] 2.3 오디오 캡처 모듈 구현 (lib/audio.ts)
    - AudioCapture 클래스 구현
    - start, stop 메서드
    - Float32 → PCM16 변환 로직
    - 16kHz mono PCM s16le, 20-100ms 청크 설정
    - _Requirements: 2.1, 2.3, 2.4, 2.5_

  - [x] 2.4 REST API 클라이언트 확장 (lib/api.ts)
    - translateKoToEn 함수 구현
    - TranslateRequest, TranslateResponse 타입
    - 에러 처리 로직 (400 detail 반영)
    - _Requirements: 5.2, 5.7_

- [x] 3. Checkpoint - Lib 모듈 검증
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Custom Hooks 구현
  - [x] 4.1 useMeeting 훅 구현 (hooks/useMeeting.ts)
    - MeetingState 인터페이스 정의
    - WebSocket 이벤트 핸들러 구현
    - startMeeting, stopMeeting, reconnect, dismissError 액션
    - 전사 partial/final 상태 관리
    - 번역 연결 로직 (sourceTs 매칭 + orphan 저장)
    - session.start/session.stop control 전송
    - client.ping/server.pong 상태 처리
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.8, 1.9, 1.10, 3.1, 3.2, 3.3, 3.5, 4.1, 4.3, 4.5, 6.1, 7.1, 7.2, 7.5_

  - [ ]* 4.2 Write property test for transcript state management
    - **Property 3: Transcript Partial/Final State Management**
    - **Validates: Requirements 3.1, 3.2**

  - [ ]* 4.3 Write property test for transcript ordering
    - **Property 4: Transcript Ordering and Speaker Preservation**
    - **Validates: Requirements 3.3, 3.5**

  - [ ]* 4.4 Write property test for translation association
    - **Property 5: Translation Association with Source Transcript**
    - **Validates: Requirements 4.1, 4.3, 4.5**

  - [ ]* 4.5 Write property test for suggestions state
    - **Property 7: Suggestions State Management**
    - **Validates: Requirements 6.1, 6.2, 6.4**

  - [ ]* 4.6 Write property test for error state
    - **Property 8: Error State Management**
    - **Validates: Requirements 7.1, 7.2, 7.5**

  - [x] 4.7 useTranslate 훅 구현 (hooks/useTranslate.ts)
    - TranslateState 인터페이스 정의
    - setInputText, translate, copyToClipboard, clear 액션
    - 로딩 및 에러 상태 관리
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 4.8 Write property test for quick translate state machine
    - **Property 6: Quick Translate State Machine**
    - **Validates: Requirements 5.1, 5.3, 5.4, 5.5**

  - [ ]* 4.9 Write property test for keepalive timeout handling
    - **Property 11: Keepalive Timeout Handling**
    - **Validates: Requirements 1.8, 1.9**

- [x] 5. Checkpoint - Hooks 검증
  - Ensure all tests pass, ask the user if questions arise.


- [x] 6. UI 컴포넌트 구현
  - [x] 6.1 TranscriptItem 컴포넌트 구현 (components/TranscriptItem.tsx)
    - 화자 라벨 표시
    - partial/final 스타일 구분
    - 번역 텍스트 표시 (복수)
    - _Requirements: 3.1, 3.2, 3.5, 4.1, 4.2_

  - [x] 6.2 TranslationItem 컴포넌트 구현 (components/TranslationItem.tsx)
    - orphan 번역 표시
    - _Requirements: 4.1, 4.3, 4.5_

  - [x] 6.3 ErrorBanner 컴포넌트 구현 (components/ErrorBanner.tsx)
    - 에러 메시지 표시
    - Retry 버튼 (retryable인 경우)
    - Dismiss 버튼
    - ARIA role="alert" 적용
    - _Requirements: 7.1, 7.2, 7.4, 7.5, 9.1_

  - [x] 6.4 TranscribeControls 컴포넌트 구현 (components/TranscribeControls.tsx)
    - Start/Stop 버튼
    - 연결 상태 표시
    - ARIA labels 적용
    - _Requirements: 1.1, 1.3, 2A.1, 2A.2, 2A.3, 2A.4, 9.1_

  - [x] 6.5 MicSettingsPanel 컴포넌트 구현 (components/MicSettingsPanel.tsx)
    - 마이크 선택/테스트 UI
    - _Requirements: 2A.5_

  - [x] 6.6 TopBar 컴포넌트 구현 (components/TopBar.tsx)
    - 전사 상태 표시 + MicSettingsPanel + TranscribeControls 통합
    - _Requirements: 2A.1, 2A.2, 2A.3, 2A.4, 2A.5_

  - [x] 6.7 MeetingPanel 컴포넌트 구현 (components/MeetingPanel.tsx)
    - 전사 목록 표시 (TranscriptItem/TranslationItem 사용)
    - 자동 스크롤 구현
    - ErrorBanner 통합
    - ARIA live region 적용
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.5, 7.1, 9.1, 9.3_

  - [x] 6.8 QuickTranslate 컴포넌트 구현 (components/QuickTranslate.tsx)
    - 한국어 입력 textarea
    - Translate/Clear 버튼
    - 번역 결과 표시
    - Copy to clipboard 버튼
    - 로딩 및 에러 상태 표시
    - ARIA labels 및 describedby 적용
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 9.1_

  - [x] 6.9 SuggestionsPanel 컴포넌트 구현 (components/SuggestionsPanel.tsx)
    - 제안 목록 표시 (영어/한국어)
    - 클릭 시 클립보드 복사
    - 빈 상태 placeholder
    - ARIA labels 적용
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 9.1_

- [x] 7. App 통합 및 레이아웃
  - [x] 7.1 App 컴포넌트 업데이트 (App.tsx)
    - useMeeting 훅 연결
    - TopBar, MeetingPanel, QuickTranslate, SuggestionsPanel 통합
    - 반응형 그리드 레이아웃 (md:grid-cols-3)
    - 환경 변수 설정 (VITE_WS_BASE_URL, VITE_API_BASE_URL)
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 7.2 Write unit tests for App component
    - 컴포넌트 렌더링 검증
    - 훅 연결 검증
    - _Requirements: 8.1, 8.2_

- [x] 8. Checkpoint - 전체 통합 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. 접근성 및 마무리
  - [ ] 9.1 접근성 검증 및 개선
    - 모든 interactive 요소에 ARIA labels 확인
    - 키보드 네비게이션 테스트
    - ARIA live regions 동작 확인
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ]* 9.2 Write accessibility tests
    - ARIA labels 존재 검증
    - role 속성 검증
    - _Requirements: 9.1, 9.3_

- [ ] 10. Final Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- fast-check 라이브러리를 사용하여 속성 기반 테스트 구현
