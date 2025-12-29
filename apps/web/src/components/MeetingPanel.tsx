import { useEffect, useRef } from "react";

import { ErrorEvent } from "../types/events";
import {
  OrphanTranslationEntry,
  TranscriptEntry,
} from "../hooks/useMeeting";
import { ErrorBanner } from "./ErrorBanner";
import { TranscriptItem } from "./TranscriptItem";
import { TranslationItem } from "./TranslationItem";

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

  useEffect(() => {
    if (typeof liveScrollRef.current?.scrollTo !== "function") {
      return;
    }
    liveScrollRef.current.scrollTo({ top: 0 });
  }, [liveTimeline.length]);

  useEffect(() => {
    if (typeof historyScrollRef.current?.scrollTo !== "function") {
      return;
    }
    historyScrollRef.current.scrollTo({ top: 0 });
  }, [historyTimeline.length]);

  return (
    <section
      className="flex h-full min-h-0 flex-col rounded-lg border bg-white"
      aria-label="Meeting Panel"
    >
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
            <span className="text-[10px] font-normal normal-case text-slate-400">
              Partial stream
            </span>
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
            <span className="text-[10px] font-normal normal-case text-slate-400">
              Final transcripts
            </span>
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
