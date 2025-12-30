import { OrphanTranslationEntry } from "../hooks/useMeeting";
import { formatTime } from "../lib/time";

interface TranslationItemProps {
  translation: OrphanTranslationEntry;
  viewMode?: "both" | "ko" | "en";
}

export function TranslationItem({
  translation,
  viewMode = "both",
}: TranslationItemProps) {
  const timestamp = formatTime(translation.sourceTs || translation.ts);
  const showEnglish = viewMode !== "ko";
  const showKorean = viewMode !== "en";

  return (
    <div className="grid grid-cols-[auto,1fr] items-start gap-x-2 gap-y-1">
      <div className="flex min-w-[52px] items-center gap-2 text-xs font-medium text-slate-500">
        <span className="text-slate-400">{timestamp}</span>
      </div>
      {showEnglish && (
        <p className="text-sm text-slate-600">{translation.sourceText}</p>
      )}
      {showKorean && (
        <p className="rounded-md border border-emerald-200/60 bg-emerald-50/70 px-3 py-2 text-sm font-semibold leading-relaxed text-emerald-950 md:text-base">
          {translation.translatedText}
        </p>
      )}
    </div>
  );
}
