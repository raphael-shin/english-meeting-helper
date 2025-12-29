export interface BaseEvent {
  type: string;
  ts: number;
}

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

export interface TranslationFinalEvent extends BaseEvent {
  type: "translation.final";
  sessionId: string;
  sourceTs: number;
  speaker: string;
  sourceText: string;
  translatedText: string;
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
  | TranscriptPartialEvent
  | TranscriptFinalEvent
  | TranslationFinalEvent
  | SuggestionsUpdateEvent
  | ErrorEvent
  | ServerPongEvent;

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
