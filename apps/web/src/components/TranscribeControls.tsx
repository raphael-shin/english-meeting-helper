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
  return (
    <div className="flex items-center gap-3">
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
        onClick={onEnd}
        disabled={!isRecording && !isPaused}
        className="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-xs font-semibold text-slate-600 shadow-sm hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
        aria-label="End session"
      >
        End session
      </button>
    </div>
  );
}
