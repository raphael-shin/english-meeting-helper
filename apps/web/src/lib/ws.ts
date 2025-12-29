import {
  ClientControlMessage,
  SessionStartMessage,
  WebSocketEvent,
} from "../types/events";

export type EventHandler = (event: WebSocketEvent) => void;

export class MeetingWsClient {
  private socket: WebSocket | null = null;
  private pingIntervalId: number | null = null;
  private pongTimeoutId: number | null = null;

  constructor(
    private readonly baseUrl: string,
    private readonly onEvent?: EventHandler,
    private readonly onConnectionChange?: (connected: boolean) => void,
    private readonly onConnectionIssue?: (reason: string) => void
  ) {}

  connect(sessionId: string, startMessage: SessionStartMessage): void {
    this.open(this.buildUrl(sessionId), startMessage);
  }

  reconnect(sessionId: string, startMessage: SessionStartMessage): void {
    this.disconnect();
    this.connect(sessionId, startMessage);
  }

  sendAudio(audioData: ArrayBuffer): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(audioData);
    }
  }

  sendControl(message: ClientControlMessage): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }

  disconnect(): void {
    this.stopKeepAlive();
    this.socket?.close();
    this.socket = null;
  }

  private open(url: string, startMessage: SessionStartMessage): void {
    const socket = new WebSocket(url);
    this.socket = socket;

    socket.onopen = () => {
      this.onConnectionChange?.(true);
      this.sendControl(startMessage);
      this.startKeepAlive();
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketEvent;
        if (data.type === "server.pong") {
          this.handlePong();
          return;
        }
        this.onEvent?.(data);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    socket.onclose = () => {
      this.stopKeepAlive();
      this.socket = null;
      this.onConnectionChange?.(false);
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }

  private startKeepAlive(): void {
    this.stopKeepAlive();
    this.pingIntervalId = window.setInterval(() => {
      this.sendControl({ type: "client.ping", ts: Date.now() });
      this.startPongTimeout();
    }, 15000);
  }

  private startPongTimeout(): void {
    if (this.pongTimeoutId) {
      window.clearTimeout(this.pongTimeoutId);
    }
    this.pongTimeoutId = window.setTimeout(() => {
      this.onConnectionIssue?.("PONG_TIMEOUT");
      this.disconnect();
    }, 30000);
  }

  private handlePong(): void {
    if (this.pongTimeoutId) {
      window.clearTimeout(this.pongTimeoutId);
      this.pongTimeoutId = null;
    }
  }

  private stopKeepAlive(): void {
    if (this.pingIntervalId) {
      window.clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
    }
    if (this.pongTimeoutId) {
      window.clearTimeout(this.pongTimeoutId);
      this.pongTimeoutId = null;
    }
  }

  private buildUrl(sessionId: string): string {
    const trimmed = this.baseUrl.replace(/\/$/, "");
    if (trimmed.startsWith("ws://") || trimmed.startsWith("wss://")) {
      return `${trimmed}/ws/v1/meetings/${sessionId}`;
    }
    const wsBase = trimmed.startsWith("https://")
      ? trimmed.replace("https://", "wss://")
      : trimmed.replace("http://", "ws://");
    return `${wsBase}/ws/v1/meetings/${sessionId}`;
  }
}
