import { useCallback, useEffect, useRef, useState } from "react";

import { AudioCapture } from "../lib/audio";
import { logDebug } from "../lib/debug";
import { MeetingWsClient } from "../lib/ws";
import {
  DisplayUpdateEvent,
  ErrorEvent,
  SuggestionItem,
  SubtitleSegment,
  TranscriptCorrectedEvent,
  TranscriptFinalEvent,
  TranscriptPartialEvent,
  TranslationFinalEvent,
  TranslationCorrectedEvent,
  WebSocketEvent,
} from "../types/events";
import { ProviderMode } from "../types/provider";

export interface TranscriptEntry {
  id: string;
  kind: "transcript";
  speaker: string;
  text: string;
  isFinal: boolean;
  ts: number;
  segmentId: number;
  translations: TranslationEntry[];
}

export interface TranslationEntry {
  speaker: string;
  sourceTs: number;
  sourceText: string;
  translatedText: string;
  segmentId: number;
}

export interface OrphanTranslationEntry extends TranslationEntry {
  id: string;
  kind: "translation";
  ts: number;
}

export interface SummaryData {
  markdown: string;
}

export interface MeetingState {
  isConnected: boolean;
  isRecording: boolean;
  isPaused: boolean;
  sessionId: string | null;
  liveTranscripts: TranscriptEntry[];
  transcripts: TranscriptEntry[];
  orphanTranslations: OrphanTranslationEntry[];
  suggestions: SuggestionItem[];
  summary: SummaryData | null;
  summaryStatus: "idle" | "loading" | "ready" | "error";
  summaryError: string | null;
  error: ErrorEvent | null;
  displayBuffer: {
    confirmed: SubtitleSegment[];
    current: SubtitleSegment | null;
  };
}

const LIVE_TRANSCRIPT_PARTIAL_TTL_MS = 25_000;
const LIVE_TRANSCRIPT_PRUNE_INTERVAL_MS = 2_000;
const LIVE_TRANSCRIPT_HISTORY_LIMIT = 10;

const PROVIDER_SAMPLE_RATES: Record<ProviderMode, number> = {
  AWS: 16000,
  OPENAI: 24000,
};

