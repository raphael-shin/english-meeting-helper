# Implementation Plan: Backend Implementation

## Overview

English Meeting Helper 백엔드를 구현합니다. 기존 스켈레톤(`apps/api`)을 기반으로 AWS Transcribe Streaming, Bedrock 번역, AI 질문 제안 기능을 추가합니다. Python 3.11+, FastAPI, Pydantic v2를 사용합니다.

## Tasks

- [x] 1. Core 설정 및 의존성 추가
  - [x] 1.1 pyproject.toml 의존성 업데이트
    - amazon-transcribe, boto3, pydantic-settings 추가
    - hypothesis (테스트용) 추가
    - _Requirements: 1.1, 10.1-10.5_
  - [x] 1.2 app/core/config.py 생성
    - Pydantic Settings 기반 환경 설정 클래스
    - AWS_REGION, TRANSCRIBE_LANGUAGE_CODE, BEDROCK_*_MODEL_ID, CORS_ORIGINS
    - _Requirements: 10.1-10.5_
  - [x] 1.3 app/core/logging.py 생성
    - 구조화된 로깅 설정
    - _Requirements: 9.6_

- [x] 2. Domain 모델 정의
  - [x] 2.1 app/domain/models/events.py 생성
    - BaseEvent, SessionStartEvent, SessionStopEvent
    - TranscriptPartialEvent, TranscriptFinalEvent
    - TranslationFinalEvent, SuggestionsUpdateEvent, ErrorEvent
    - 외부 인터페이스는 camelCase, `ts`는 epoch ms 사용
    - _Requirements: 6.1-6.5_
  - [x]* 2.2 Property 6: Event Structure Validity 테스트 작성
    - **Property 6: Event Structure Validity**
    - 모든 이벤트 타입에 대해 필수 필드 존재 검증
    - **Validates: Requirements 6.1, 6.3, 6.5**
  - [x] 2.3 app/domain/models/translate.py 생성
    - TranslateRequest, TranslateResponse 모델
    - _Requirements: 4.1, 4.3_
  - [x] 2.4 app/domain/models/session.py 생성
    - MeetingSession 클래스 (인메모리 세션 관리)
    - 문장 경계 감지 로직 포함 (`.`, `!`, `?`, 1~2문장 버퍼)
    - _Requirements: 7.1-7.4, 3.5_
  - [x]* 2.5 Property 3: Sentence Boundary Detection 테스트 작성
    - **Property 3: Sentence Boundary Detection**
    - 다양한 문장 조합에 대해 경계 감지 정확성 검증
    - **Validates: Requirements 3.5**
  - [x]* 2.6 Property 7: Session State Accumulation 테스트 작성
    - **Property 7: Session State Accumulation**
    - transcript/translation 추가에 대해 누적 정확성 검증
    - **Validates: Requirements 7.2**

- [x] 3. Checkpoint - 모델 테스트 확인
  - pytest 실행하여 모델 테스트 통과 확인
  - 문제 발생 시 사용자에게 질문

- [x] 4. Bedrock Service 구현
  - [x] 4.1 app/services/bedrock.py 생성
    - BedrockService 클래스
    - translate_en_to_ko (Nova 2 Lite)
    - translate_ko_to_en (Claude Haiku)
    - _invoke_model 내부 메서드
    - _Requirements: 3.2, 4.2_
  - [x] 4.2 Bedrock Service 단위 테스트 작성
    - moto 또는 mock을 사용한 테스트
    - _Requirements: 3.2, 4.2_

- [x] 5. Transcribe Service 구현
  - [x] 5.1 app/services/transcribe.py 생성
    - TranscribeService 클래스
    - start_stream, send_audio, stop_stream, get_results
    - _Requirements: 2.1-2.6_
  - [x] 5.2 Transcribe Service 단위 테스트 작성
    - mock을 사용한 스트리밍 테스트
    - _Requirements: 2.1-2.6_

- [x] 6. Suggestion Service 구현
  - [x] 6.1 app/services/suggestion.py 생성
    - SuggestionService 클래스
    - generate_suggestions 메서드 (3+ transcripts 임계값)
    - 미팅 진행 속도 기반 업데이트 트리거 고려 (동일 화자 연속 3문장 또는 Transcribe 화자 라벨 변경)
    - _Requirements: 5.1-5.5_
  - [x]* 6.2 Property 5: Suggestion Generation Threshold 테스트 작성
    - **Property 5: Suggestion Generation Threshold**
    - 3개 미만 transcript에서는 빈 배열, 3개 이상에서는 2-3개 질문 생성
    - **Validates: Requirements 5.1, 5.3, 5.4**

