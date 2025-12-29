import { useEffect, useRef, useState } from "react";

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
  const [activeTab, setActiveTab] = useState<"live" | "history">("live");
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
      <header className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
        <h2 className="text-lg font-semibold">Transcript</h2>
        <div
          className="flex items-center rounded-full border border-slate-200 bg-slate-50 p-1 text-xs font-semibold"
          role="tablist"
          aria-label="Transcript tabs"
        >
          <button
            type="button"
            role="tab"
            id="live-tab"
            aria-selected={activeTab === "live"}
            aria-controls="live-tabpanel"
            onClick={() => setActiveTab("live")}
            className={`rounded-full px-3 py-1 transition ${
              activeTab === "live"
                ? "bg-slate-900 text-white shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            Live
          </button>
          <button
            type="button"
            role="tab"
            id="history-tab"
            aria-selected={activeTab === "history"}
            aria-controls="history-tabpanel"
            onClick={() => setActiveTab("history")}
            className={`rounded-full px-3 py-1 transition ${
              activeTab === "history"
                ? "bg-slate-900 text-white shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            History
          </button>
        </div>
      </header>

      {error && (
        <ErrorBanner
          error={error}
          onDismiss={onDismissError}
          onRetry={error.retryable ? onReconnect : undefined}
        />
      )}

      <div className="flex min-h-0 flex-1 flex-col gap-3 p-4">
        <div
          id="live-tabpanel"
          role="tabpanel"
          aria-hidden={activeTab !== "live"}
          aria-labelledby="live-tab"
          className={`flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg border border-slate-900/10 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100 shadow-sm ${
            activeTab === "live" ? "" : "hidden"
          }`}
        >
          <div className="flex items-center justify-between border-b border-white/10 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-200/80">
            <span className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span
                  className={`absolute inline-flex h-full w-full rounded-full bg-emerald-400 ${
                    isRecording ? "animate-ping opacity-75" : "opacity-0"
                  }`}
                />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-400" />
              </span>
              <span>Live</span>
            </span>
            <span className="text-[10px] font-medium normal-case tracking-normal text-emerald-100/60">
              Real-time captions
            </span>
          </div>
          <div
            ref={liveScrollRef}
            className="flex-1 space-y-4 overflow-y-auto p-3"
            role="log"
            aria-live="polite"
            aria-label="Live transcripts"
          >
            {liveTimeline.length === 0 ? (
              <p className="text-base text-emerald-100/70">
                {isRecording
                  ? "Listening for speech..."
                  : "Click Start to begin recording"}
              </p>
            ) : (
              liveTimeline.map((entry) => (
                <TranscriptItem key={entry.id} transcript={entry} tone="live" />
              ))
            )}
          </div>
        </div>
        <div
          id="history-tabpanel"
          role="tabpanel"
          aria-hidden={activeTab !== "history"}
          aria-labelledby="history-tab"
          className={`flex min-h-0 flex-1 flex-col rounded-lg border border-slate-100 bg-white ${
            activeTab === "history" ? "" : "hidden"
          }`}
        >
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
                  <TranscriptItem key={entry.id} transcript={entry} tone="history" />
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
