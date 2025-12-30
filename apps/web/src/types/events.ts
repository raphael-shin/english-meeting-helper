export interface BaseEvent {
  type: string;
  ts: number;
}

export interface SubtitleSegment {
  id: string;
  text: string;
  speaker: string;
  startTime: number;
  endTime: number | null;
  isFinal: boolean;
  llmCorrected: boolean;
  segmentId: number;
  translation?: string;
}

export interface DisplayUpdateEvent extends BaseEvent {
  type: "display.update";
  sessionId: string;
  confirmed: SubtitleSegment[];
  current: SubtitleSegment | null;
}

export interface TranscriptPartialEvent extends BaseEvent {
  type: "transcript.partial";
  sessionId: string;
  speaker: string;
  text: string;
  segmentId: number;
}

export interface TranscriptFinalEvent extends BaseEvent {
  type: "transcript.final";
  sessionId: string;
  speaker: string;
  text: string;
  segmentId: number;
}

export interface TranslationFinalEvent extends BaseEvent {
  type: "translation.final";
  sessionId: string;
  sourceTs: number;
  segmentId: number;
  speaker: string;
  sourceText: string;
  translatedText: string;
}

export interface TranslationCorrectedEvent extends BaseEvent {
  type: "translation.corrected";
  sessionId: string;
  segmentId: number;
  speaker: string;
  sourceText: string;
  translatedText: string;
}

export interface TranscriptCorrectedEvent extends BaseEvent {
  type: "transcript.corrected";
  sessionId: string;
  segmentId: number;
  originalText: string;
  correctedText: string;
}

export interface SuggestionItem {
  en: string;
  ko: string;
}

export interface SuggestionsUpdateEvent extends BaseEvent {
  type: "suggestions.update";
  sessionId: string;
  items: SuggestionItem[];
}

export interface SummaryUpdateEvent extends BaseEvent {
  type: "summary.update";
  sessionId: string;
  summaryMarkdown: string | null;
  error?: string | null;
}

export interface ErrorEvent extends BaseEvent {
  type: "error";
  code: string;
  message: string;
  retryable?: boolean;
}

export interface ServerPongEvent extends BaseEvent {
  type: "server.pong";
}

export type WebSocketEvent =
  | DisplayUpdateEvent
  | TranscriptPartialEvent
  | TranscriptFinalEvent
  | TranscriptCorrectedEvent
  | TranslationFinalEvent
  | TranslationCorrectedEvent
  | SuggestionsUpdateEvent
  | SummaryUpdateEvent
  | ErrorEvent
  | ServerPongEvent;

export interface SessionStartMessage {
  type: "session.start";
  sampleRate: 16000 | 24000;
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

export interface SummaryRequestMessage {
  type: "summary.request";
}

export type ClientControlMessage =
  | SessionStartMessage
  | SessionStopMessage
  | ClientPingMessage
  | SuggestionsPromptMessage
  | SummaryRequestMessage;
