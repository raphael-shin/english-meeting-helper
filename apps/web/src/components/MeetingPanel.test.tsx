import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { MeetingPanel } from "./MeetingPanel";
import { SubtitleSegment } from "../types/events";

const baseProps = {
  isRecording: false,
  isPaused: false,
  displayBuffer: { confirmed: [], current: null },
  transcripts: [],
  orphanTranslations: [],
  summary: null,
  summaryStatus: "idle" as const,
  summaryError: null,
  error: null,
  onReconnect: () => {},
  onDismissError: () => {},
  onSummaryRequest: () => {},
};

test("shows empty state when not recording", () => {
  render(<MeetingPanel {...baseProps} />);
  expect(screen.getByText(/Press Start to begin capturing captions/i)).toBeInTheDocument();
});

test("shows listening state when recording", () => {
  render(<MeetingPanel {...baseProps} isRecording />);
  expect(screen.getByText(/Listening for speech/i)).toBeInTheDocument();
});

test("renders confirmed and current subtitles", () => {
  const confirmed: SubtitleSegment[] = [
    {
      id: "seg_1",
      text: "Confirmed one.",
      speaker: "spk_1",
      startTime: 1,
      endTime: 2,
      isFinal: true,
      llmCorrected: false,
      segmentId: 1,
    },
    {
      id: "seg_2",
      text: "Confirmed two.",
      speaker: "spk_1",
      startTime: 3,
      endTime: 4,
      isFinal: true,
      llmCorrected: false,
      segmentId: 2,
    },
  ];
  const current: SubtitleSegment = {
    id: "seg_3",
    text: "Current line",
    speaker: "spk_1",
    startTime: 5,
    endTime: null,
    isFinal: false,
    llmCorrected: false,
    segmentId: 3,
  };

  render(
    <MeetingPanel
      {...baseProps}
      isRecording
      displayBuffer={{ confirmed, current }}
    />
  );

  expect(screen.getByText("Confirmed one.")).toBeInTheDocument();
  expect(screen.getByText("Confirmed two.")).toBeInTheDocument();
  expect(screen.getByText("Current line")).toBeInTheDocument();
  expect(screen.getByText(/Composing/i)).toBeInTheDocument();
  expect(screen.getAllByText("▌")).toHaveLength(1);
});

test("summary button triggers request in history tab", () => {
  const onSummaryRequest = vi.fn();
  render(
    <MeetingPanel
      {...baseProps}
      transcripts={[
        {
          id: "final-1",
          kind: "transcript",
          speaker: "spk_1",
          text: "Hello",
          isFinal: true,
          ts: 1,
          segmentId: 1,
          translations: [],
        },
      ]}
      onSummaryRequest={onSummaryRequest}
    />
  );

  fireEvent.click(screen.getByRole("tab", { name: "History" }));
  fireEvent.click(screen.getByRole("button", { name: /Generate meeting summary/i }));
  expect(onSummaryRequest).toHaveBeenCalledTimes(1);
});

test("renders summary card when ready", () => {
  render(
    <MeetingPanel
      {...baseProps}
      transcripts={[
        {
          id: "final-1",
          kind: "transcript",
          speaker: "spk_1",
          text: "Hello",
          isFinal: true,
          ts: 1,
          segmentId: 1,
          translations: [],
        },
      ]}
      summary={{
        markdown: "## 5줄 요약\n- 요약 1\n- 요약 2\n- 요약 3\n- 요약 4\n- 요약 5\n\n## 핵심 내용\n- 핵심 1\n- 핵심 2\n\n## Action Items\n- 액션 1",
      }}
      summaryStatus="ready"
    />
  );

  fireEvent.click(screen.getByRole("tab", { name: "History" }));
  expect(screen.getByText("Meeting Summary")).toBeInTheDocument();
  expect(screen.getByText("요약 1")).toBeInTheDocument();
  expect(screen.getByText("핵심 1")).toBeInTheDocument();
  expect(screen.getByText("액션 1")).toBeInTheDocument();
});
