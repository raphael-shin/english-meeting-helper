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
          className="flex items-center gap-2 rounded-full bg-red-100 px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-200"
          aria-label="Stop transcribing"
        >
          <span className="h-3 w-3 rounded bg-red-500" aria-hidden />
          Stop
        </button>
      ) : (
        <button
          onClick={onStart}
          className="rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          aria-label="Start transcribing"
        >
          Start transcribing
        </button>
      )}
    </div>
  );
}
