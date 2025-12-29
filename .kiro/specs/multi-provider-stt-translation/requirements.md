# Requirements Document

## Introduction

이 문서는 실시간 영어 회의 지원 시스템의 STT(Speech-to-Text) 및 번역 서비스를 멀티 프로바이더 아키텍처로 확장하기 위한 요구사항을 정의합니다. 현재 AWS(Transcribe, Bedrock) 기반 구현을 유지하면서, OpenAI와 Google 플랫폼을 추가하여 사용자가 환경 변수를 통해 프로바이더를 선택할 수 있도록 합니다. OpenAI STT는 Realtime transcription 세션을 사용하며 24kHz PCM 오디오 포맷 제약을 고려해야 합니다. 기존 16kHz 오디오 파이프라인은 프로바이더별 요구사항에 맞춰 리샘플링해야 하며, 질문 제안은 계속 Bedrock 기반으로 유지합니다. diarization을 지원하지 않는 프로바이더는 `speaker`를 `spk_1`로 고정합니다.

## Glossary

- **Provider_Mode**: 시스템이 사용할 클라우드 서비스 프로바이더를 지정하는 설정값 (AWS, OPENAI, GOOGLE)
- **STT_Service**: 음성을 텍스트로 변환하는 Speech-to-Text 서비스
- **Translation_Service**: 텍스트를 다른 언어로 번역하는 서비스
- **Service_Factory**: Provider_Mode에 따라 적절한 서비스 구현체를 생성하는 팩토리 컴포넌트
- **STT_Protocol**: STT 서비스가 구현해야 하는 공통 인터페이스
- **Translation_Protocol**: 번역 서비스가 구현해야 하는 공통 인터페이스
- **AWS_STT**: AWS Transcribe Streaming을 사용한 STT 구현체
- **OpenAI_STT**: OpenAI Realtime transcription 세션을 사용한 STT 구현체
- **Google_STT**: Google Cloud Speech-to-Text를 사용한 STT 구현체
- **AWS_Translation**: Amazon Bedrock을 사용한 번역 구현체
- **OpenAI_Translation**: OpenAI GPT 모델을 사용한 번역 구현체
- **Language_Code_Mapping**: 프로바이더별 언어 코드 규격 차이를 매핑하는 규칙 (예: AWS `en-US` → OpenAI `en`)
- **Google_Translation**: Google Cloud Translation API를 사용한 번역 구현체

## Requirements

### Requirement 1: Provider Mode 설정

**User Story:** As a 시스템 관리자, I want to 환경 변수로 프로바이더를 선택, so that 배포 환경에 따라 적절한 클라우드 서비스를 사용할 수 있습니다.

#### Acceptance Criteria

1. THE Settings SHALL support a `provider_mode` field with values "AWS", "OPENAI", or "GOOGLE"
2. WHEN `PROVIDER_MODE` environment variable is not set, THE Settings SHALL default to "AWS"
3. WHEN an invalid `PROVIDER_MODE` value is provided, THE Settings SHALL raise a validation error with a descriptive message
4. THE Settings SHALL load provider-specific configuration fields based on the selected Provider_Mode

### Requirement 2: STT Service Protocol

**User Story:** As a 개발자, I want to 공통 STT 인터페이스를 정의, so that 프로바이더 변경 시 기존 코드 수정을 최소화할 수 있습니다.

#### Acceptance Criteria

1. THE STT_Protocol SHALL define `start_stream(session_id: str)` method for initiating audio streaming
2. THE STT_Protocol SHALL define `send_audio(audio_chunk: bytes)` method for sending audio data
3. THE STT_Protocol SHALL define `stop_stream()` method for terminating the stream
4. THE STT_Protocol SHALL define `get_results()` method returning an async iterator of normalized transcript results
5. THE normalized transcript results SHALL include `is_partial`, `text`, and `speaker` fields
6. WHEN speaker diarization is unavailable, THE `speaker` SHALL be fixed to `"spk_1"`
7. WHEN any STT implementation is used, THE implementation SHALL conform to STT_Protocol interface

### Requirement 3: Translation Service Protocol

**User Story:** As a 개발자, I want to 공통 번역 인터페이스를 정의, so that 프로바이더 변경 시 기존 코드 수정을 최소화할 수 있습니다.

#### Acceptance Criteria

1. THE Translation_Protocol SHALL define `translate_en_to_ko(text: str) -> str` method for English to Korean translation
2. THE Translation_Protocol SHALL define `translate_ko_to_en(text: str) -> str` method for Korean to English translation
3. WHEN any Translation implementation is used, THE implementation SHALL conform to Translation_Protocol interface

### Requirement 4: AWS Provider 구현

**User Story:** As a 사용자, I want to AWS 서비스를 사용한 STT와 번역, so that 기존 AWS 인프라를 활용할 수 있습니다.

#### Acceptance Criteria

