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
      className="rounded-3xl border border-white/70 bg-white/90 p-4 shadow-[var(--shadow)] backdrop-blur"
      aria-label="Quick Translate"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Quick Translate
          </div>
          <p className="text-sm text-slate-500">
            Draft in Korean and get instant English phrasing.
          </p>
        </div>
        <button
          onClick={clear}
          disabled={isLoading}
          className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm hover:bg-slate-50 disabled:cursor-not-allowed"
        >
          Clear
        </button>
      </div>

      {outputText && (
        <div className="mt-4 flex items-start justify-between gap-3 rounded-2xl border border-blue-100/60 bg-gradient-to-br from-blue-50 to-white p-4 shadow-sm">
          <p className="text-sm font-medium text-slate-900">{outputText}</p>
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

      <div className="mt-4 flex items-end gap-2">
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
          className="min-h-[70px] flex-1 resize-none rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm focus:outline-none focus:ring focus:ring-blue-200"
          placeholder="Type Korean text..."
          aria-label="Korean text input"
        />
        <button
          onClick={translate}
          disabled={!inputText.trim() || isLoading}
          className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/30 transition hover:bg-[var(--accent-strong)] disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {isLoading ? "Translating..." : "Translate"}
        </button>
      </div>
    </section>
  );
}
