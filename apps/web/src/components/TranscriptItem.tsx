import { TranscriptEntry } from "../hooks/useMeeting";
import { formatTime } from "../lib/time";

interface TranscriptItemProps {
  transcript: TranscriptEntry;
}

export function TranscriptItem({ transcript }: TranscriptItemProps) {
  const timestamp = formatTime(transcript.ts);

  return (
    <div className="grid grid-cols-[auto,1fr] items-start gap-x-2 gap-y-1">
      <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
        <span>{transcript.speaker}</span>
        <span className="text-slate-400">{timestamp}</span>
      </div>
      <p
        className={`text-sm ${
          transcript.isFinal ? "text-slate-900" : "text-slate-400 italic"
        }`}
      >
        {transcript.text}
      </p>
      {transcript.translations.map((translation, index) => (
        <p
          key={`${transcript.id}-tr-${index}`}
          className="col-start-2 text-sm text-blue-600"
        >
          {translation}
        </p>
      ))}
    </div>
  );
}
