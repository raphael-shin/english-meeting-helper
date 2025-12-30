import { OrphanTranslationEntry } from "../hooks/useMeeting";
import { formatTime } from "../lib/time";

interface TranslationItemProps {
  translation: OrphanTranslationEntry;
}

export function TranslationItem({ translation }: TranslationItemProps) {
  const timestamp = formatTime(translation.sourceTs || translation.ts);

  return (
    <div className="grid grid-cols-[auto,1fr] items-start gap-x-2 gap-y-1">
      <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
        <span className="text-slate-400">{timestamp}</span>
      </div>
      <p className="text-sm text-slate-500">{translation.sourceText}</p>
      <p className="text-sm text-blue-600">{translation.translatedText}</p>
    </div>
  );
}
