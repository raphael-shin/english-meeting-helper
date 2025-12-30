import { render, screen } from "@testing-library/react";
import { act } from "react";
import { vi } from "vitest";

import { SubtitleItem } from "./SubtitleItem";
import { SubtitleSegment } from "../types/events";

const baseSegment: SubtitleSegment = {
  id: "seg_1",
  text: "Sample line",
  speaker: "spk_1",
  startTime: 1,
  endTime: 2,
  isFinal: true,
  llmCorrected: false,
  segmentId: 1,
};

test("does not render cursor for confirmed subtitles", () => {
  render(<SubtitleItem segment={baseSegment} variant="confirmed" />);
  expect(screen.getByText("Sample line")).toBeInTheDocument();
  expect(screen.queryByText("▌")).not.toBeInTheDocument();
});

test("renders cursor for current subtitles", () => {
  render(
    <SubtitleItem
      segment={{ ...baseSegment, text: "In progress", endTime: null, isFinal: false }}
      variant="current"
    />
  );
  expect(screen.getByText("In progress")).toBeInTheDocument();
  expect(screen.getByText("▌")).toBeInTheDocument();
});

test("fades confirmed subtitles after the timeout", () => {
  vi.useFakeTimers();
  vi.setSystemTime(0);

  render(<SubtitleItem segment={baseSegment} variant="confirmed" />);
  const wrapper = screen.getByTestId("subtitle-item");
  expect(wrapper).toHaveStyle({ opacity: 1 });

  act(() => {
    vi.advanceTimersByTime(30000);
  });

  act(() => {
    vi.runOnlyPendingTimers();
  });

  expect(wrapper).toHaveStyle({ opacity: 0.4 });

  vi.useRealTimers();
});
