import { TranscriptEntry } from "../hooks/useMeeting";
import { formatTime } from "../lib/time";

interface TranscriptItemProps {
  transcript: TranscriptEntry;
  tone?: "live" | "history";
}

export function TranscriptItem({ transcript, tone = "history" }: TranscriptItemProps) {
  const timestamp = formatTime(transcript.ts);
  const isLive = tone === "live";
  const containerClass = isLive
    ? "grid grid-cols-[auto,1fr] items-start gap-x-3 gap-y-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 shadow-[0_0_0_1px_rgba(15,23,42,0.35)]"
    : "grid grid-cols-[auto,1fr] items-start gap-x-2 gap-y-1";
  const metaClass = isLive
    ? "text-[11px] font-semibold uppercase tracking-widest text-emerald-200/80"
    : "text-xs font-medium text-slate-500";
  const timeClass = isLive ? "text-emerald-200/60" : "text-slate-400";
  const textClass = isLive
    ? transcript.isFinal
      ? "text-base font-semibold leading-relaxed text-white"
      : "text-base leading-relaxed text-white/70 italic"
    : transcript.isFinal
      ? "text-sm text-slate-900"
      : "text-sm text-slate-400 italic";
  const translationClass = isLive
    ? "col-start-2 text-base font-medium text-emerald-200"
    : "col-start-2 text-sm text-blue-600";

  return (
    <div className={containerClass}>
      <div className={`flex items-center gap-2 ${metaClass}`}>
        <span className={timeClass}>{timestamp}</span>
      </div>
      <p className={textClass}>{transcript.text}</p>
      {transcript.translations.map((translation, index) => (
        <p key={`${transcript.id}-tr-${index}`} className={translationClass}>
          {translation.translatedText}
        </p>
      ))}
    </div>
  );
}
