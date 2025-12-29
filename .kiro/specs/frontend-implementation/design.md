# Design Document: Frontend Implementation

## Overview

English Meeting Helper 프론트엔드 설계 문서입니다. React + TypeScript + TailwindCSS 기반으로 실시간 회의 지원 UI를 구현합니다. 백엔드 WebSocket 및 REST API와 연동하여 음성 전사, 번역, AI 질문 제안 기능을 제공합니다.

### 핵심 설계 원칙
- **컴포넌트 기반**: 기능별로 분리된 React 컴포넌트 구조
- **커스텀 훅**: 상태 관리 및 비즈니스 로직을 훅으로 분리
- **타입 안전성**: TypeScript로 모든 이벤트 및 상태 타입 정의
- **반응형 디자인**: TailwindCSS 유틸리티 클래스 활용

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Application                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                      App Component                      │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐    │    │
│  │  │MeetingPanel │ │QuickTranslate│ │SuggestionsPanel│    │    │
│  │  └──────┬──────┘ └──────┬──────┘ └────────┬────────┘    │    │
│  └─────────┼───────────────┼─────────────────┼─────────────┘    │
│            │               │                 │                  │
│  ┌─────────┴───────────────┴─────────────────┴─────────────┐    │
│  │                    Custom Hooks Layer                    │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │   │
│  │  │useMeeting    │ │useTranslate  │ │useAudioCapture   │  │   │
│  │  └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘  │   │
│  └─────────┼────────────────┼──────────────────┼────────────┘   │
│            │                │                  │                │
│  ┌─────────┴────────────────┴──────────────────┴────────────┐   │
│  │                      Lib Layer                           │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │   │
│  │  │  ws.ts       │ │  api.ts      │ │  audio.ts        │  │   │
│  │  │ (WebSocket)  │ │ (REST API)   │ │ (Audio Capture)  │  │   │
│  │  └──────────────┘ └──────────────┘ └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   WebSocket   │   │    REST API     │   │   Browser API   │
│/ws/v1/meetings│   │/api/v1/translate│   │ getUserMedia()  │
└───────────────┘   └─────────────────┘   └─────────────────┘
```


### 디렉토리 구조

```
apps/web/src/
├── main.tsx                    # React 앱 진입점
├── App.tsx                     # 루트 컴포넌트
├── index.css                   # 글로벌 스타일
├── components/
│   ├── TopBar.tsx              # 상단 헤더 (전사 상태/버튼/설정)
│   ├── MeetingPanel.tsx        # 회의 패널 (전사/번역 표시)
│   ├── QuickTranslate.tsx      # 빠른 번역 입력/출력
│   ├── SuggestionsPanel.tsx    # AI 제안 표시
│   ├── TranscriptItem.tsx      # 개별 전사 항목
│   ├── TranslationItem.tsx     # 개별 번역 항목
│   ├── ErrorBanner.tsx         # 에러 배너
│   ├── TranscribeControls.tsx  # 전사 시작/중단 버튼
│   └── MicSettingsPanel.tsx    # 마이크 설정 패널
├── hooks/
│   ├── useMeeting.ts           # 회의 세션 상태 관리
│   ├── useTranslate.ts         # 빠른 번역 상태 관리
│   └── useAudioCapture.ts      # 오디오 캡처 관리
├── lib/
│   ├── ws.ts                   # WebSocket 클라이언트
│   ├── api.ts                  # REST API 클라이언트
│   └── audio.ts                # 오디오 캡처 유틸리티
└── types/
    └── events.ts               # WebSocket 이벤트 타입 정의
```

## Components and Interfaces

### 1. 타입 정의 (types/events.ts)

백엔드 WebSocket 이벤트와 일치하는 TypeScript 타입 정의입니다.

```typescript
// 기본 이벤트 타입
export interface BaseEvent {
  type: string;
  ts: number;
}

// 전사 이벤트
export interface TranscriptPartialEvent extends BaseEvent {
  type: "transcript.partial";
  sessionId: string;
  speaker: string;
  text: string;
}

export interface TranscriptFinalEvent extends BaseEvent {
  type: "transcript.final";
  sessionId: string;
  speaker: string;
  text: string;
}

// 번역 이벤트
export interface TranslationFinalEvent extends BaseEvent {
  type: "translation.final";
  sessionId: string;
  sourceTs: number;
  speaker: string;
  sourceText: string;
  translatedText: string;
}

// 제안 이벤트
export interface SuggestionItem {
  en: string;
  ko: string;
}

export interface SuggestionsUpdateEvent extends BaseEvent {
  type: "suggestions.update";
  sessionId: string;
  items: SuggestionItem[];
}

// 에러 이벤트
export interface ErrorEvent extends BaseEvent {
  type: "error";
  code: string;
  message: string;
  retryable?: boolean;
}

export interface ServerPongEvent extends BaseEvent {
  type: "server.pong";
}

// 유니온 타입
export type WebSocketEvent =
  | TranscriptPartialEvent
  | TranscriptFinalEvent
  | TranslationFinalEvent
  | SuggestionsUpdateEvent
  | ErrorEvent
  | ServerPongEvent;

