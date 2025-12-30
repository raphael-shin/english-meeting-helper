import { useEffect, useRef, useState } from "react";

import { ErrorEvent, SubtitleSegment } from "../types/events";
import {
  OrphanTranslationEntry,
  TranscriptEntry,
} from "../hooks/useMeeting";
import { ErrorBanner } from "./ErrorBanner";
import { SubtitleItem } from "./SubtitleItem";
import { TranscriptItem } from "./TranscriptItem";
import { TranslationItem } from "./TranslationItem";
import { formatTime } from "../lib/time";

interface MeetingPanelProps {
  isRecording: boolean;
  isPaused: boolean;
  displayBuffer: {
    confirmed: SubtitleSegment[];
    current: SubtitleSegment | null;
  };
  transcripts: TranscriptEntry[];
  orphanTranslations: OrphanTranslationEntry[];
  error: ErrorEvent | null;
  onReconnect: () => void;
  onDismissError: () => void;
}

export function MeetingPanel({
  isRecording,
  isPaused,
  displayBuffer,
  transcripts,
  orphanTranslations,
  error,
  onReconnect,
  onDismissError,
}: MeetingPanelProps) {
  const [activeTab, setActiveTab] = useState<"live" | "history">("live");
  const [historyView, setHistoryView] = useState<"both" | "ko" | "en">("both");
  const [historyCopied, setHistoryCopied] = useState(false);
  const liveScrollRef = useRef<HTMLDivElement>(null);
  const historyScrollRef = useRef<HTMLDivElement>(null);
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
  }, [displayBuffer.confirmed.length, displayBuffer.current?.id]);

  useEffect(() => {
    if (typeof historyScrollRef.current?.scrollTo !== "function") {
      return;
    }
    historyScrollRef.current.scrollTo({ top: 0 });
  }, [historyTimeline.length]);

  const handleCopyHistory = async () => {
    const lines: string[] = [];
    for (const entry of [...historyTimeline].reverse()) {
      const timestamp =
        entry.kind === "transcript"
          ? formatTime(entry.ts)
          : formatTime(entry.sourceTs || entry.ts);
      if (entry.kind === "transcript") {
        if (historyView !== "ko") {
          lines.push(`[${timestamp}] ${entry.text}`);
        }
        if (historyView !== "en") {
          for (const translation of entry.translations) {
            lines.push(`[${timestamp}] ${translation.translatedText}`);
          }
        }
      } else {
        if (historyView !== "ko") {
          lines.push(`[${timestamp}] ${entry.sourceText}`);
        }
        if (historyView !== "en") {
          lines.push(`[${timestamp}] ${entry.translatedText}`);
        }
      }
    }
    try {
      await navigator.clipboard.writeText(lines.join("\n"));
      setHistoryCopied(true);
      window.setTimeout(() => setHistoryCopied(false), 1500);
    } catch (error) {
      console.error("Failed to copy history:", error);
    }
  };

  return (
    <section
      className="flex h-full min-h-0 flex-col rounded-3xl border border-white/60 bg-white/80 shadow-[var(--shadow)] backdrop-blur"
      aria-label="Meeting Panel"
    >
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-white/70 px-4 py-3">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Transcript</h2>
          <p className="text-xs text-slate-500">Live captions and session history</p>
        </div>
        <div
          className="flex items-center rounded-full border border-white/70 bg-white/80 p-1 text-xs font-semibold uppercase tracking-wide"
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
          className={`flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-slate-900/20 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-slate-100 shadow-[0_30px_60px_rgba(15,23,42,0.45)] ${
            activeTab === "live" ? "" : "hidden"
          }`}
        >
          <div className="flex items-center justify-between border-b border-white/10 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-emerald-200/80">
            <span className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span
                  className={`absolute inline-flex h-full w-full rounded-full bg-emerald-400 ${
                    isRecording ? "animate-ping opacity-75" : "opacity-0"
                  }`}
                />
                <span
                  className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
                    isPaused ? "bg-orange-300" : "bg-emerald-400"
                  }`}
                />
              </span>
              <span>{isPaused ? "Paused Feed" : "Live Feed"}</span>
            </span>
            <span className="text-[10px] font-medium normal-case tracking-normal text-emerald-100/60">
              {isPaused ? "Resume to continue" : "Real-time captions"}
            </span>
          </div>
          <div
            ref={liveScrollRef}
            className="flex-1 space-y-4 overflow-y-auto p-3"
            role="log"
            aria-live="polite"
            aria-label="Live transcripts"
          >
            {isPaused && (
              <div className="flex items-center justify-between gap-3 rounded-2xl border border-orange-200/40 bg-orange-50/10 px-4 py-3 text-orange-100">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-orange-500/20 text-orange-200">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      aria-hidden
                    >
                      <path
                        d="M7 4V20M17 4V20"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                      />
                    </svg>
                  </span>
                  <div>
                    <p className="text-sm font-semibold">Paused</p>
                    <p className="text-xs text-orange-200/80">
                      Resume to continue capturing live captions.
                    </p>
                  </div>
                </div>
                <span className="text-[10px] uppercase tracking-[0.2em] text-orange-200/70">
                  Hold
                </span>
              </div>
            )}
            {displayBuffer.confirmed.length === 0 && !displayBuffer.current ? (
              <div className="space-y-4 rounded-2xl border border-white/10 bg-white/5 p-4 text-emerald-100/80">
                <div className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-200/70">
                  {isPaused ? "Paused" : "Ready for captions"}
                </div>
                <p className="text-base">
                  {isRecording
                    ? "Listening for speech..."
                    : isPaused
                      ? "Paused — resume to keep capturing captions."
                      : "Press Start to begin capturing captions."}
                </p>
                <div className="space-y-2">
                  <div className="h-2 w-2/3 rounded-full bg-emerald-300/20 animate-pulse-subtle" />
                  <div className="h-2 w-1/2 rounded-full bg-emerald-300/20 animate-pulse-subtle" />
                  <div className="h-2 w-3/4 rounded-full bg-emerald-300/20 animate-pulse-subtle" />
                </div>
              </div>
            ) : (
              <>
                {displayBuffer.current && (
                  <>
                    <div className="relative mb-4">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-emerald-400/30"></div>
                      </div>
                      <div className="relative flex justify-center">
                        <span className="bg-slate-900 px-3 text-xs text-emerald-200/60 uppercase tracking-wider">
                          Composing
                        </span>
                      </div>
                    </div>
                    <SubtitleItem
                      segment={displayBuffer.current}
                      variant="current"
                    />
                  </>
                )}
                {[...displayBuffer.confirmed].reverse().map((segment, index) => (
                  <SubtitleItem
                    key={segment.id}
                    segment={segment}
                    variant="confirmed"
                    isLatestConfirmed={index === 0}
                  />
                ))}
              </>
            )}
          </div>
        </div>
        <div
          id="history-tabpanel"
          role="tabpanel"
          aria-hidden={activeTab !== "history"}
          aria-labelledby="history-tab"
          className={`flex min-h-0 flex-1 flex-col rounded-2xl border border-slate-100/80 bg-white/90 ${
            activeTab === "history" ? "" : "hidden"
          }`}
        >
          <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <span>History</span>
            <span className="text-[10px] font-normal normal-case text-slate-400">
              Final transcripts
            </span>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-3 py-2">
            <div className="flex items-center rounded-full border border-slate-200 bg-slate-50 p-1 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setHistoryView("both")}
                className={`rounded-full px-3 py-1 ${
                  historyView === "both"
                    ? "bg-slate-900 text-white shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                Both
              </button>
              <button
                type="button"
                onClick={() => setHistoryView("ko")}
                className={`rounded-full px-3 py-1 ${
                  historyView === "ko"
                    ? "bg-slate-900 text-white shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                Korean
              </button>
              <button
                type="button"
                onClick={() => setHistoryView("en")}
                className={`rounded-full px-3 py-1 ${
                  historyView === "en"
                    ? "bg-slate-900 text-white shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                English
              </button>
            </div>
            <button
              type="button"
              onClick={handleCopyHistory}
              aria-label={historyCopied ? "Copied" : "Copy all transcripts"}
              className={`flex h-8 w-8 items-center justify-center rounded-full border shadow-sm transition ${
                historyCopied
                  ? "border-emerald-200 bg-emerald-50 text-emerald-600"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {historyCopied ? (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden
                >
                  <path
                    d="M5 12L10 17L19 8"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden
                >
                  <rect
                    x="9"
                    y="9"
                    width="11"
                    height="11"
                    rx="2"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <rect
                    x="4"
                    y="4"
                    width="11"
                    height="11"
                    rx="2"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                </svg>
              )}
            </button>
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
                  <TranscriptItem
                    key={entry.id}
                    transcript={entry}
                    tone="history"
                    viewMode={historyView}
                  />
                ) : (
                  <TranslationItem
                    key={entry.id}
                    translation={entry}
                    viewMode={historyView}
                  />
                )
              )
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
