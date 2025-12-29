import { useState } from "react";

import { MeetingPanel } from "./components/MeetingPanel";
import { QuickTranslate } from "./components/QuickTranslate";
import { SuggestionsPanel } from "./components/SuggestionsPanel";
import { TopBar } from "./components/TopBar";
import { useMeeting } from "./hooks/useMeeting";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000";

export default function App() {
  const meeting = useMeeting(WS_BASE_URL);
  const [suggestionsPrompt, setSuggestionsPrompt] = useState("");

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-gradient-to-b from-slate-50 via-white to-slate-100 text-slate-900">
      <main className="mx-auto flex w-full max-w-7xl flex-1 min-h-0 flex-col gap-4 p-4 md:p-6">
        <TopBar
          isRecording={meeting.isRecording}
          isConnected={meeting.isConnected}
          onStart={meeting.startMeeting}
          onStop={meeting.stopMeeting}
        />

        <section className="flex-[3] min-h-0">
          <MeetingPanel
            isRecording={meeting.isRecording}
            liveTranscripts={meeting.liveTranscripts}
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
