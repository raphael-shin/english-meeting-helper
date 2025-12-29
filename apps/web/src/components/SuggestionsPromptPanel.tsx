interface SuggestionsPromptPanelProps {
  value: string;
  onChange: (value: string) => void;
  onApply: () => void;
  isConnected: boolean;
}

export function SuggestionsPromptPanel({
  value,
  onChange,
  onApply,
  isConnected,
}: SuggestionsPromptPanelProps) {
  return (
    <section className="rounded-lg border bg-white p-4" aria-label="Suggestions Prompt">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Suggestions Prompt</h2>
        <span className="text-xs text-slate-400">
          {isConnected ? "Active" : "Pending"}
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-500">
        Add meeting goals, key points, or constraints to steer the suggestions.
      </p>
      <div className="mt-3 space-y-2">
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          rows={4}
          className="w-full resize-none rounded border px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
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
            onClick={onApply}
            className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800"
          >
            Apply
          </button>
        </div>
      </div>
    </section>
  );
}
