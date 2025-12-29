import { useState } from "react";

import { MeetingPanel } from "./components/MeetingPanel";
import { QuickTranslate } from "./components/QuickTranslate";
import { SuggestionsPanel } from "./components/SuggestionsPanel";
import { SuggestionsPromptPanel } from "./components/SuggestionsPromptPanel";
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

        <section className="grid flex-1 min-h-0 items-stretch gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] md:gap-6">
          <div className="flex h-full min-h-0 flex-col">
            <MeetingPanel
              isRecording={meeting.isRecording}
              liveTranscripts={meeting.liveTranscripts}
              transcripts={meeting.transcripts}
              orphanTranslations={meeting.orphanTranslations}
              error={meeting.error}
              onReconnect={meeting.reconnect}
              onDismissError={meeting.dismissError}
            />
          </div>
          <div className="flex h-full min-h-0 flex-col gap-4">
            <SuggestionsPromptPanel
              value={suggestionsPrompt}
              onChange={setSuggestionsPrompt}
              onApply={() => meeting.sendSuggestionsPrompt(suggestionsPrompt)}
              isConnected={meeting.isConnected}
            />
            <div className="flex min-h-0 flex-1">
              <SuggestionsPanel suggestions={meeting.suggestions} />
            </div>
          </div>
        </section>

        <QuickTranslate />
      </main>
    </div>
  );
}
