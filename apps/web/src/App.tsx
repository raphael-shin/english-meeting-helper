import { useEffect, useState } from "react";

import { MeetingPanel } from "./components/MeetingPanel";
import { QuickTranslate } from "./components/QuickTranslate";
import { SuggestionsPanel } from "./components/SuggestionsPanel";
import { TopBar } from "./components/TopBar";
import { useMeeting } from "./hooks/useMeeting";
import { ProviderMode } from "./types/provider";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000";

export default function App() {
  const [providerMode, setProviderMode] = useState<ProviderMode>(() => {
    if (typeof window === "undefined") {
      return "AWS";
    }
    const stored = window.localStorage.getItem("meeting-provider-mode");
    return stored === "OPENAI" ? "OPENAI" : "AWS";
  });
  const meeting = useMeeting(WS_BASE_URL, providerMode);
  const [suggestionsPrompt, setSuggestionsPrompt] = useState("");

  useEffect(() => {
    window.localStorage.setItem("meeting-provider-mode", providerMode);
  }, [providerMode]);

  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden text-[var(--ink)]">
      <div className="pointer-events-none absolute -top-24 right-[-10%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.35),transparent_70%)] blur-2xl" />
      <div className="pointer-events-none absolute bottom-[-18%] left-[-12%] h-[520px] w-[520px] rounded-full bg-[radial-gradient(circle_at_center,rgba(14,165,233,0.3),transparent_70%)] blur-2xl" />
      <main className="relative mx-auto flex w-full max-w-7xl flex-1 min-h-0 flex-col gap-5 p-4 md:p-6">
        <TopBar
          isRecording={meeting.isRecording}
          isConnected={meeting.isConnected}
          onStart={meeting.startMeeting}
          onStop={meeting.stopMeeting}
          providerMode={providerMode}
          onProviderModeChange={setProviderMode}
        />

        <section className="flex-[3] min-h-0">
          <MeetingPanel
            isRecording={meeting.isRecording}
            displayBuffer={meeting.displayBuffer}
            transcripts={meeting.transcripts}
            orphanTranslations={meeting.orphanTranslations}
            error={meeting.error}
            onReconnect={meeting.reconnect}
            onDismissError={meeting.dismissError}
          />
        </section>

        <section className="grid flex-[1] min-h-0 gap-4 md:grid-cols-2 md:items-stretch">
          <QuickTranslate />
          <SuggestionsPanel
            suggestions={meeting.suggestions}
            promptValue={suggestionsPrompt}
            onPromptChange={setSuggestionsPrompt}
            onPromptApply={() => meeting.sendSuggestionsPrompt(suggestionsPrompt)}
            isConnected={meeting.isConnected}
          />
        </section>
      </main>
    </div>
  );
}
