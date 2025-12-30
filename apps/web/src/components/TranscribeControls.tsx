import { useState } from "react";

interface TranscribeControlsProps {
  isRecording: boolean;
  isPaused: boolean;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onEnd: () => void;
}

export function TranscribeControls({
  isRecording,
  isPaused,
  onStart,
  onPause,
  onResume,
  onEnd,
}: TranscribeControlsProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const canEnd = isRecording || isPaused;

  return (
    <div className="relative flex items-center gap-3">
      {isRecording ? (
        <button
          onClick={onPause}
          className="flex items-center gap-2 rounded-full bg-orange-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-orange-500/20 hover:bg-orange-600"
          aria-label="Pause transcribing"
        >
          <span className="h-3 w-3 rounded bg-orange-100" aria-hidden />
          Pause
        </button>
      ) : isPaused ? (
        <button
          onClick={onResume}
          className="rounded-full bg-[var(--accent)] px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-500/30 transition hover:bg-[var(--accent-strong)]"
          aria-label="Resume transcribing"
        >
          Resume
        </button>
      ) : (
        <button
          onClick={onStart}
          className="rounded-full bg-[var(--accent)] px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-500/30 transition hover:bg-[var(--accent-strong)]"
          aria-label="Start transcribing"
        >
          Start transcribing
        </button>
      )}
      <button
        onClick={() => setShowConfirm(true)}
        disabled={!canEnd}
        className="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-xs font-semibold text-slate-600 shadow-sm hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
        aria-label="End session"
      >
        End session
      </button>
      {showConfirm && (
        <div className="absolute right-0 top-14 z-50 w-72 rounded-2xl border border-white/70 bg-white/95 p-4 shadow-xl backdrop-blur">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-red-100 text-red-600">
              <span className="text-sm font-bold">!</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">
                End this session?
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Live captions will be cleared. History stays in this tab.
              </p>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-end gap-2">
            <button
              onClick={() => setShowConfirm(false)}
              className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                setShowConfirm(false);
                onEnd();
              }}
              className="rounded-full bg-red-500 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-red-600"
            >
              End session
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
