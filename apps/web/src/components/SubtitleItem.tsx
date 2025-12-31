import { useEffect, useState } from "react";

import { SubtitleSegment } from "../types/events";

export interface SubtitleItemProps {
  segment: SubtitleSegment;
  variant?: "current" | "confirmed";
  isLatestConfirmed?: boolean;
}

export function SubtitleItem({
  segment,
  variant = "confirmed",
  isLatestConfirmed,
}: SubtitleItemProps) {
  const isConfirmed = variant === "confirmed";
  const [opacity, setOpacity] = useState(1);

  useEffect(() => {
    if (!isConfirmed) {
      return;
    }
    const FADEOUT_SECONDS = 60;
    const elapsed = Date.now() - segment.startTime;
    const timeout = FADEOUT_SECONDS * 1000 - elapsed;
    if (timeout <= 0) {
      setOpacity(0.4);
      return;
    }
    const timer = window.setTimeout(() => {
      setOpacity(0.4);
    }, timeout);
    return () => window.clearTimeout(timer);
  }, [isConfirmed, segment.startTime]);

  const renderTextWithHighlights = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        const word = part.slice(2, -2);
        return (
          <strong key={i} className="font-bold text-emerald-300">
            {word}
          </strong>
        );
      }
      return part;
    });
  };

  return (
    <div
      data-testid="subtitle-item"
      style={{ opacity: isConfirmed ? opacity : 1 }}
      className={`group rounded-lg px-4 py-3 transition-all duration-300 ${
        isConfirmed
          ? "border border-emerald-400/20 bg-white/10 shadow-sm hover:bg-white/15"
          : "animate-pulse-subtle border-2 border-emerald-400/60 border-dashed bg-gradient-to-r from-emerald-500/10 to-emerald-400/10"
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`mt-1 h-2 w-2 flex-shrink-0 rounded-full ${
            isConfirmed ? "bg-emerald-400/60" : "animate-ping bg-emerald-400"
          }`}
        />
        <div className="flex-1 space-y-1">
          <p
            className={`${
              isConfirmed
                ? "text-sm font-semibold leading-relaxed text-white"
                : "max-h-32 overflow-y-auto text-sm font-medium leading-relaxed text-emerald-100/90 italic"
            }`}
          >
            {segment.text}
            {!isConfirmed && (
              <span className="ml-1 inline-block animate-blink text-emerald-300">
                ▌
              </span>
            )}
          </p>
          {segment.translation && (
            <p className="mt-2 rounded-lg border border-emerald-400/30 bg-emerald-400/15 px-3 py-2 text-sm font-semibold leading-relaxed text-emerald-50 shadow-sm md:text-base">
              {renderTextWithHighlights(segment.translation)}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
