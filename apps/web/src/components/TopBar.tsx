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
    <header className="flex items-center justify-between rounded-full border bg-white px-4 py-2 shadow-sm">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-slate-100" aria-hidden />
          <span className="text-base font-semibold">Notes</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {isRecording && (
          <div className="flex items-center gap-2 rounded-full bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                isConnected ? "bg-emerald-500" : "bg-amber-500"
              } animate-pulse`}
              aria-hidden
            />
            <span className="sr-only">
              {isConnected ? "Transcribing" : "Reconnecting"}
            </span>
            <span className="hidden sm:inline">
              {isConnected ? "Transcript" : "Reconnecting..."}
            </span>
            <div
              className={`mic-meter ${isConnected ? "" : "mic-meter--idle"}`}
              aria-hidden
            >
              {micBars}
            </div>
          </div>
        )}
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