// 클라이언트 컨트롤 메시지
export interface SessionStartMessage {
  type: "session.start";
  sampleRate: 16000;
  format: "pcm_s16le";
  lang: "en-US";
}

export interface SessionStopMessage {
  type: "session.stop";
}

export interface ClientPingMessage {
  type: "client.ping";
  ts: number;
}

export interface SuggestionsPromptMessage {
  type: "suggestions.prompt";
  prompt: string;
}

export type ClientControlMessage =
  | SessionStartMessage
  | SessionStopMessage
  | ClientPingMessage
  | SuggestionsPromptMessage;
```


### 2. WebSocket 클라이언트 (lib/ws.ts)

기존 WsClient를 확장하여 타입 안전한 이벤트 처리를 지원합니다.

```typescript
import {
  WebSocketEvent,
  ClientControlMessage,
  SessionStartMessage,
} from "../types/events";

export type EventHandler = (event: WebSocketEvent) => void;

export class MeetingWsClient {
  private socket: WebSocket | null = null;
  private pingIntervalId: number | null = null;
  private pongTimeoutId: number | null = null;

  constructor(
    private readonly baseUrl: string,
    private readonly onEvent?: EventHandler,
    private readonly onConnectionChange?: (connected: boolean) => void,
    private readonly onConnectionIssue?: (reason: string) => void
  ) {}

  connect(sessionId: string, startMessage: SessionStartMessage): void {
    this.open(this.buildUrl(sessionId), startMessage);
  }

  reconnect(sessionId: string, startMessage: SessionStartMessage): void {
    this.disconnect();
    this.connect(sessionId, startMessage);
  }

  sendAudio(audioData: ArrayBuffer): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(audioData);
    }
  }

  sendControl(message: ClientControlMessage): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }

  disconnect(): void {
    this.stopKeepAlive();
    this.socket?.close();
    this.socket = null;
  }

  private open(url: string, startMessage: SessionStartMessage): void {
    const socket = new WebSocket(url);
    this.socket = socket;

    socket.onopen = () => {
      this.onConnectionChange?.(true);
      this.sendControl(startMessage);
      this.startKeepAlive();
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketEvent;
        if (data.type === "server.pong") {
          this.handlePong();
          return;
        }
        this.onEvent?.(data);
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    socket.onclose = () => {
      this.stopKeepAlive();
      this.socket = null;
      this.onConnectionChange?.(false);
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }

  private startKeepAlive(): void {
    this.stopKeepAlive();
    this.pingIntervalId = window.setInterval(() => {
      this.sendControl({ type: "client.ping", ts: Date.now() });
      this.startPongTimeout();
    }, 15000);
  }

  private startPongTimeout(): void {
    if (this.pongTimeoutId) {
      window.clearTimeout(this.pongTimeoutId);
    }
    this.pongTimeoutId = window.setTimeout(() => {
      this.onConnectionIssue?.("PONG_TIMEOUT");
      this.disconnect();
    }, 30000);
  }

  private handlePong(): void {
    if (this.pongTimeoutId) {
      window.clearTimeout(this.pongTimeoutId);
      this.pongTimeoutId = null;
    }
  }

  private stopKeepAlive(): void {
    if (this.pingIntervalId) {
      window.clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
    }
    if (this.pongTimeoutId) {
      window.clearTimeout(this.pongTimeoutId);
      this.pongTimeoutId = null;
    }
  }

  private buildUrl(sessionId: string): string {
    const trimmed = this.baseUrl.replace(/\/$/, "");
    if (trimmed.startsWith("ws://") || trimmed.startsWith("wss://")) {
      return `${trimmed}/ws/v1/meetings/${sessionId}`;
    }
    const wsBase = trimmed.startsWith("https://")
      ? trimmed.replace("https://", "wss://")
      : trimmed.replace("http://", "ws://");
    return `${wsBase}/ws/v1/meetings/${sessionId}`;
  }
}
```

### 3. 오디오 캡처 (lib/audio.ts)

마이크 오디오를 캡처하고 PCM 형식으로 변환합니다.

```typescript
export interface AudioCaptureOptions {
  sampleRate: number;  // 16000
  chunkIntervalMs: number;  // 100ms
}

export class AudioCapture {
  private stream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private onAudioChunk: ((chunk: ArrayBuffer) => void) | null = null;

  async start(
    options: AudioCaptureOptions,
    onChunk: (chunk: ArrayBuffer) => void
  ): Promise<void> {
    this.onAudioChunk = onChunk;
    
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: options.sampleRate,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    this.audioContext = new AudioContext({ sampleRate: options.sampleRate });
    const source = this.audioContext.createMediaStreamSource(this.stream);
    
    // ScriptProcessorNode for audio processing (deprecated but widely supported)
    const bufferSize = Math.floor(options.sampleRate * options.chunkIntervalMs / 1000);
    this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
    
    this.processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      const pcmData = this.float32ToPcm16(inputData);
      this.onAudioChunk?.(pcmData.buffer);
    };

    source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
  }

  stop(): void {
    this.processor?.disconnect();
    this.audioContext?.close();
    this.stream?.getTracks().forEach((track) => track.stop());
    this.processor = null;
    this.audioContext = null;
    this.stream = null;
    this.onAudioChunk = null;
  }

  private float32ToPcm16(float32Array: Float32Array): Int16Array {
    const pcm16 = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return pcm16;
  }
}
```


### 4. REST API 클라이언트 (lib/api.ts)

빠른 번역을 위한 REST API 클라이언트입니다.

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface TranslateRequest {
  text: string;
}

export interface TranslateResponse {
  translatedText: string;
}

export async function translateKoToEn(text: string): Promise<TranslateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/translate/ko-en`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text } as TranslateRequest),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `Translation failed: ${response.status}`);
  }

  return response.json();
}

