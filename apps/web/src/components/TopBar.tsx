import { MicSettingsPanel } from "./MicSettingsPanel";
import { TranscribeControls } from "./TranscribeControls";
import { ProviderMode } from "../types/provider";

interface TopBarProps {
  isRecording: boolean;
  isConnected: boolean;
  onStart: () => void;
  onStop: () => void;
  providerMode: ProviderMode;
  onProviderModeChange: (mode: ProviderMode) => void;
}

export function TopBar({
  isRecording,
  isConnected,
  onStart,
  onStop,
  providerMode,
  onProviderModeChange,
}: TopBarProps) {
  const statusLabel = isRecording
    ? isConnected
      ? "Live"
      : "Reconnecting"
    : "Ready";
  const statusTone = isRecording
    ? isConnected
      ? "bg-emerald-500"
      : "bg-amber-500"
    : "bg-slate-400";

  const micBars = Array.from({ length: 14 }, (_, index) => (
    <span
      key={`mic-bar-${index}`}
      className="mic-bar"
      style={{
        animationDelay: `${index * 0.08}s`,
        animationDuration: `${1 + (index % 3) * 0.2}s`,
      }}
    />
  ));

  return (
    <header className="flex flex-wrap items-center justify-between gap-4 rounded-[28px] border border-white/60 bg-white/80 px-5 py-3 shadow-[var(--shadow)] backdrop-blur">
      <div className="flex items-center gap-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white shadow-sm">
          <span className="text-base font-semibold">N</span>
        </div>
        <div>
          <span className="block text-lg font-semibold tracking-tight">
            Notes
          </span>
          <span className="block text-xs text-slate-500">
            English Meeting Helper
          </span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 rounded-full bg-slate-900/5 px-3 py-1.5 text-xs font-semibold text-slate-700">
          <span
            className={`h-2.5 w-2.5 rounded-full ${statusTone}`}
            aria-hidden
          />
          <span>{statusLabel}</span>
          {isRecording && (
            <div
              className={`mic-meter ${isConnected ? "" : "mic-meter--idle"}`}
              aria-hidden
            >
              {micBars}
            </div>
          )}
        </div>
        <MicSettingsPanel
          providerMode={providerMode}
          onProviderModeChange={onProviderModeChange}
        />
        <TranscribeControls
          isRecording={isRecording}
          onStart={onStart}
          onStop={onStop}
        />
      </div>
    </header>
  );
}