- [x] 7. Checkpoint - 서비스 테스트 확인
  - pytest 실행하여 서비스 테스트 통과 확인
  - 문제 발생 시 사용자에게 질문

- [x] 8. REST API 구현
  - [x] 8.1 app/api/translate.py 생성
    - POST /api/v1/translate/ko-en 엔드포인트
    - 빈 입력 검증 (400 에러)
    - _Requirements: 4.1-4.4_
  - [x]* 8.2 Property 4: Empty Input Validation 테스트 작성
    - **Property 4: Empty Input Validation**
    - 빈/공백 문자열에 대해 400 응답 검증
    - **Validates: Requirements 4.4**
  - [x] 8.3 app/api/health.py 업데이트 (필요시)
    - 기존 health 엔드포인트 확인/유지
    - _Requirements: 8.1, 8.2_
  - [x] 8.4 app/api/__init__.py 라우터 등록
    - translate 라우터 추가
    - _Requirements: 4.1_

- [x] 9. WebSocket Handler 구현
  - [x] 9.1 app/ws/meetings.py 업데이트
    - 기존 echo placeholder를 실제 구현으로 교체
    - 오디오 수신 → Transcribe 스트리밍
    - Transcribe 결과 → 이벤트 emit
    - `{sessionId}`는 클라이언트 제공 값으로 세션 바인딩
    - 오디오 청크 20~100ms 단위 수신 가정/검증
    - 이벤트 필드 camelCase + `ts` epoch ms 준수
    - _Requirements: 2.1-2.6, 6.1-6.5_
  - [x]* 9.2 Property 1: Transcript Event Emission 테스트 작성
    - **Property 1: Transcript Event Emission**
    - partial/final 결과에 대해 올바른 이벤트 타입 emit 검증
    - **Validates: Requirements 2.5, 2.6**
  - [x] 9.3 번역 및 제안 통합
    - transcript.final → 번역 → translation.final
    - 3+ transcripts + (동일 화자 연속 3문장 또는 Transcribe 화자 라벨 변경) → 제안 생성 → suggestions.update
    - _Requirements: 3.1, 3.3, 5.1, 5.4_
  - [x]* 9.4 Property 2: Translation Flow Integrity 테스트 작성
    - **Property 2: Translation Flow Integrity**
    - transcript.final 후 translation.final 이벤트 emit 검증
    - **Validates: Requirements 3.1, 3.3**
  - [x] 9.5 에러 처리 구현
    - TRANSCRIBE_STREAM_ERROR, BEDROCK_ERROR, INVALID_MESSAGE, SESSION_NOT_FOUND 처리
    - _Requirements: 9.1-9.6_
  - [x]* 9.6 Property 8: Invalid Message Handling 테스트 작성
    - **Property 8: Invalid Message Handling**
    - 잘못된 메시지 형식에 대해 INVALID_MESSAGE 에러 검증
    - **Validates: Requirements 9.3**

- [x] 10. Checkpoint - API/WebSocket 테스트 확인
  - pytest 실행하여 전체 테스트 통과 확인
  - 문제 발생 시 사용자에게 질문

- [x] 11. main.py 통합 및 CORS 설정
  - [x] 11.1 app/main.py 업데이트
    - CORS 미들웨어 추가
    - 서비스 의존성 주입 설정
    - 라우터 등록 확인
    - _Requirements: 10.5_
  - [x] 11.2 requirements.txt 업데이트
    - pyproject.toml과 동기화
    - _Requirements: 1.1_

- [x] 12. 통합 테스트 작성
  - [x] 12.1 tests/test_integration.py 생성
    - WebSocket 연결 → 이벤트 흐름 테스트
    - REST API 번역 테스트
    - AWS 서비스는 mock 사용
    - _Requirements: 2.1-2.6, 3.1-3.5, 4.1-4.4_

- [x] 13. Final Checkpoint - 전체 테스트 확인
  - `npm run test:api` 실행하여 모든 테스트 통과 확인
  - uvicorn 실행하여 서버 기동 확인
  - 문제 발생 시 사용자에게 질문

## Notes

- `*` 표시된 태스크는 선택적이며, 빠른 MVP를 위해 건너뛸 수 있습니다
- 각 태스크는 특정 요구사항을 참조하여 추적 가능합니다
- Checkpoint에서 테스트 실패 시 이전 태스크를 수정합니다
- Property 테스트는 해당 기능 구현 직후에 배치하여 조기에 오류를 발견합니다
- AWS 서비스 테스트는 moto 또는 mock을 사용하여 로컬에서 실행 가능하게 합니다
