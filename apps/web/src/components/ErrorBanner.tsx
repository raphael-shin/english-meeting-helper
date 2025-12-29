import { ErrorEvent } from "../types/events";

interface ErrorBannerProps {
  error: ErrorEvent;
  onDismiss: () => void;
  onRetry?: () => void;
}

export function ErrorBanner({ error, onDismiss, onRetry }: ErrorBannerProps) {
  return (
    <div
      className="flex items-center justify-between gap-3 border-b border-red-200 bg-red-50 px-4 py-3"
      role="alert"
    >
      <div className="flex items-center gap-2 text-sm text-red-800">
        <span aria-hidden>!</span>
        <span>{error.message}</span>
      </div>
      <div className="flex items-center gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-sm font-medium text-red-700 hover:text-red-900"
          >
            Retry
          </button>
        )}
        <button
          onClick={onDismiss}
          className="text-sm text-slate-600 hover:text-slate-800"
          aria-label="Dismiss error"
        >
          Close
        </button>
      </div>
    </div>
  );
}