export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}
```

### 5. useMeeting 훅 (hooks/useMeeting.ts)

회의 세션 상태를 관리하는 커스텀 훅입니다.

```typescript
import { useState, useCallback, useRef, useEffect } from "react";
import { MeetingWsClient } from "../lib/ws";
import { AudioCapture } from "../lib/audio";
import {
  WebSocketEvent,
  TranscriptPartialEvent,
  TranscriptFinalEvent,
  TranslationFinalEvent,
  SuggestionItem,
  ErrorEvent,
} from "../types/events";

export interface TranscriptEntry {
  id: string;
  kind: "transcript";
  speaker: string;
  text: string;
  isFinal: boolean;
  ts: number;
  translations: string[];
}

export interface OrphanTranslationEntry {
  id: string;
  kind: "translation";
  ts: number;
  speaker: string;
  sourceTs: number;
  translatedText: string;
}

export interface MeetingState {
  isConnected: boolean;
  isRecording: boolean;
  sessionId: string | null;
  transcripts: TranscriptEntry[];
  orphanTranslations: OrphanTranslationEntry[];
  suggestions: SuggestionItem[];
  error: ErrorEvent | null;
}

export function useMeeting(wsBaseUrl: string) {
  const [state, setState] = useState<MeetingState>({
    isConnected: false,
    isRecording: false,
    sessionId: null,
    transcripts: [],
    orphanTranslations: [],
    suggestions: [],
    error: null,
  });

  const wsClientRef = useRef<MeetingWsClient | null>(null);
  const audioCaptureRef = useRef<AudioCapture | null>(null);

  const handleEvent = useCallback((event: WebSocketEvent) => {
    switch (event.type) {
      case "transcript.partial":
        handlePartialTranscript(event);
        break;
      case "transcript.final":
        handleFinalTranscript(event);
        break;
      case "translation.final":
        handleTranslation(event);
        break;
      case "suggestions.update":
        setState((s) => ({ ...s, suggestions: event.items }));
        break;
      case "server.pong":
        break;
      case "error":
        setState((s) => ({ ...s, error: event }));
        break;
    }
  }, []);

  const handlePartialTranscript = (event: TranscriptPartialEvent) => {
    setState((s) => {
      const existing = s.transcripts.find(
        (t) => !t.isFinal && t.speaker === event.speaker
      );
      if (existing) {
        return {
          ...s,
          transcripts: s.transcripts.map((t) =>
            t.id === existing.id ? { ...t, text: event.text, ts: event.ts } : t
          ),
        };
      }
      return {
        ...s,
        transcripts: [
          ...s.transcripts,
          {
            id: `partial-${event.ts}`,
            kind: "transcript",
            speaker: event.speaker,
            text: event.text,
            isFinal: false,
            ts: event.ts,
            translations: [],
          },
        ],
      };
    });
  };

  const handleFinalTranscript = (event: TranscriptFinalEvent) => {
    setState((s) => {
      // Remove partial and add final
      const filtered = s.transcripts.filter(
        (t) => t.isFinal || t.speaker !== event.speaker
      );
      return {
        ...s,
        transcripts: [
          ...filtered,
          {
            id: `final-${event.ts}`,
            kind: "transcript",
            speaker: event.speaker,
            text: event.text,
            isFinal: true,
            ts: event.ts,
            translations: [],
          },
        ],
      };
    });
  };

  const handleTranslation = (event: TranslationFinalEvent) => {
    setState((s) => {
      const targetIndex = s.transcripts.findIndex((t) => t.ts === event.sourceTs);
      if (targetIndex === -1) {
        return {
          ...s,
          orphanTranslations: [
            ...s.orphanTranslations,
            {
              id: `orphan-${event.ts}`,
              kind: "translation",
              ts: event.ts,
              speaker: event.speaker,
              sourceTs: event.sourceTs,
              translatedText: event.translatedText,
            },
          ],
        };
      }
      const transcripts = [...s.transcripts];
      const target = transcripts[targetIndex];
      transcripts[targetIndex] = {
        ...target,
        translations: [...target.translations, event.translatedText],
      };
      return { ...s, transcripts };
    });
  };

  const startMeeting = useCallback(async () => {
    const sessionId = crypto.randomUUID().toLowerCase();

    wsClientRef.current = new MeetingWsClient(
      wsBaseUrl,
      handleEvent,
      (connected) => setState((s) => ({ ...s, isConnected: connected })),
      () => {
        audioCaptureRef.current?.stop();
        setState((s) => ({
          ...s,
          error: {
            type: "error",
            ts: Date.now(),
            code: "CONNECTION_LOST",
            message: "Connection lost",
            retryable: true,
          },
          isRecording: false,
        }));
      }
    );

    wsClientRef.current.connect(sessionId, {
      type: "session.start",
      sampleRate: 16000,
      format: "pcm_s16le",
      lang: "en-US",
    });

    audioCaptureRef.current = new AudioCapture();
    await audioCaptureRef.current.start(
      { sampleRate: 16000, chunkIntervalMs: 100 },
      (chunk) => wsClientRef.current?.sendAudio(chunk)
    );

    setState((s) => ({
      ...s,
      sessionId,
      isRecording: true,
      transcripts: [],
      orphanTranslations: [],
      suggestions: [],
      error: null,
    }));
  }, [wsBaseUrl, handleEvent]);

  const stopMeeting = useCallback(() => {
    wsClientRef.current?.sendControl({ type: "session.stop" });
    audioCaptureRef.current?.stop();
    wsClientRef.current?.disconnect();
    setState((s) => ({ ...s, isRecording: false, sessionId: null }));
  }, []);

  const reconnect = useCallback(async () => {
    const sessionId = crypto.randomUUID().toLowerCase();
    wsClientRef.current?.reconnect(sessionId, {
      type: "session.start",
      sampleRate: 16000,
      format: "pcm_s16le",
      lang: "en-US",
    });
    audioCaptureRef.current?.stop();
    audioCaptureRef.current = new AudioCapture();
    await audioCaptureRef.current.start(
      { sampleRate: 16000, chunkIntervalMs: 100 },
      (chunk) => wsClientRef.current?.sendAudio(chunk)
    );
    setState((s) => ({
      ...s,
      sessionId,
      isRecording: true,
      error: null,
    }));
  }, []);

  const dismissError = useCallback(() => {
    setState((s) => ({ ...s, error: null }));
  }, []);

  useEffect(() => {
    return () => {
      audioCaptureRef.current?.stop();
      wsClientRef.current?.disconnect();
    };
  }, []);

  return {
    ...state,
    startMeeting,
    stopMeeting,
    reconnect,
    dismissError,
  };
}
```


### 6. useTranslate 훅 (hooks/useTranslate.ts)

빠른 번역 상태를 관리하는 커스텀 훅입니다.

```typescript
import { useState, useCallback } from "react";
import { translateKoToEn } from "../lib/api";

