import { act } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { useMeeting } from "./useMeeting";
import { DisplayUpdateEvent } from "../types/events";
import { __getLastWsClient } from "../lib/ws";

const globalCrypto = globalThis.crypto as { randomUUID?: () => string } | undefined;
if (!globalCrypto) {
  (globalThis as { crypto: { randomUUID: () => string } }).crypto = {
    randomUUID: () => "test-uuid",
  };
} else if (!globalCrypto.randomUUID) {
  globalCrypto.randomUUID = () => "test-uuid";
}

vi.mock("../lib/audio", () => ({
  AudioCapture: class {
    start() {
      return Promise.resolve();
    }
    stop() {}
  },
}));

vi.mock("../lib/ws", () => {
  let lastClient: {
    emit?: (event: unknown) => void;
    sendControl?: (message: unknown) => void;
    sentControls?: unknown[];
  } | null = null;

  class MeetingWsClient {
    private onEvent?: (event: unknown) => void;
    private onConnectionChange?: (connected: boolean) => void;
    private sentControls: unknown[] = [];

    constructor(
      _baseUrl: string,
      onEvent?: (event: unknown) => void,
      onConnectionChange?: (connected: boolean) => void
    ) {
      this.onEvent = onEvent;
      this.onConnectionChange = onConnectionChange;
      lastClient = {
        emit: (event) => this.emit(event),
        sendControl: (message) => this.sendControl(message),
        sentControls: this.sentControls,
      };
    }

    connect() {
      this.onConnectionChange?.(true);
    }

    reconnect() {
      this.onConnectionChange?.(true);
    }

    sendAudio() {}

    sendControl(message: unknown) {
      this.sentControls.push(message);
    }

    disconnect() {
      this.onConnectionChange?.(false);
    }

    emit(event: unknown) {
      this.onEvent?.(event);
    }
  }

  return {
    MeetingWsClient,
    __getLastWsClient: () => lastClient,
  };
});

function TestHarness() {
  const meeting = useMeeting("ws://localhost", "AWS");
  return (
    <div>
      <button type="button" onClick={() => meeting.startMeeting()}>
        start
      </button>
      <button type="button" onClick={() => meeting.requestSummary()}>
        summary
      </button>
      <pre data-testid="display">{JSON.stringify(meeting.displayBuffer)}</pre>
      <pre data-testid="transcripts">{JSON.stringify(meeting.transcripts)}</pre>
      <pre data-testid="summary">{JSON.stringify(meeting.summary)}</pre>
      <pre data-testid="summary-status">{meeting.summaryStatus}</pre>
    </div>
  );
}

test("updates display buffer on display.update event", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  const event: DisplayUpdateEvent = {
    type: "display.update",
    ts: Date.now(),
    sessionId: "sess_1",
    confirmed: [
      {
        id: "seg_1",
        text: "Hello.",
        speaker: "spk_1",
        startTime: 1,
        endTime: 2,
        isFinal: true,
        llmCorrected: false,
        segmentId: 1,
      },
    ],
    current: {
      id: "seg_2",
      text: "Working on it",
      speaker: "spk_1",
      startTime: 3,
      endTime: null,
      isFinal: false,
      llmCorrected: false,
      segmentId: 2,
    },
  };

  await act(async () => {
    client?.emit?.(event);
  });

  await waitFor(() => {
    const payload = screen.getByTestId("display").textContent ?? "{}";
    const display = JSON.parse(payload);
    expect(display.confirmed).toHaveLength(1);
    expect(display.confirmed[0].text).toBe("Hello.");
    expect(display.current.text).toBe("Working on it");
  });
});

