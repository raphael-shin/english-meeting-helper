import { useState } from "react";

import { useTranslate } from "../hooks/useTranslate";

export function QuickTranslate() {
  const {
    inputText,
    outputText,
    isLoading,
    error,
    setInputText,
    translate,
    copyToClipboard,
    clear,
  } = useTranslate();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const success = await copyToClipboard();
    if (success) {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <section
      className="rounded-2xl border bg-white/95 p-3 shadow-lg backdrop-blur"
      aria-label="Quick Translate"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          <span>Quick Translate</span>
          <span className="text-[11px] font-normal normal-case text-slate-400">
            Draft in Korean → English
          </span>
        </div>
        <button
          onClick={clear}
          disabled={isLoading}
          className="rounded-full border px-3 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed"
        >
          Clear
        </button>
      </div>

      {outputText && (
        <div className="mt-3 flex items-start justify-between gap-3 rounded-xl border bg-slate-50 p-3">
          <p className="text-sm text-slate-900">{outputText}</p>
          <button
            onClick={handleCopy}
            className="shrink-0 text-xs font-semibold text-blue-600 hover:underline"
            aria-label="Copy translation to clipboard"
          >
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      )}

      {error && (
        <p id="translate-error" className="mt-2 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      <div className="mt-3 flex items-end gap-2">
        <textarea
          value={inputText}
          onChange={(event) => setInputText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              translate();
            }
          }}
          disabled={isLoading}
          rows={2}
          className="min-h-[56px] flex-1 resize-none rounded-2xl border px-4 py-3 text-sm shadow-sm focus:outline-none focus:ring focus:ring-blue-200"
          placeholder="Type Korean text..."
          aria-label="Korean text input"
        />
        <button
          onClick={translate}
          disabled={!inputText.trim() || isLoading}
          className="rounded-full bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {isLoading ? "Translating..." : "Translate"}
        </button>
      </div>
    </section>
  );
}