export interface TranslateState {
  inputText: string;
  outputText: string;
  isLoading: boolean;
  error: string | null;
}

export function useTranslate() {
  const [state, setState] = useState<TranslateState>({
    inputText: "",
    outputText: "",
    isLoading: false,
    error: null,
  });

  const setInputText = useCallback((text: string) => {
    setState((s) => ({ ...s, inputText: text, error: null }));
  }, []);

  const translate = useCallback(async () => {
    if (!state.inputText.trim()) return;

    setState((s) => ({ ...s, isLoading: true, error: null }));

    try {
      const response = await translateKoToEn(state.inputText);
      setState((s) => ({
        ...s,
        outputText: response.translatedText,
        isLoading: false,
      }));
    } catch (e) {
      setState((s) => ({
        ...s,
        error: e instanceof Error ? e.message : "Translation failed",
        isLoading: false,
      }));
    }
  }, [state.inputText]);

  const copyToClipboard = useCallback(async () => {
    if (state.outputText) {
      await navigator.clipboard.writeText(state.outputText);
      return true;
    }
    return false;
  }, [state.outputText]);

  const clear = useCallback(() => {
    setState({ inputText: "", outputText: "", isLoading: false, error: null });
  }, []);

  return {
    ...state,
    setInputText,
    translate,
    copyToClipboard,
    clear,
  };
}
```

### 7. TopBar 컴포넌트 (components/TopBar.tsx)

상단 전사 컨트롤을 제공하는 헤더 컴포넌트입니다.

```typescript
import { TranscribeControls } from "./TranscribeControls";
import { MicSettingsPanel } from "./MicSettingsPanel";

interface TopBarProps {
  isRecording: boolean;
  isConnected: boolean;
  onStart: () => void;
  onStop: () => void;
}

export function TopBar({ isRecording, isConnected, onStart, onStop }: TopBarProps) {
  return (
    <header className="flex items-center justify-between rounded-full border bg-white px-4 py-2">
      <div className="flex items-center gap-3">
        <span className="text-base font-semibold">Notes</span>
        {isRecording && (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <span>Transcript</span>
            <div className="h-3 w-24 rounded-full bg-slate-200" aria-hidden />
          </div>
        )}
      </div>
      <div className="flex items-center gap-3">
        <MicSettingsPanel />
        <TranscribeControls
          isRecording={isRecording}
          isConnected={isConnected}
          onStart={onStart}
          onStop={onStop}
        />
      </div>
    </header>
  );
}
```

### 8. MeetingPanel 컴포넌트 (components/MeetingPanel.tsx)

회의 전사 및 번역을 표시하는 메인 패널입니다.

```typescript
import { useRef, useEffect } from "react";
import { OrphanTranslationEntry, TranscriptEntry } from "../hooks/useMeeting";
import { TranscriptItem } from "./TranscriptItem";
import { TranslationItem } from "./TranslationItem";
import { ErrorBanner } from "./ErrorBanner";
import { ErrorEvent } from "../types/events";