test("updates transcript text on transcript.corrected event", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  await act(async () => {
    client?.emit?.({
      type: "transcript.final",
      ts: Date.now(),
      sessionId: "sess_1",
      speaker: "spk_1",
      text: "Orig text",
      segmentId: 10,
    });
  });

  await act(async () => {
    client?.emit?.({
      type: "transcript.corrected",
      ts: Date.now(),
      sessionId: "sess_1",
      segmentId: 10,
      originalText: "Orig text",
      correctedText: "Corrected text",
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("transcripts").textContent ?? "[]";
    const transcripts = JSON.parse(payload);
    expect(transcripts).toHaveLength(1);
    expect(transcripts[0].text).toBe("Corrected text");
  });
});

test("updates translation on translation.corrected event", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  await act(async () => {
    client?.emit?.({
      type: "transcript.final",
      ts: 1000,
      sessionId: "sess_1",
      speaker: "spk_1",
      text: "Hello",
      segmentId: 5,
    });
  });

  await act(async () => {
    client?.emit?.({
      type: "translation.final",
      ts: 1000,
      sessionId: "sess_1",
      sourceTs: 1000,
      segmentId: 5,
      speaker: "spk_1",
      sourceText: "Hello",
      translatedText: "안녕",
    });
  });

  await act(async () => {
    client?.emit?.({
      type: "translation.corrected",
      ts: 2000,
      sessionId: "sess_1",
      segmentId: 5,
      speaker: "spk_1",
      sourceText: "Hello world",
      translatedText: "안녕하세요",
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("transcripts").textContent ?? "[]";
    const transcripts = JSON.parse(payload);
    expect(transcripts).toHaveLength(1);
    expect(transcripts[0].translations).toHaveLength(1);
    expect(transcripts[0].translations[0].translatedText).toBe("안녕하세요");
  });
});

test("ignores correction for non-existent segment", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  await act(async () => {
    client?.emit?.({
      type: "transcript.corrected",
      ts: Date.now(),
      sessionId: "sess_1",
      segmentId: 999,
      originalText: "Original",
      correctedText: "Corrected",
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("transcripts").textContent ?? "[]";
    const transcripts = JSON.parse(payload);
    expect(transcripts).toHaveLength(0);
  });
});

test("handles duplicate corrections for same segment", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  await act(async () => {
    client?.emit?.({
      type: "transcript.final",
      ts: Date.now(),
      sessionId: "sess_1",
      speaker: "spk_1",
      text: "Original",
      segmentId: 7,
    });
  });

  await act(async () => {
    client?.emit?.({
      type: "transcript.corrected",
      ts: Date.now(),
      sessionId: "sess_1",
      segmentId: 7,
      originalText: "Original",
      correctedText: "First correction",
    });
  });

  await act(async () => {
    client?.emit?.({
      type: "transcript.corrected",
      ts: Date.now(),
      sessionId: "sess_1",
      segmentId: 7,
      originalText: "First correction",
      correctedText: "Second correction",
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("transcripts").textContent ?? "[]";
    const transcripts = JSON.parse(payload);
    expect(transcripts).toHaveLength(1);
    expect(transcripts[0].text).toBe("Second correction");
  });
});

test("progressively updates current with same segmentId", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  // First partial
  await act(async () => {
    client?.emit?.({
      type: "display.update",
      ts: Date.now(),
      sessionId: "sess_1",
      confirmed: [],
      current: {
        id: "seg_1",
        text: "Smart",
        speaker: "spk_1",
        startTime: 1000,
        endTime: null,
        isFinal: false,
        llmCorrected: false,
        segmentId: 1,
      },
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("display").textContent ?? "{}";
    const display = JSON.parse(payload);
    expect(display.current.segmentId).toBe(1);
    expect(display.current.text).toBe("Smart");
  });

  // Progressive update with same segmentId
  await act(async () => {
    client?.emit?.({
      type: "display.update",
      ts: Date.now(),
      sessionId: "sess_1",
      confirmed: [],
      current: {
        id: "seg_1",
        text: "Smart founders",
        speaker: "spk_1",
        startTime: 1000,
        endTime: null,
        isFinal: false,
        llmCorrected: false,
        segmentId: 1,
      },
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("display").textContent ?? "{}";
    const display = JSON.parse(payload);
    expect(display.current.segmentId).toBe(1);
    expect(display.current.text).toBe("Smart founders");
  });
});

test("moves current to confirmed on final", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  // Current exists
  await act(async () => {
    client?.emit?.({
      type: "display.update",
      ts: Date.now(),
      sessionId: "sess_1",
      confirmed: [],
      current: {
        id: "seg_1",
        text: "Smart founders",
        speaker: "spk_1",
        startTime: 1000,
        endTime: null,
        isFinal: false,
        llmCorrected: false,
        segmentId: 1,
      },
    });
  });

  // Final: current becomes confirmed
  await act(async () => {
    client?.emit?.({
      type: "display.update",
      ts: Date.now(),
      sessionId: "sess_1",
      confirmed: [
        {
          id: "seg_1",
          text: "Smart founders apply to YC.",
          speaker: "spk_1",
          startTime: 1000,
          endTime: 2000,
          isFinal: true,
          llmCorrected: false,
          segmentId: 1,
        },
      ],
      current: null,
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("display").textContent ?? "{}";
    const display = JSON.parse(payload);
    expect(display.confirmed).toHaveLength(1);
    expect(display.confirmed[0].text).toBe("Smart founders apply to YC.");
    expect(display.current).toBeNull();
  });
});

test("handles summary.update event", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  await act(async () => {
    client?.emit?.({
      type: "summary.update",
      ts: Date.now(),
      sessionId: "sess_1",
      summaryMarkdown: "## 5줄 요약\n- 요약 1\n- 요약 2\n- 요약 3\n- 요약 4\n- 요약 5\n\n## 핵심 내용\n- 핵심 1",
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("summary").textContent ?? "{}";
    const summary = JSON.parse(payload);
    expect(summary.markdown).toContain("## 5줄 요약");
    expect(screen.getByTestId("summary-status").textContent).toBe("ready");
  });
});

test("requests summary over websocket", async () => {
  render(<TestHarness />);
  const startButton = screen.getByRole("button", { name: "start" });
  const summaryButton = screen.getByRole("button", { name: "summary" });

  await act(async () => {
    fireEvent.click(startButton);
  });

  await act(async () => {
    fireEvent.click(summaryButton);
  });

  const client = __getLastWsClient();
  expect(client?.sentControls).toContainEqual({ type: "summary.request" });
  expect(screen.getByTestId("summary-status").textContent).toBe("loading");
});

test("maintains max 4 confirmed subtitles (FIFO)", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  // Add 5 confirmed subtitles
  await act(async () => {
    client?.emit?.({
      type: "display.update",
      ts: Date.now(),
      sessionId: "sess_1",
      confirmed: [
        { id: "seg_1", text: "First", speaker: "spk_1", startTime: 1000, endTime: 2000, isFinal: true, llmCorrected: false, segmentId: 1 },
        { id: "seg_2", text: "Second", speaker: "spk_1", startTime: 2000, endTime: 3000, isFinal: true, llmCorrected: false, segmentId: 2 },
        { id: "seg_3", text: "Third", speaker: "spk_1", startTime: 3000, endTime: 4000, isFinal: true, llmCorrected: false, segmentId: 3 },
        { id: "seg_4", text: "Fourth", speaker: "spk_1", startTime: 4000, endTime: 5000, isFinal: true, llmCorrected: false, segmentId: 4 },
      ],
      current: null,
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("display").textContent ?? "{}";
    const display = JSON.parse(payload);
    expect(display.confirmed).toHaveLength(4);
    expect(display.confirmed[0].text).toBe("First");
    expect(display.confirmed[3].text).toBe("Fourth");
  });
});

test("progressive translation update for partial (Composing) text", async () => {
  render(<TestHarness />);
  const button = screen.getByRole("button", { name: "start" });

  await act(async () => {
    fireEvent.click(button);
  });

  const client = __getLastWsClient();
  expect(client).not.toBeNull();

  // First display.update with English only (no translation yet)
  await act(async () => {
    client?.emit?.({
      type: "display.update",
      ts: Date.now(),
      sessionId: "sess_1",
      confirmed: [],
      current: {
        id: "seg_1",
        text: "Hello world",
        speaker: "spk_1",
        startTime: Date.now(),
        endTime: null,
        isFinal: false,
        llmCorrected: false,
        segmentId: 1,
        translation: null,
      },
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("display").textContent ?? "{}";
    const display = JSON.parse(payload);
    expect(display.current).not.toBeNull();
    expect(display.current.text).toBe("Hello world");
    expect(display.current.translation).toBeNull();
  });

  // Second display.update with translation added (async translation completed)
  await act(async () => {
    client?.emit?.({
      type: "display.update",
      ts: Date.now(),
      sessionId: "sess_1",
      confirmed: [],
      current: {
        id: "seg_1",
        text: "Hello world",
        speaker: "spk_1",
        startTime: Date.now(),
        endTime: null,
        isFinal: false,
        llmCorrected: false,
        segmentId: 1,
        translation: "안녕하세요",
      },
    });
  });

  await waitFor(() => {
    const payload = screen.getByTestId("display").textContent ?? "{}";
    const display = JSON.parse(payload);
    expect(display.current).not.toBeNull();
    expect(display.current.text).toBe("Hello world");
    expect(display.current.translation).toBe("안녕하세요");
  });
});