1. WHEN Provider_Mode is "AWS", THE Service_Factory SHALL create AWS_STT using Amazon Transcribe Streaming
2. WHEN Provider_Mode is "AWS", THE Service_Factory SHALL create AWS_Translation using Amazon Bedrock
3. THE AWS_STT SHALL support real-time streaming transcription with optional speaker labels
4. THE AWS_Translation SHALL use configurable model IDs for translation tasks
5. WHEN AWS credentials are not configured, THE AWS_STT SHALL raise a descriptive error

### Requirement 5: OpenAI Provider 구현

**User Story:** As a 사용자, I want to OpenAI 서비스를 사용한 STT와 번역, so that OpenAI의 고품질 모델을 활용할 수 있습니다.

#### Acceptance Criteria

1. WHEN Provider_Mode is "OPENAI", THE Service_Factory SHALL create OpenAI_STT using OpenAI Realtime transcription session (WebSocket)
2. WHEN Provider_Mode is "OPENAI", THE Service_Factory SHALL create OpenAI_Translation using GPT models
3. THE OpenAI_STT SHALL use a configurable realtime transcription model (default: `gpt-4o-transcribe`)
4. THE OpenAI_STT SHALL send input audio as `audio/pcm` at 24kHz mono to the Realtime API
5. THE OpenAI_STT SHALL resample 16kHz PCM input to 24kHz when necessary, preferring the most optimized location (frontend if possible, backend as fallback)
6. THE OpenAI_STT SHALL support real-time streaming transcription without speaker diarization and SHALL emit `speaker` as `"spk_1"`
7. THE OpenAI_STT SHALL return partial/final transcripts suitable for 1-2 sentence grouping in the UI
8. THE OpenAI_Translation SHALL use configurable model IDs for translation tasks and MUST return only the translation text
9. WHEN `OPENAI_API_KEY` is not set, THE OpenAI_STT SHALL raise a descriptive error

### Requirement 6: Google Provider 인터페이스 (향후 구현 예정)

**User Story:** As a 개발자, I want to Google Provider를 위한 인터페이스를 설계, so that 향후 Google Cloud 서비스를 쉽게 추가할 수 있습니다.

#### Acceptance Criteria

1. THE STT_Protocol SHALL be designed to accommodate Google Cloud Speech-to-Text streaming API
2. THE Translation_Protocol SHALL be designed to accommodate Google Cloud Translation API
3. WHEN Provider_Mode is "GOOGLE", THE Service_Factory SHALL raise NotImplementedError with a message indicating future support

### Requirement 7: Service Factory

**User Story:** As a 개발자, I want to 팩토리 패턴으로 서비스 인스턴스를 생성, so that 프로바이더 선택 로직을 중앙화할 수 있습니다.

#### Acceptance Criteria

1. THE Service_Factory SHALL create appropriate STT_Service based on Provider_Mode setting
2. THE Service_Factory SHALL create appropriate Translation_Service based on Provider_Mode setting
3. THE SuggestionService SHALL continue to use Bedrock regardless of Provider_Mode
4. WHEN an unsupported Provider_Mode is requested, THE Service_Factory SHALL raise a ValueError with supported options
5. THE Service_Factory SHALL be injectable via FastAPI dependency injection

### Requirement 8: 환경 변수 구성

**User Story:** As a 시스템 관리자, I want to 프로바이더별 환경 변수를 설정, so that 각 프로바이더의 인증 및 설정을 관리할 수 있습니다.

#### Acceptance Criteria

1. THE Settings SHALL support AWS-specific fields: `aws_region`, `bedrock_translation_model_id`, `bedrock_quick_translate_model_id`
2. THE Settings SHALL support OpenAI-specific fields: `openai_api_key`, `openai_stt_model`, `openai_translation_model`, `openai_stt_language`
3. THE Settings SHALL reserve Google-specific fields for future implementation: `google_project_id`, `google_credentials_path`
4. WHEN Provider_Mode is "AWS" or "OPENAI", THE Settings SHALL validate that required fields for that provider are configured
5. THE Settings SHALL apply Language_Code_Mapping when Provider_Mode is "OPENAI" (ISO-639-1, e.g. `en`)

### Requirement 9: 오디오 포맷/언어 정합성

**User Story:** As a 개발자, I want to 프로바이더별 오디오/언어 규격을 정합화, so that 실시간 전사 품질과 성능 목표를 유지할 수 있습니다.

#### Acceptance Criteria

1. WHEN Provider_Mode is "AWS", THE system SHALL keep 16kHz mono PCM s16le audio input
2. WHEN Provider_Mode is "OPENAI", THE system SHALL ensure audio is `audio/pcm` at 24kHz mono before sending to Realtime API
3. WHEN Provider_Mode is "OPENAI", THE language code SHALL be ISO-639-1 and derived from settings (`openai_stt_language` or mapped from `transcribe_language_code`)
4. THE resampling path SHALL avoid unnecessary latency and SHALL meet the performance targets in `.kiro/steering/performance-requirements.md`
