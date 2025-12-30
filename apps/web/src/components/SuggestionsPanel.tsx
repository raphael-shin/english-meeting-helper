import { useState } from "react";

import { SuggestionItem } from "../types/events";
import settingsIcon from "../assets/settings-btn.png";

interface SuggestionsPanelProps {
  suggestions: SuggestionItem[];
  promptValue: string;
  onPromptChange: (value: string) => void;
  onPromptApply: () => void;
  isConnected: boolean;
}

export function SuggestionsPanel({
  suggestions,
  promptValue,
  onPromptChange,
  onPromptApply,
  isConnected,
}: SuggestionsPanelProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const visibleSuggestions = suggestions.slice(0, 10);

  const handleCopy = async (index: number, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    window.setTimeout(() => setCopiedIndex(null), 1500);
  };

  return (
    <section
      className="flex h-full min-h-0 flex-col rounded-3xl border border-white/70 bg-white/90 p-4 shadow-[var(--shadow)] backdrop-blur"
      aria-label="AI Suggestions"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">AI Suggestions</h2>
        <button
          type="button"
          onClick={() => setShowSettings((current) => !current)}
          className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm hover:bg-slate-50"
          aria-expanded={showSettings}
          aria-controls="ai-suggestions-settings"
          aria-label={showSettings ? "Close settings" : "Open settings"}
        >
          <img src={settingsIcon} alt="" className="h-4 w-4" />
        </button>
      </div>

      {showSettings && (
        <div
          id="ai-suggestions-settings"
          className="mt-4 rounded-2xl border border-slate-100 bg-slate-50/70 p-4"
        >
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-slate-700">Suggestions prompt</p>
            <span className="text-xs text-slate-400">
              {isConnected ? "Active" : "Pending"}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Add meeting goals or constraints to guide the suggestions.
          </p>
          <div className="mt-3 space-y-2">
            <textarea
              value={promptValue}
              onChange={(event) => onPromptChange(event.target.value)}
              rows={3}
              className="w-full resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
              placeholder="e.g. 목표: 신규 기능 출시 일정 확정. 반드시 전달할 정보: 리스크와 리소스 상황."
              aria-label="Suggestions system prompt"
            />
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs text-slate-400">
                {isConnected
                  ? "Apply to upcoming suggestions."
                  : "Will apply when connected."}
              </span>
              <button
                onClick={onPromptApply}
                className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-slate-800"
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      )}

      {visibleSuggestions.length > 0 && (
        <ul className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1" role="list">
          {visibleSuggestions.map((item, index) => (
            <li key={`${item.en}-${index}`} className="space-y-1">
              <button
                onClick={() => handleCopy(index, item.en)}
                className={`w-full rounded-2xl border p-3 text-left transition ${
                  index === 0
                    ? "border-slate-900 bg-slate-900 text-white shadow-lg shadow-slate-900/20"
                    : "border-transparent bg-white hover:border-slate-200 hover:bg-slate-50"
                }`}
                aria-label={`Copy suggestion: ${item.en}`}
              >
                <p
                  className={`text-xs font-semibold ${
                    index === 0 ? "text-white" : "text-slate-900"
                  }`}
                >
                  {item.en}
                </p>
                <p
                  className={`text-[11px] ${
                    index === 0 ? "text-slate-200" : "text-slate-500"
                  }`}
                >
                  {item.ko}
                </p>
                {copiedIndex === index && (
                  <span
                    className={`mt-1 block text-xs ${
                      index === 0 ? "text-blue-200" : "text-blue-600"
                    }`}
                  >
                    Copied
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
