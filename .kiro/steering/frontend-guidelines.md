---
inclusion: fileMatch
fileMatchPattern: "apps/web/**/*.{ts,tsx}"
---

# Frontend 개발 가이드라인 (React + Vite)

## 디렉토리 구조
```
apps/web/src/
  app/              # 페이지/레이아웃
  components/       # 공통 UI 컴포넌트
  features/
    meeting/        # 전사/번역 패널
    translate/      # 빠른 번역
    suggestions/    # AI 질문 제안 (P1)
  hooks/            # 커스텀 훅
  lib/
    ws.ts           # WebSocket 클라이언트
    api.ts          # REST 클라이언트
    audio.ts        # 마이크 캡처/리샘플/인코딩
  styles/           # TailwindCSS
  types/            # contracts 생성 타입
```

## 코딩 규칙
- TypeScript strict 모드
- 함수형 컴포넌트 + React Hooks
- TailwindCSS로 스타일링
- contracts에서 생성된 타입 사용

## UI 레이아웃
```
┌──────────────────────────────────────────────┐
│  Header: 로고/노트, 전사 상태, 설정, Start/Stop  │
├────────────────────┬─────────────────────────┤
│  Left Panel        │  Right Panel            │
│  Transcript Live   │  Suggestions Prompt     │
│  Transcript History│  AI Suggestions         │
├────────────────────┴─────────────────────────┤
│  Bottom Panel: 한→영 입력 (Quick Translate)     │
└──────────────────────────────────────────────┘
```

## 상단 컨트롤 (Transcribe)
- 시작/중단 버튼을 최상단 우측에 배치하고 상태에 따라 라벨/색상 변경 (Start transcribing ↔ Stop)
- 전사 중에는 상태 텍스트와 간단한 레벨 시각화(예: 웨이브/도트) 표시
- 설정 버튼은 상단 우측에 배치하고 마이크 선택/테스트를 제공

## 빠른 번역 UI
- Enter 키 또는 버튼으로 번역 실행
- 번역 결과 복사 버튼 제공
- 세션 내 번역 히스토리 유지

## 화자 색상
- Speaker 1: 파랑 (#3B82F6)
- Speaker 2: 초록 (#10B981)
- Speaker 3: 보라 (#8B5CF6)
- 이후: 순환

## WebSocket 처리
- 자동 재연결 구현
- 바이너리 프레임으로 오디오 전송 (20~100ms 청크)
- JSON 이벤트 파싱 및 상태 업데이트

## 오디오 캡처
- Web Audio API 사용
- 16kHz mono PCM s16le로 리샘플링
- AudioWorklet 권장

## 테스트
- vitest + React Testing Library
- Playwright (E2E)

## 접근성
- WCAG 2.1 AA 준수
- 키보드 네비게이션 지원
- 스크린 리더 호환
