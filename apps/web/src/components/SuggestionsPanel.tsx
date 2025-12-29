import { useState } from "react";

import { SuggestionItem } from "../types/events";

interface SuggestionsPanelProps {
  suggestions: SuggestionItem[];
}

export function SuggestionsPanel({ suggestions }: SuggestionsPanelProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const visibleSuggestions = suggestions.slice(0, 5);

  const handleCopy = async (index: number, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    window.setTimeout(() => setCopiedIndex(null), 1500);
  };

  return (
    <section
      className="flex h-full min-h-0 flex-col rounded-lg border bg-white p-4"
      aria-label="AI Suggestions"
    >
      <div>
        <h2 className="text-lg font-semibold">AI Suggestions</h2>
        <p className="mt-1 text-sm text-slate-500">
          Fresh prompts based on the latest transcript.
        </p>
      </div>

      {visibleSuggestions.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          Suggestions will appear once the conversation gets going.
        </p>
      ) : (
        <ul className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1" role="list">
          {visibleSuggestions.map((item, index) => (
            <li key={`${item.en}-${index}`} className="space-y-1">
              <button
                onClick={() => handleCopy(index, item.en)}
                className="w-full rounded border border-transparent p-2 text-left hover:border-slate-200 hover:bg-slate-50"
                aria-label={`Copy suggestion: ${item.en}`}
              >
                <p className="text-sm font-medium text-slate-900">{item.en}</p>
                <p className="text-xs text-slate-500">{item.ko}</p>
                {copiedIndex === index && (
                  <span className="mt-1 block text-xs text-blue-600">Copied</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