export function useMeeting(
  wsBaseUrl: string,
  providerMode: ProviderMode = "AWS"
) {
  const [state, setState] = useState<MeetingState>({
    isConnected: false,
    isRecording: false,
    isPaused: false,
    sessionId: null,
    liveTranscripts: [],
    transcripts: [],
    orphanTranslations: [],
    suggestions: [],
    summary: null,
    summaryStatus: "idle",
    summaryError: null,
    error: null,
    displayBuffer: { confirmed: [], current: null },
  });

  const wsClientRef = useRef<MeetingWsClient | null>(null);
  const audioCaptureRef = useRef<AudioCapture | null>(null);
  const pendingPromptRef = useRef<string | null>(null);
  const lastPromptRef = useRef<string | null>(null);
  const lastLiveCountRef = useRef<number>(0);
  const lastHistoryCountRef = useRef<number>(0);
  const lastConfirmedCountRef = useRef<number>(0);
  const lastCurrentIdRef = useRef<number | null>(null);

  const handlePartialTranscript = (event: TranscriptPartialEvent) => {
    setState((current) => {
      const existing = current.liveTranscripts.find(
        (entry) => !entry.isFinal && entry.segmentId === event.segmentId
      );
      const updated: TranscriptEntry = existing
        ? {
            ...existing,
            text: event.text,
            ts: event.ts,
            segmentId: event.segmentId,
          }
        : {
            id: `partial-${event.segmentId}`,
            kind: "transcript",
            speaker: event.speaker,
            text: event.text,
            isFinal: false,
            ts: event.ts,
            segmentId: event.segmentId,
            translations: [],
          };
      return {
        ...current,
        liveTranscripts: [
          ...current.liveTranscripts.filter(
            (entry) => entry.isFinal || entry.segmentId !== event.segmentId
          ),
          updated,
        ],
      };
    });
  };

  const handleFinalTranscript = (event: TranscriptFinalEvent) => {
    setState((current) => {
      const liveTranscripts = [...current.liveTranscripts];
      const existingIndex = liveTranscripts.findIndex(
        (entry) => entry.segmentId === event.segmentId
      );
      const existing =
        existingIndex >= 0 ? liveTranscripts[existingIndex] : null;
      const finalEntry: TranscriptEntry = {
        id: `final-${event.segmentId}`,
        kind: "transcript",
        speaker: event.speaker,
        text: event.text,
        isFinal: true,
        ts: event.ts,
        segmentId: event.segmentId,
        translations: existing?.translations ?? [],
      };
      if (existingIndex >= 0) {
        liveTranscripts[existingIndex] = finalEntry;
      } else {
        liveTranscripts.push(finalEntry);
      }
      const trimmedFinals = liveTranscripts
        .filter(
          (entry) =>
            entry.isFinal ||
            entry.segmentId === event.segmentId
        )
        .sort(
          (left, right) =>
            right.segmentId - left.segmentId
        )
        .slice(0, LIVE_TRANSCRIPT_HISTORY_LIMIT);
      const historyFinals = current.transcripts.filter(
        (entry) =>
          entry.isFinal &&
          entry.segmentId !== event.segmentId
      );
      return {
        ...current,
        liveTranscripts: trimmedFinals,
        transcripts: [...historyFinals, finalEntry],
      };
    });
  };

  const handleTranslation = (event: TranslationFinalEvent) => {
    const translationEntry: TranslationEntry = {
      speaker: event.speaker,
      sourceTs: event.sourceTs,
      sourceText: event.sourceText,
      translatedText: event.translatedText,
      segmentId: event.segmentId,
    };
    setState((current) => {
      const transcripts = [...current.transcripts];
      const targetIndex = transcripts.findIndex(
        (entry) => entry.segmentId === event.segmentId
      );
      if (targetIndex >= 0) {
        const target = transcripts[targetIndex];
        const translations = target.translations.some(
          (entry) =>
            entry.translatedText === translationEntry.translatedText &&
            entry.sourceText === translationEntry.sourceText
        )
          ? target.translations
          : [...target.translations, translationEntry];
        transcripts[targetIndex] = {
          ...target,
          translations,
        };
        const liveTranscripts = current.liveTranscripts.map((entry) =>
          entry.segmentId === event.segmentId
            ? { ...entry, translations }
            : entry
        );
        return { ...current, transcripts, liveTranscripts };
      }

      const liveTranscripts = [...current.liveTranscripts];
      const liveIndex = liveTranscripts.findIndex(
        (entry) => entry.segmentId === event.segmentId
      );
      if (liveIndex >= 0) {
        const target = liveTranscripts[liveIndex];
        const translations = target.translations.some(
          (entry) =>
            entry.translatedText === translationEntry.translatedText &&
            entry.sourceText === translationEntry.sourceText
        )
          ? target.translations
          : [...target.translations, translationEntry];
        liveTranscripts[liveIndex] = {
          ...target,
          translations,
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
              ...translationEntry,
            },
          ],
        };
      }
      return current;
    });
  };

  const handleTranslationCorrected = (event: TranslationCorrectedEvent) => {
    const translationEntry: TranslationEntry = {
      speaker: event.speaker,
      sourceTs: event.ts,
      sourceText: event.sourceText,
      translatedText: event.translatedText,
      segmentId: event.segmentId,
    };
    setState((current) => ({
      ...current,
      transcripts: current.transcripts.map((entry) =>
        entry.segmentId === event.segmentId
          ? { ...entry, translations: [translationEntry] }
          : entry
      ),
    }));
  };

  const handleTranscriptCorrected = (event: TranscriptCorrectedEvent) => {
    setState((current) => ({
      ...current,
      transcripts: current.transcripts.map((entry) =>
        entry.segmentId === event.segmentId
          ? { ...entry, text: event.correctedText }
          : entry
      ),
    }));
  };

  const handleDisplayUpdate = (event: DisplayUpdateEvent) => {
    logDebug(
      "display.update",
      {
        confirmedCount: event.confirmed.length,
        currentSegmentId: event.current?.segmentId ?? null,
        currentTextLen: event.current?.text.length ?? 0,
      },
      { sampleRate: 1, level: "info" }
    );
    
    // Log current (Composing) text for debugging disappearing text
    if (event.current) {
      console.log(`[COMPOSING] segmentId=${event.current.segmentId} text="${event.current.text}"`);
    } else {
      console.log(`[COMPOSING] current=null (cleared)`);
    }
    
    setState((current) => {
      // Preserve previous translation if new one is null
      const previousCurrent = current.displayBuffer.current;
      const newCurrent = event.current
        ? {
            ...event.current,
            translation:
              event.current.translation ??
              (previousCurrent?.segmentId === event.current.segmentId
                ? previousCurrent.translation
                : undefined),
          }
        : null;

      return {
        ...current,
        displayBuffer: {
          confirmed: event.confirmed,
          current: newCurrent,
        },
      };
    });
  };

  const handleEvent = useCallback((event: WebSocketEvent) => {
    logDebug(
      "meeting.event",
      {
        type: event.type,
        segmentId: "segmentId" in event ? event.segmentId : undefined,
        ts: event.ts,
      },
      { sampleRate: 0.2 }
    );
    if (event.type === "display.update") {
      logDebug(
        "meeting.display_event",
        {
          confirmedCount: event.confirmed.length,
          currentSegmentId: event.current?.segmentId ?? null,
        },
        { sampleRate: 1, level: "info" }
      );
    }
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
      case "translation.corrected":
        handleTranslationCorrected(event);
        break;
      case "transcript.corrected":
        handleTranscriptCorrected(event);
        break;
      case "display.update":
        handleDisplayUpdate(event);
        break;
      case "suggestions.update":
        setState((current) => ({ ...current, suggestions: event.items }));
        break;
      case "summary.update":
        setState((current) => ({
          ...current,
          summary: event.summaryMarkdown
            ? {
                markdown: event.summaryMarkdown,
              }
            : null,
          summaryStatus: event.error ? "error" : "ready",
          summaryError: event.error ?? null,
        }));
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
    const sampleRate = PROVIDER_SAMPLE_RATES[providerMode] as 16000 | 24000;

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
          isPaused: false,
        }));
      }
    );

    wsClientRef.current.connect(sessionId, {
      type: "session.start",
      sampleRate,
      format: "pcm_s16le",
      lang: "en-US",
    });
    if (lastPromptRef.current) {
      pendingPromptRef.current = lastPromptRef.current;
    }

    audioCaptureRef.current = new AudioCapture();
    await audioCaptureRef.current.start(
      { sampleRate, chunkIntervalMs: 100 },
      (chunk) => wsClientRef.current?.sendAudio(chunk)
    );

    setState((current) => ({
      ...current,
      sessionId,
      isRecording: true,
      isPaused: false,
      liveTranscripts: [],
      transcripts: [],
      orphanTranslations: [],
      suggestions: [],
      summary: null,
      summaryStatus: "idle",
      summaryError: null,
      error: null,
      displayBuffer: { confirmed: [], current: null },
    }));
  }, [handleEvent, providerMode, wsBaseUrl]);

  const pauseMeeting = useCallback(() => {
    audioCaptureRef.current?.stop();
    setState((current) => ({
      ...current,
      isRecording: false,
      isPaused: true,
    }));
  }, []);

  const resumeMeeting = useCallback(async () => {
    if (!state.sessionId || !wsClientRef.current) {
      await startMeeting();
      return;
    }
    const sampleRate = PROVIDER_SAMPLE_RATES[providerMode] as 16000 | 24000;
    audioCaptureRef.current?.stop();
    audioCaptureRef.current = new AudioCapture();
    await audioCaptureRef.current.start(
      { sampleRate, chunkIntervalMs: 100 },
      (chunk) => wsClientRef.current?.sendAudio(chunk)
    );
    setState((current) => ({
      ...current,
      isRecording: true,
      isPaused: false,
      error: null,
    }));
  }, [providerMode, startMeeting, state.sessionId]);

  const endSession = useCallback(() => {
    wsClientRef.current?.sendControl({ type: "session.stop" });
    audioCaptureRef.current?.stop();
    wsClientRef.current?.disconnect();
    setState((current) => ({
      ...current,
      isRecording: false,
      isPaused: false,
      sessionId: null,
      liveTranscripts: [],
      displayBuffer: { confirmed: [], current: null },
    }));
  }, []);

  const reconnect = useCallback(async () => {
    const sessionId = crypto.randomUUID().toLowerCase();
    const sampleRate = PROVIDER_SAMPLE_RATES[providerMode] as 16000 | 24000;
    wsClientRef.current?.reconnect(sessionId, {
      type: "session.start",
      sampleRate,
      format: "pcm_s16le",
      lang: "en-US",
    });
    if (lastPromptRef.current) {
      pendingPromptRef.current = lastPromptRef.current;
    }
    audioCaptureRef.current?.stop();
    audioCaptureRef.current = new AudioCapture();
    await audioCaptureRef.current.start(
      { sampleRate, chunkIntervalMs: 100 },
      (chunk) => wsClientRef.current?.sendAudio(chunk)
    );
    setState((current) => ({
      ...current,
      sessionId,
      isRecording: true,
      isPaused: false,
      liveTranscripts: [],
      error: null,
      displayBuffer: { confirmed: [], current: null },
    }));
  }, [providerMode]);

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

  const requestSummary = useCallback(() => {
    if (!wsClientRef.current || !state.isConnected) {
      setState((current) => ({
        ...current,
        summaryStatus: "error",
        summaryError: "Not connected.",
      }));
      return;
    }
    setState((current) => ({
      ...current,
      summaryStatus: "loading",
      summaryError: null,
    }));
    wsClientRef.current.sendControl({ type: "summary.request" });
  }, [state.isConnected]);

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
          (entry) =>
            entry.isFinal || now - entry.ts < LIVE_TRANSCRIPT_PARTIAL_TTL_MS
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
    if (state.liveTranscripts.length !== lastLiveCountRef.current) {
      logDebug("state.live_transcripts", {
        count: state.liveTranscripts.length,
        delta: state.liveTranscripts.length - lastLiveCountRef.current,
      });
      lastLiveCountRef.current = state.liveTranscripts.length;
    }
    if (state.transcripts.length !== lastHistoryCountRef.current) {
      logDebug("state.history_transcripts", {
        count: state.transcripts.length,
        delta: state.transcripts.length - lastHistoryCountRef.current,
      });
      lastHistoryCountRef.current = state.transcripts.length;
    }
    if (state.displayBuffer.confirmed.length !== lastConfirmedCountRef.current) {
      logDebug(
        "state.display_confirmed",
        {
          count: state.displayBuffer.confirmed.length,
          delta:
            state.displayBuffer.confirmed.length -
            lastConfirmedCountRef.current,
        },
        { sampleRate: 1, level: "info" }
      );
      lastConfirmedCountRef.current = state.displayBuffer.confirmed.length;
    }
    const currentId = state.displayBuffer.current?.segmentId ?? null;
    if (currentId !== lastCurrentIdRef.current) {
      logDebug(
        "state.display_current",
        { segmentId: currentId },
        { sampleRate: 1, level: "info" }
      );
      lastCurrentIdRef.current = currentId;
    }
  }, [
    state.liveTranscripts.length,
    state.transcripts.length,
    state.displayBuffer,
  ]);

  useEffect(() => {
    return () => {
      audioCaptureRef.current?.stop();
      wsClientRef.current?.disconnect();
    };
  }, []);

  return {
    ...state,
    startMeeting,
    pauseMeeting,
    resumeMeeting,
    endSession,
    reconnect,
    dismissError,
    sendSuggestionsPrompt,
    requestSummary,
  };
}
