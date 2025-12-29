import { useCallback, useEffect, useRef, useState } from "react";

import { AudioCapture } from "../lib/audio";
import { MeetingWsClient } from "../lib/ws";
import {
  ErrorEvent,
  SuggestionItem,
  TranscriptFinalEvent,
  TranscriptPartialEvent,
  TranslationFinalEvent,
  WebSocketEvent,
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
  liveTranscripts: TranscriptEntry[];
  transcripts: TranscriptEntry[];
  orphanTranslations: OrphanTranslationEntry[];
  suggestions: SuggestionItem[];
  error: ErrorEvent | null;
}

const LIVE_TRANSCRIPT_TTL_MS = 10_000;
const LIVE_TRANSCRIPT_PRUNE_INTERVAL_MS = 2_000;

export function useMeeting(wsBaseUrl: string) {
  const [state, setState] = useState<MeetingState>({
    isConnected: false,
    isRecording: false,
    sessionId: null,
    liveTranscripts: [],
    transcripts: [],
    orphanTranslations: [],
    suggestions: [],
    error: null,
  });

  const wsClientRef = useRef<MeetingWsClient | null>(null);
  const audioCaptureRef = useRef<AudioCapture | null>(null);
  const pendingPromptRef = useRef<string | null>(null);
  const lastPromptRef = useRef<string | null>(null);

  const handlePartialTranscript = (event: TranscriptPartialEvent) => {
    setState((current) => {
      const existing = current.liveTranscripts.find(
        (entry) => entry.speaker === event.speaker
      );
      const updated: TranscriptEntry = existing
        ? { ...existing, text: event.text, ts: event.ts }
        : {
            id: `partial-${event.speaker}-${event.ts}`,
            kind: "transcript",
            speaker: event.speaker,
            text: event.text,
            isFinal: false,
            ts: event.ts,
            translations: [],
          };
      return {
        ...current,
        liveTranscripts: [
          ...current.liveTranscripts.filter(
            (entry) => entry.speaker !== event.speaker
          ),
          updated,
        ],
      };
    });
  };

  const handleFinalTranscript = (event: TranscriptFinalEvent) => {
    setState((current) => {
      return {
        ...current,
        liveTranscripts: current.liveTranscripts.filter(
          (entry) => entry.speaker !== event.speaker
        ),
        transcripts: [
          ...current.transcripts.filter((entry) => entry.isFinal),
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
    setState((current) => {
      const transcripts = [...current.transcripts];
      const targetIndex = transcripts.findIndex(
        (entry) => entry.ts === event.sourceTs
      );
      if (targetIndex >= 0) {
        const target = transcripts[targetIndex];
        const translations = target.translations.includes(event.translatedText)
          ? target.translations
          : [...target.translations, event.translatedText];
        transcripts[targetIndex] = {
          ...target,
          translations,
        };
        return { ...current, transcripts };
      }

      const liveTranscripts = [...current.liveTranscripts];
      const liveIndex = liveTranscripts.findIndex(
        (entry) => entry.speaker === event.speaker
      );
      if (liveIndex >= 0) {
        const target = liveTranscripts[liveIndex];
        liveTranscripts[liveIndex] = {
          ...target,
          translations: [event.translatedText],
        };
        return { ...current, liveTranscripts };
      }

      const hasSpeaker =
        current.transcripts.some((entry) => entry.speaker === event.speaker) ||
        current.liveTranscripts.some((entry) => entry.speaker === event.speaker);
      if (!hasSpeaker) {
        return {
          ...current,
          orphanTranslations: [
            ...current.orphanTranslations,
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
      return current;
    });
  };

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
        setState((current) => ({ ...current, suggestions: event.items }));
        break;
      case "error":
        setState((current) => ({ ...current, error: event }));
        break;
      case "server.pong":
        break;
    }
  }, []);

  const startMeeting = useCallback(async () => {
    const sessionId = crypto.randomUUID().toLowerCase();

    wsClientRef.current = new MeetingWsClient(
      wsBaseUrl,
      handleEvent,
      (connected) =>
        setState((current) => ({ ...current, isConnected: connected })),
      () => {
        audioCaptureRef.current?.stop();
        setState((current) => ({
          ...current,
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
    if (lastPromptRef.current) {
      pendingPromptRef.current = lastPromptRef.current;
    }

    audioCaptureRef.current = new AudioCapture();
    await audioCaptureRef.current.start(
      { sampleRate: 16000, chunkIntervalMs: 100 },
      (chunk) => wsClientRef.current?.sendAudio(chunk)
    );

    setState((current) => ({
      ...current,
      sessionId,
      isRecording: true,
      liveTranscripts: [],
      transcripts: [],
      orphanTranslations: [],
      suggestions: [],
      error: null,
    }));
  }, [handleEvent, wsBaseUrl]);

  const stopMeeting = useCallback(() => {
    wsClientRef.current?.sendControl({ type: "session.stop" });
    audioCaptureRef.current?.stop();
    wsClientRef.current?.disconnect();
    setState((current) => ({
      ...current,
      isRecording: false,
      sessionId: null,
      liveTranscripts: [],
    }));
  }, []);

  const reconnect = useCallback(async () => {
    const sessionId = crypto.randomUUID().toLowerCase();
    wsClientRef.current?.reconnect(sessionId, {
      type: "session.start",
      sampleRate: 16000,
      format: "pcm_s16le",
      lang: "en-US",
    });
    if (lastPromptRef.current) {
      pendingPromptRef.current = lastPromptRef.current;
    }
    audioCaptureRef.current?.stop();
    audioCaptureRef.current = new AudioCapture();
    await audioCaptureRef.current.start(
      { sampleRate: 16000, chunkIntervalMs: 100 },
      (chunk) => wsClientRef.current?.sendAudio(chunk)
    );
    setState((current) => ({
      ...current,
      sessionId,
      isRecording: true,
      liveTranscripts: [],
      error: null,
    }));
  }, []);

  const dismissError = useCallback(() => {
    setState((current) => ({ ...current, error: null }));
  }, []);

  const sendSuggestionsPrompt = useCallback(
    (prompt: string) => {
      const trimmed = prompt.trim();
      lastPromptRef.current = trimmed;
      if (wsClientRef.current && state.isConnected) {
        wsClientRef.current.sendControl({
          type: "suggestions.prompt",
          prompt: trimmed,
        });
        return;
      }
      pendingPromptRef.current = trimmed;
    },
    [state.isConnected]
  );

  useEffect(() => {
    if (!state.isConnected) {
      return;
    }
    if (pendingPromptRef.current === null) {
      return;
    }
    const pendingPrompt = pendingPromptRef.current;
    pendingPromptRef.current = null;
    wsClientRef.current?.sendControl({
      type: "suggestions.prompt",
      prompt: pendingPrompt,
    });
  }, [state.isConnected]);

  useEffect(() => {
    if (!state.isRecording) {
      return;
    }
    const interval = window.setInterval(() => {
      setState((current) => {
        if (current.liveTranscripts.length === 0) {
          return current;
        }
        const now = Date.now();
        const liveTranscripts = current.liveTranscripts.filter(
          (entry) => now - entry.ts < LIVE_TRANSCRIPT_TTL_MS
        );
        if (liveTranscripts.length === current.liveTranscripts.length) {
          return current;
        }
        return { ...current, liveTranscripts };
      });
    }, LIVE_TRANSCRIPT_PRUNE_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [state.isRecording]);

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
    sendSuggestionsPrompt,
  };
}
