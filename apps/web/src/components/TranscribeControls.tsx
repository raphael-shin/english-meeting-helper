interface TranscribeControlsProps {
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
}

export function TranscribeControls({
  isRecording,
  onStart,
  onStop,
}: TranscribeControlsProps) {
  return (
    <div className="flex items-center gap-3">
      {isRecording ? (
        <button
          onClick={onStop}
          className="flex items-center gap-2 rounded-full bg-red-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-red-500/20 hover:bg-red-600"
          aria-label="Stop transcribing"
        >
          <span className="h-3 w-3 rounded bg-red-100" aria-hidden />
          Stop
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
    </div>
  );
}
