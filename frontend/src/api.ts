export type AgentStatus = {
  running: boolean;
  goal?: string | null;
  step: number;
  last_action?: string | null;
  last_reasoning?: string | null;
  dry_run: boolean;
};

export type EventEnvelope = {
  type: string;
  ts: number;
  payload: any;
};

export type EventsConnectionState = 'connecting' | 'open' | 'closed';

// Prefer Vite env override; fallback to same-host; then localhost for dev.
const API_BASE =
  (import.meta as any).env?.VITE_API_BASE ??
  `${window.location.protocol}//${window.location.hostname}:8000`;

function wsUrlFromApiBase(): string {
  const override = (import.meta as any).env?.VITE_WS_BASE;
  if (override) return `${override}/api/events`;

  const api = new URL(API_BASE);
  const wsProtocol = api.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${wsProtocol}//${api.host}/api/events`;
}

export async function fetchStatus(): Promise<AgentStatus> {
  const res = await fetch(`${API_BASE}/api/status`);
  return await res.json();
}

export async function runGoal(goal: string): Promise<{ ok: boolean; status: AgentStatus; error?: string }> {
  const res = await fetch(`${API_BASE}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal })
  });
  return await res.json();
}

export async function stopGoal(): Promise<{ ok: boolean; status: AgentStatus }> {
  const res = await fetch(`${API_BASE}/api/stop`, { method: 'POST' });
  return await res.json();
}

export async function fetchSettings(): Promise<{ settings: Record<string, any> }> {
  const res = await fetch(`${API_BASE}/api/settings`);
  return await res.json();
}

export async function updateSettings(settings: Record<string, any>): Promise<{ ok: boolean; settings?: Record<string, any>; error?: string }> {
  const res = await fetch(`${API_BASE}/api/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  });
  return await res.json();
}

export function connectEvents(
  onEvent: (evt: EventEnvelope) => void,
  onState?: (state: EventsConnectionState) => void
): { close: () => void } {
  let ws: WebSocket | null = null;
  let closed = false;
  let attempt = 0;

  const connect = () => {
    if (closed) return;

    onState?.('connecting');
    const url = wsUrlFromApiBase();
    ws = new WebSocket(url);

    ws.onopen = () => {
      attempt = 0;
      onState?.('open');
    };

    ws.onmessage = (msg) => {
      try {
        onEvent(JSON.parse(msg.data));
      } catch {
        // ignore
      }
    };

    ws.onerror = () => {
      // Let onclose handle reconnection.
    };

    ws.onclose = () => {
      onState?.('closed');
      if (closed) return;
      const delayMs = Math.min(5000, 250 * Math.pow(2, attempt));
      attempt = Math.min(attempt + 1, 5);
      window.setTimeout(connect, delayMs);
    };
  };

  connect();

  return {
    close: () => {
      closed = true;
      try {
        ws?.close();
      } catch {
        // ignore
      }
    }
  };
}
