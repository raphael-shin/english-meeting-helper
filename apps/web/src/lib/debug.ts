const LOG_BUFFER_SIZE = 200;

type LogEntry = {
  ts: number;
  event: string;
  data?: Record<string, unknown>;
};

const isDebugEnabled = (): boolean => {
  if (typeof window === "undefined") {
    return false;
  }
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get("debug") === "1") {
      return true;
    }
    return window.localStorage.getItem("EMH_DEBUG") === "true";
  } catch {
    return false;
  }
};

const pushLog = (entry: LogEntry) => {
  if (typeof window === "undefined") {
    return;
  }
  const store = (window as typeof window & { __EMH_LOGS__?: LogEntry[] });
  const buffer = store.__EMH_LOGS__ ?? [];
  buffer.push(entry);
  if (buffer.length > LOG_BUFFER_SIZE) {
    buffer.splice(0, buffer.length - LOG_BUFFER_SIZE);
  }
  store.__EMH_LOGS__ = buffer;
};

export const logDebug = (
  event: string,
  data?: Record<string, unknown>,
  options?: { sampleRate?: number; level?: "debug" | "info" | "warn" | "error" }
) => {
  const level = options?.level ?? "debug";
  const sampleRate = options?.sampleRate ?? 1;
  if (sampleRate < 1 && Math.random() > sampleRate) {
    return;
  }
  const debugEnabled = isDebugEnabled();
  const entry = { ts: Date.now(), event, data };
  pushLog(entry);
  if (typeof console !== "undefined" && typeof console[level] === "function") {
    console[level]("[EMH]", event, data ?? {});
  }
  if (!debugEnabled) {
    return;
  }
};
