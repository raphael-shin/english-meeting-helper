import { render, screen } from "@testing-library/react";

import { MeetingPanel } from "./MeetingPanel";
import { SubtitleSegment } from "../types/events";

const baseProps = {
  isRecording: false,
  isPaused: false,
  displayBuffer: { confirmed: [], current: null },
  transcripts: [],
  orphanTranslations: [],
  error: null,
  onReconnect: () => {},
  onDismissError: () => {},
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
