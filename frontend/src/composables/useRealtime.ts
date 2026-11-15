import { ref } from 'vue';

/**
 * Singleton real-time connection to the backend WebSocket hub.
 *
 * - auto-connects once authenticated and reconnects with backoff
 * - `on(type, handler)` subscribes to server events, e.g.
 *   `on('message', ...)`, `on('notification', ...)`, `on('signal', ...)`
 * - `join(room)` / `signal(...)` power the consultation rooms
 */
type Handler = (payload: Record<string, unknown>) => void;

const connected = ref(false);
const handlers = new Map<string, Set<Handler>>();
let socket: WebSocket | null = null;
let retries = 0;
let reconnectTimer: number | undefined;

function wsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}/ws/realtime`;
}

function emit(type: string, payload: Record<string, unknown>) {
  handlers.get(type)?.forEach((handler) => handler(payload));
  handlers.get('*')?.forEach((handler) => handler({ ...payload, __type: type }));
}

function connect() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return;
  try {
    socket = new WebSocket(wsUrl());
  } catch {
    scheduleReconnect();
    return;
  }
  socket.onopen = () => {
    connected.value = true;
    retries = 0;
  };
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as Record<string, unknown>;
      if (typeof data.type === 'string') emit(data.type, data);
    } catch {
      // ignore malformed frames
    }
  };
  socket.onclose = () => {
    connected.value = false;
    socket = null;
    scheduleReconnect();
  };
  socket.onerror = () => socket?.close();
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  const delay = Math.min(15000, 1000 * 2 ** Math.min(retries, 4));
  retries += 1;
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = undefined;
    connect();
  }, delay);
}

function send(payload: Record<string, unknown>) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload));
  }
}

export function useRealtime() {
  return {
    connected,
    connect,
    on(type: string, handler: Handler) {
      if (!handlers.has(type)) handlers.set(type, new Set());
      handlers.get(type)!.add(handler);
      return () => handlers.get(type)?.delete(handler);
    },
    join(room: string) {
      send({ type: 'join', room });
    },
    leave(room: string) {
      send({ type: 'leave', room });
    },
    signal(room: string, to: string, data: unknown) {
      send({ type: 'signal', room, to, data });
    },
  };
}
