# Implementation Plan: Multi-Provider STT/Translation

## Overview

기존 AWS 기반 STT/번역 서비스를 멀티 프로바이더 아키텍처로 리팩토링하고, OpenAI 프로바이더를 추가합니다. Protocol 기반 추상화와 Factory 패턴을 사용하여 프로바이더 전환이 용이하도록 구현합니다.

## Tasks

- [ ] 1. Core 모델 및 설정 확장
  - [ ] 1.1 ProviderMode Enum 및 TranscriptResult 모델 생성
    - `app/domain/models/provider.py` 파일 생성
    - ProviderMode Enum (AWS, OPENAI, GOOGLE) 정의
    - TranscriptResult Pydantic 모델 정의 (is_partial, text, speaker)
    - _Requirements: 1.1, 2.5_
  - [ ] 1.2 Settings 클래스에 프로바이더 설정 추가
    - `provider_mode` 필드 추가 (기본값: AWS)
    - OpenAI 설정 필드 추가 (openai_api_key, openai_stt_model, openai_translation_model, openai_stt_language, openai_commit_interval_ms)
    - Google 설정 필드 예약 (google_project_id, google_credentials_path)
    - 프로바이더별 필수 필드 검증 로직 추가
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 8.1, 8.2, 8.3, 8.4_
  - [ ]* 1.3 Property test: Provider Mode Validation
    - **Property 1: Provider Mode Validation**
    - **Validates: Requirements 1.1, 1.3, 7.4**

- [ ] 2. STT Service 리팩토링
  - [ ] 2.1 STT Protocol 및 Factory 생성
    - `app/services/stt/__init__.py` 파일 생성
    - STTServiceProtocol 정의
    - create_stt_service 팩토리 함수 구현
    - 언어 코드 매핑 함수 (get_openai_language_code) 구현
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 7.1, 8.5_
  - [ ] 2.2 AWS STT Service 리팩토링
    - `app/services/stt/aws.py` 파일 생성
    - 기존 TranscribeService를 AWSSTTService로 리팩토링
    - TranscriptResult 정규화 로직 추가
    - _Requirements: 4.1, 4.3, 4.5_
  - [ ] 2.3 OpenAI STT Service 구현
    - `app/services/stt/openai.py` 파일 생성
    - OpenAI Realtime API WebSocket 연결 구현
    - 16kHz → 24kHz 리샘플링 함수 구현 (백엔드 fallback)
    - input_audio_buffer.commit 주기적 호출 로직 구현
    - partial/final transcript 처리 로직 구현
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 5.6, 5.7, 5.9_
  - [ ] 2.6 OpenAI Realtime 전사 버퍼 커밋/에러 처리 통합
    - input_audio_buffer.commit 주기/타이밍 검증 (지연 <2초 목표)
    - transcription.failed 이벤트 처리 및 에러 전파
    - _Requirements: 5.1, 5.7, 9.4_
  - [ ]* 2.4 Property test: Audio Resampling Correctness
    - **Property 4: Audio Resampling Correctness**
    - **Validates: Requirements 5.5, 9.2**
  - [ ]* 2.5 Property test: Language Code Mapping
    - **Property 5: Language Code Mapping**
    - **Validates: Requirements 8.5, 9.3**

- [ ] 3. Translation Service 리팩토링
  - [ ] 3.1 Translation Protocol 및 Factory 생성
    - `app/services/translation/__init__.py` 파일 생성
    - TranslationServiceProtocol 정의
    - create_translation_service 팩토리 함수 구현
    - _Requirements: 3.1, 3.2, 7.2_
  - [ ] 3.2 AWS Translation Service 리팩토링
    - `app/services/translation/aws.py` 파일 생성
    - 기존 BedrockService를 AWSTranslationService로 리팩토링
    - _Requirements: 4.2, 4.4_
  - [ ] 3.3 OpenAI Translation Service 구현
    - `app/services/translation/openai.py` 파일 생성
    - AsyncOpenAI 클라이언트를 사용한 번역 구현
    - translate_en_to_ko, translate_ko_to_en 메서드 구현
    - _Requirements: 5.2, 5.8_

- [ ] 4. Checkpoint - Core Services 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. 의존성 주입 및 통합
  - [ ] 5.1 FastAPI 의존성 업데이트
    - `app/core/deps.py` 수정
    - get_stt_service, get_translation_service 의존성 함수 추가
    - 기존 get_transcribe_service, get_bedrock_service 대체
    - _Requirements: 7.5_
  - [ ] 5.2 WebSocket 핸들러 업데이트
    - `app/ws/` 핸들러에서 새로운 Protocol 기반 서비스 사용
    - TranscriptResult 기반 이벤트 처리로 변경
    - session.start sampleRate 값을 STT 서비스에 전달 (OpenAI 입력 샘플레이트 갱신)
    - _Requirements: 2.4, 2.5, 2.6_
  - [ ] 5.3 REST API 업데이트
    - `app/api/` 라우터에서 새로운 Translation 서비스 사용
    - _Requirements: 3.1, 3.2_
  - [ ]* 5.4 Property test: Service Factory Correctness
    - **Property 2: Service Factory Correctness**
    - **Validates: Requirements 7.1, 7.2**
  - [ ]* 5.5 Property test: Protocol Conformance
    - **Property 3: Protocol Conformance**
    - **Validates: Requirements 2.7, 3.3**

- [ ] 6. 기존 파일 정리
  - [ ] 6.1 레거시 서비스 파일 제거
    - `app/services/transcribe.py` 삭제 (stt/aws.py로 이동 완료)
    - `app/services/bedrock.py` 삭제 (translation/aws.py로 이동 완료)
    - suggestion.py의 BedrockService 임포트 경로 수정
    - _Requirements: 7.3_

- [ ] 7. 환경 변수 및 문서 업데이트
  - [ ] 7.1 환경 변수 파일 업데이트
    - `.env.example` 파일에 새로운 환경 변수 추가
    - PROVIDER_MODE, OPENAI_API_KEY, OPENAI_STT_MODEL 등
    - _Requirements: 8.1, 8.2, 8.3_
  - [ ] 7.2 WebSocket 프로토콜 문서 업데이트
    - OpenAI 모드 24kHz PCM 전송 및 session.start sampleRate 설명 추가
    - _Requirements: 9.1, 9.2_
  - [ ] 7.3 프론트 오디오 파이프라인 업데이트
    - OpenAI 모드에서 24kHz PCM 생성 (AudioWorklet/리샘플링)
    - PROVIDER_MODE에 따른 전송 샘플레이트 분기
    - _Requirements: 9.1, 9.2, 9.4_

- [ ] 8. 테스트 업데이트 및 회귀 검증
  - [ ] 8.1 테스트 리팩토링
    - TranscribeService/BedrockService 제거에 따른 기존 테스트 업데이트
    - DI 변경으로 인한 WebSocket/REST 테스트 수정
  - [ ] 8.2 통합 테스트 보강
    - OpenAI STT 이벤트(부분/완료) 경로 테스트
    - Bedrock 기반 SuggestionService 유지 검증

- [ ] 9. Final Checkpoint - 전체 통합 검증
  - Ensure all tests pass, ask the user if questions arise.
  - OpenAI 모드로 전환하여 실제 STT/번역 동작 확인

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- 기존 AWS 기능은 유지되며, PROVIDER_MODE=AWS가 기본값
- Google 프로바이더는 NotImplementedError로 처리 (향후 구현)
- SuggestionService는 항상 Bedrock 사용 (프로바이더 독립)
- 프론트엔드는 OpenAI 모드에서 24kHz PCM 전송, 백엔드는 필요 시에만 리샘플링