interface MeetingPanelProps {
  isRecording: boolean;
  liveTranscripts: TranscriptEntry[];
  transcripts: TranscriptEntry[];
  orphanTranslations: OrphanTranslationEntry[];
  error: ErrorEvent | null;
  onReconnect: () => void;
  onDismissError: () => void;
}

export function MeetingPanel({
  isRecording,
  liveTranscripts,
  transcripts,
  orphanTranslations,
  error,
  onReconnect,
  onDismissError,
}: MeetingPanelProps) {
  const liveScrollRef = useRef<HTMLDivElement>(null);
  const historyScrollRef = useRef<HTMLDivElement>(null);
  const liveTimeline = [...liveTranscripts].sort((left, right) => right.ts - left.ts);
  const historyTimeline = [...transcripts, ...orphanTranslations].sort((left, right) => {
    if (left.ts !== right.ts) {
      return right.ts - left.ts;
    }
    if (left.kind === right.kind) {
      return 0;
    }
    return left.kind === "transcript" ? -1 : 1;
  });

  // Auto-scroll to latest transcript (top in reversed order)
  useEffect(() => {
    liveScrollRef.current?.scrollTo({ top: 0 });
  }, [liveTimeline.length]);

  useEffect(() => {
    historyScrollRef.current?.scrollTo({ top: 0 });
  }, [historyTimeline.length]);

  return (
    <section className="flex h-full min-h-0 flex-col rounded-lg border bg-white" aria-label="Meeting Panel">
      <header className="flex items-center justify-between border-b px-4 py-3">
        <h2 className="text-lg font-semibold">Transcript</h2>
      </header>

      {error && (
        <ErrorBanner
          error={error}
          onDismiss={onDismissError}
          onRetry={error.retryable ? onReconnect : undefined}
        />
      )}

      <div className="flex min-h-0 flex-1 flex-col gap-3 p-4">
        <div className="flex min-h-0 flex-[2] flex-col rounded-lg border border-slate-100 bg-slate-50/70">
          <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <span>Live</span>
          </div>
          <div
            ref={liveScrollRef}
            className="flex-1 space-y-3 overflow-y-auto p-3"
            role="log"
            aria-live="polite"
            aria-label="Live transcripts"
          >
            {liveTimeline.length === 0 ? (
              <p className="text-sm text-slate-500">
                {isRecording
                  ? "Listening for speech..."
                  : "Click Start to begin recording"}
              </p>
            ) : (
              liveTimeline.map((entry) => (
                <TranscriptItem key={entry.id} transcript={entry} />
              ))
            )}
          </div>
        </div>
        <div className="flex min-h-0 flex-[3] flex-col rounded-lg border border-slate-100 bg-white">
          <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <span>History</span>
          </div>
          <div
            ref={historyScrollRef}
            className="flex-1 space-y-3 overflow-y-auto p-3"
            role="log"
            aria-live="polite"
            aria-label="Final transcripts"
          >
            {historyTimeline.length === 0 ? (
              <p className="text-sm text-slate-500">
                {isRecording
                  ? "Confirmed transcripts will appear here."
                  : "Start recording to capture transcripts."}
              </p>
            ) : (
              historyTimeline.map((entry) =>
                entry.kind === "transcript" ? (
                  <TranscriptItem key={entry.id} transcript={entry} />
                ) : (
                  <TranslationItem key={entry.id} translation={entry} />
                )
              )
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
```


### 9. TranscriptItem 컴포넌트 (components/TranscriptItem.tsx)

개별 전사 항목을 표시합니다.

```typescript
import { TranscriptEntry } from "../hooks/useMeeting";

interface TranscriptItemProps {
  transcript: TranscriptEntry;
}

export function TranscriptItem({ transcript }: TranscriptItemProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-start gap-2">
        <span className="text-xs font-medium text-slate-500">
          {transcript.speaker}
        </span>
        <p
          className={`text-sm ${
            transcript.isFinal ? "text-slate-900" : "text-slate-400 italic"
          }`}
        >
          {transcript.text}
        </p>
      </div>
      {transcript.translations.map((translation, index) => (
        <p key={`${transcript.id}-tr-${index}`} className="ml-6 text-sm text-blue-600">
          {translation}
        </p>
      ))}
    </div>
  );
}
```

### 10. TranslationItem 컴포넌트 (components/TranslationItem.tsx)

매칭되지 않은 번역 항목을 표시합니다.

```typescript
import { OrphanTranslationEntry } from "../hooks/useMeeting";

interface TranslationItemProps {
  translation: OrphanTranslationEntry;
}

export function TranslationItem({ translation }: TranslationItemProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-start gap-2">
        <span className="text-xs font-medium text-slate-500">{translation.speaker}</span>
        <p className="text-sm text-blue-600">{translation.translatedText}</p>
      </div>
    </div>
  );
}
```

### 11. QuickTranslate 컴포넌트 (components/QuickTranslate.tsx)

빠른 한→영 번역 UI입니다.

```typescript
import { useTranslate } from "../hooks/useTranslate";

export function QuickTranslate() {
  const {
    inputText,
    outputText,
    isLoading,
    error,
    setInputText,
    translate,
    copyToClipboard,
    clear,
  } = useTranslate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    translate();
  };

  const handleCopy = async () => {
    const success = await copyToClipboard();
    if (success) {
      // Show toast or visual feedback
    }
  };

  return (
    <section className="rounded-lg border bg-white p-4" aria-label="Quick Translate">
      <h2 className="text-lg font-semibold mb-4">Quick Translate</h2>
      
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="ko-input" className="sr-only">
            Korean text input
          </label>
          <textarea
            id="ko-input"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="한국어를 입력하세요..."
            className="w-full rounded border p-2 text-sm resize-none"
            rows={3}
            disabled={isLoading}
            aria-describedby={error ? "translate-error" : undefined}
          />
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="flex-1 rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? "Translating..." : "Translate"}
          </button>
          <button
            type="button"
            onClick={clear}
            className="rounded border px-4 py-2 text-sm hover:bg-slate-50"
          >
            Clear
          </button>
        </div>
      </form>

      {error && (
        <p id="translate-error" className="mt-2 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      {outputText && (
        <div className="mt-4 space-y-2">
          <div className="rounded bg-slate-50 p-3">
            <p className="text-sm">{outputText}</p>
          </div>
          <button
            onClick={handleCopy}
            className="text-sm text-blue-600 hover:underline"
            aria-label="Copy translation to clipboard"
          >
            Copy to clipboard
          </button>
        </div>
      )}
    </section>
  );
}
```

### 12. SuggestionsPanel 컴포넌트 (components/SuggestionsPanel.tsx)

AI 제안 질문을 표시합니다.

```typescript
import { SuggestionItem } from "../types/events";

interface SuggestionsPanelProps {
  suggestions: SuggestionItem[];
}

export function SuggestionsPanel({ suggestions }: SuggestionsPanelProps) {
  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    // Show toast or visual feedback
  };

  return (
    <section className="rounded-lg border bg-white p-4" aria-label="AI Suggestions">
      <h2 className="text-lg font-semibold mb-4">AI Suggestions</h2>

      {suggestions.length === 0 ? (
        <p className="text-sm text-slate-500">
          Suggestions will appear as the meeting progresses...
        </p>
      ) : (
        <ul className="space-y-3" role="list">
          {suggestions.map((item, index) => (
            <li key={index} className="space-y-1">
              <button
                onClick={() => handleCopy(item.en)}
                className="w-full text-left rounded p-2 hover:bg-slate-50 transition-colors"
                aria-label={`Copy suggestion: ${item.en}`}
              >
                <p className="text-sm font-medium">{item.en}</p>
                <p className="text-xs text-slate-500">{item.ko}</p>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
```


### 13. TranscribeControls 컴포넌트 (components/TranscribeControls.tsx)

전사 시작/중단 버튼입니다.

```typescript
interface TranscribeControlsProps {
  isRecording: boolean;
  isConnected: boolean;
  onStart: () => void;
  onStop: () => void;
}

export function TranscribeControls({
  isRecording,
  isConnected,
  onStart,
  onStop,
}: TranscribeControlsProps) {
  return (
    <div className="flex items-center gap-3">
      {isRecording && (
        <span className="text-xs text-slate-500">
          {isConnected ? "Live" : "Reconnecting..."}
        </span>
      )}

      {isRecording ? (
        <button
          onClick={onStop}
          className="flex items-center gap-2 rounded-full bg-red-100 px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-200"
          aria-label="Stop transcribing"
        >
          <span className="h-3 w-3 rounded bg-red-500" aria-hidden />
          Stop
        </button>
      ) : (
        <button
          onClick={onStart}
          className="rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          aria-label="Start transcribing"
        >
          Start transcribing
        </button>
      )}
    </div>
  );
}
```

### 14. MicSettingsPanel 컴포넌트 (components/MicSettingsPanel.tsx)

마이크 선택 및 테스트를 제공하는 패널입니다.

```typescript
import { useEffect, useState } from "react";

interface AudioDeviceOption {
  deviceId: string;
  label: string;
}

export function MicSettingsPanel() {
  const [devices, setDevices] = useState<AudioDeviceOption[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");

  useEffect(() => {
    navigator.mediaDevices.enumerateDevices().then((items) => {
      const mics = items
        .filter((item) => item.kind === "audioinput")
        .map((item) => ({ deviceId: item.deviceId, label: item.label || "Microphone" }));
      setDevices(mics);
      if (!selectedDeviceId && mics.length > 0) {
        setSelectedDeviceId(mics[0].deviceId);
      }
    });
  }, [selectedDeviceId]);

  return (
    <button className="rounded-full border px-3 py-2 text-sm" aria-label="Microphone settings">
      Settings
    </button>
  );
}
```

### 15. ErrorBanner 컴포넌트 (components/ErrorBanner.tsx)

에러 메시지를 표시합니다.

```typescript
import { ErrorEvent } from "../types/events";

interface ErrorBannerProps {
  error: ErrorEvent;
  onDismiss: () => void;
  onRetry?: () => void;
}

export function ErrorBanner({ error, onDismiss, onRetry }: ErrorBannerProps) {
  return (
    <div
      className="flex items-center justify-between bg-red-50 border-b border-red-200 p-3"
      role="alert"
    >
      <div className="flex items-center gap-2">
        <span className="text-red-600">⚠</span>
        <p className="text-sm text-red-800">{error.message}</p>
      </div>
      <div className="flex gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-sm text-red-600 hover:underline"
          >
            Retry
          </button>
        )}
        <button
          onClick={onDismiss}
          className="text-sm text-slate-500 hover:text-slate-700"
          aria-label="Dismiss error"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
```

### 16. App 컴포넌트 (App.tsx)

루트 컴포넌트로 전체 레이아웃을 구성합니다.

```typescript
import { useMeeting } from "./hooks/useMeeting";
import { TopBar } from "./components/TopBar";
import { MeetingPanel } from "./components/MeetingPanel";
import { QuickTranslate } from "./components/QuickTranslate";
import { SuggestionsPanel } from "./components/SuggestionsPanel";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000";

export default function App() {
  const meeting = useMeeting(WS_BASE_URL);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <main className="mx-auto max-w-7xl p-4 md:p-6">
        <div className="mb-6">
          <TopBar
            isRecording={meeting.isRecording}
            isConnected={meeting.isConnected}
            onStart={meeting.startMeeting}
            onStop={meeting.stopMeeting}
          />
        </div>

        <div className="grid gap-4 md:grid-cols-3 md:gap-6">
          <div className="md:col-span-2">
            <MeetingPanel
              isRecording={meeting.isRecording}
              liveTranscripts={meeting.liveTranscripts}
              transcripts={meeting.transcripts}
              orphanTranslations={meeting.orphanTranslations}
              error={meeting.error}
              onReconnect={meeting.reconnect}
              onDismissError={meeting.dismissError}
            />
          </div>

          <div className="space-y-4 md:space-y-6">
            <QuickTranslate />
            <SuggestionsPanel suggestions={meeting.suggestions} />
          </div>
        </div>
      </main>
    </div>
  );
}
```

## Data Models

### 상태 모델

```typescript
// 회의 세션 상태
interface MeetingState {
  isConnected: boolean;      // WebSocket 연결 상태
  isRecording: boolean;      // 오디오 녹음 상태
  sessionId: string | null;  // 현재 세션 ID
  liveTranscripts: TranscriptEntry[]; // 실시간 partial 전사
  transcripts: TranscriptEntry[];  // 확정 전사 목록
  orphanTranslations: OrphanTranslationEntry[]; // 매칭되지 않은 번역
  suggestions: SuggestionItem[];   // AI 제안 목록
  error: ErrorEvent | null;  // 현재 에러
}

// 전사 항목
interface TranscriptEntry {
  id: string;           // 고유 ID
  kind: "transcript";
  speaker: string;      // 화자 라벨
  text: string;         // 전사 텍스트
  isFinal: boolean;     // final 여부
  ts: number;           // 타임스탬프
  translations: string[]; // 번역 목록
}

interface OrphanTranslationEntry {
  id: string;
  kind: "translation";
  speaker: string;
  sourceTs: number;
  translatedText: string;
  ts: number;
}

// 번역 상태
interface TranslateState {
  inputText: string;    // 입력 텍스트
  outputText: string;   // 번역 결과
  isLoading: boolean;   // 로딩 상태
  error: string | null; // 에러 메시지
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Session Lifecycle State Management

*For any* sequence of start/stop actions, the meeting state SHALL correctly reflect the current session status: `isRecording` SHALL be true after start and false after stop, and `isConnected` SHALL reflect the actual WebSocket connection state.

**Validates: Requirements 1.1, 1.3**

### Property 2: Session Control Message Emission

*For any* start/stop action, the client SHALL send `session.start` or `session.stop` control messages and update state locally (`sessionId` set on start, cleared on stop).

**Validates: Requirements 1.2, 1.4**

### Property 3: Transcript Partial/Final State Management

*For any* `transcript.partial` event, the state SHALL contain (or update) a live transcript entry for that speaker with the event's text. *For any* `transcript.final` event, the live entry for that speaker SHALL be removed and a final entry SHALL be appended to the history list. Live entries that receive no updates for 10 seconds SHALL be pruned to avoid stale partials.

**Validates: Requirements 3.1, 3.2**

### Property 4: Transcript Ordering and Speaker Preservation

*For any* collection of transcript entries in state, history entries SHALL be ordered by timestamp (ts field) in reverse chronological order (latest first), and each entry SHALL preserve its speaker label from the original event.

**Validates: Requirements 3.3, 3.5**

### Property 5: Translation Association with Source Transcript

*For any* `translation.final` event received, the translation text SHALL be appended to the transcript entry whose `ts` matches the event's `sourceTs` field. If the translation targets a live (partial) transcript, the latest translation SHALL replace the prior draft translation for that live entry. If no match exists, the translation SHALL be stored as an orphan translation and rendered in chronological order.

**Validates: Requirements 4.1, 4.3, 4.5, 4.6**

### Property 6: Quick Translate State Machine

*For any* sequence of translate operations:
- The translate button SHALL be enabled if and only if inputText is non-empty
- `isLoading` SHALL be true during API request and false otherwise
- `outputText` SHALL contain the API response on success
- `error` SHALL contain the error message on failure

**Validates: Requirements 5.1, 5.3, 5.4, 5.5**

### Property 7: Suggestions State Management

*For any* `suggestions.update` event received, the suggestions state SHALL contain exactly the items from the event, replacing any previous suggestions. Each item SHALL preserve both `en` and `ko` fields.

**Validates: Requirements 6.1, 6.2, 6.4**

### Property 8: Error State Management

*For any* `error` event received via WebSocket, the error state SHALL contain the event's code, message, and retryable fields. The error SHALL be clearable via dismiss action (setting error to null).

**Validates: Requirements 7.1, 7.2, 7.5**

### Property 9: WebSocket Event Type Discrimination

*For any* valid WebSocket event received, the event handler SHALL correctly discriminate the event type and route it to the appropriate state update handler based on the `type` field (including `server.pong`).

**Validates: Requirements 1.2, 3.1, 3.2, 4.1, 6.1, 7.1**

### Property 10: Audio Chunk Streaming Continuity

*For any* active recording session, audio chunks SHALL be continuously sent to the WebSocket at regular intervals (within 20-100ms tolerance) while the session remains active.

**Validates: Requirements 2.4**

### Property 11: Keepalive Timeout Handling

*For any* keepalive cycle, if a `server.pong` is not received within 30 seconds of a `client.ping`, the client SHALL surface a connection error and require a user-triggered reconnect.

**Validates: Requirements 1.8, 1.9**

## Error Handling

### WebSocket 연결 오류
- **연결 실패/끊김**: 에러 표시 후 재연결 버튼 제공 (새 sessionId로 재연결)
- **Keepalive 타임아웃**: 30초 내 `server.pong` 미수신 시 연결 오류 표시
- **메시지 파싱 오류**: 콘솔 로깅, 세션 유지

### 오디오 캡처 오류
- **권한 거부**: 명확한 에러 메시지 표시, 권한 요청 방법 안내
- **장치 없음**: 마이크 연결 확인 메시지 표시
- **캡처 실패**: 에러 로깅, 세션 종료

### API 오류
- **네트워크 오류**: 재시도 옵션 제공
- **서버 오류 (5xx)**: 에러 메시지 표시, 재시도 가능
- **클라이언트 오류 (4xx)**: 에러 메시지 표시, 입력 검증

### 일반 오류 처리
- 모든 에러는 사용자 친화적 메시지로 표시
- 기술적 세부사항은 콘솔에만 로깅
- 에러 발생 시에도 앱 크래시 방지 (Error Boundary)

## Testing Strategy

### 테스트 프레임워크

| 구성요소 | 테스트 프레임워크 | 속성 기반 테스트 |
|---------|-----------------|----------------|
| Components | Vitest + React Testing Library | Vitest + fast-check |
| Hooks | Vitest + @testing-library/react-hooks | Vitest + fast-check |
| Lib modules | Vitest | Vitest + fast-check |

### 단위 테스트 (Unit Tests)

**Hooks:**
- useMeeting: 상태 초기화, 이벤트 핸들링, 세션 시작/종료
- useTranslate: 입력 변경, 번역 요청, 에러 처리

**Components:**
- MeetingPanel: 렌더링, 전사 표시, 에러 배너
- QuickTranslate: 입력/출력, 버튼 상태, 로딩 표시
- SuggestionsPanel: 제안 표시, 빈 상태

**Lib modules:**
- MeetingWsClient: 연결, 메시지 파싱, 재연결
- AudioCapture: 시작/종료, PCM 변환
- API: 요청/응답, 에러 처리

### 속성 기반 테스트 (Property-Based Tests)

**Property 3: Transcript Partial/Final State Management**
- 다양한 partial/final 이벤트 시퀀스에 대해 상태 전이 검증

**Property 4: Transcript Ordering and Speaker Preservation**
- 다양한 타임스탬프와 화자 조합에 대해 정렬 및 보존 검증

**Property 5: Translation Association with Source Transcript**
- 다양한 sourceTs 값에 대해 올바른 연결 검증

**Property 6: Quick Translate State Machine**
- 다양한 입력과 API 응답에 대해 상태 전이 검증

**Property 7: Suggestions State Management**
- 다양한 suggestions.update 이벤트에 대해 상태 교체 검증

**Property 9: WebSocket Event Type Discrimination**
- 모든 이벤트 타입에 대해 올바른 핸들러 라우팅 검증

### 테스트 설정

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
  },
});
```

- 각 속성 기반 테스트는 최소 100회 반복 실행
- 테스트 태그 형식: `Feature: frontend-implementation, Property N: [property_text]`
