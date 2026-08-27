type MessageHandler = (data: any) => void;
type StatusHandler = (status: 'CONNECTED' | 'CONNECTING' | 'DISCONNECTED') => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: MessageHandler[] = [];
  private statusListeners: StatusHandler[] = [];
  private currentStatus: 'CONNECTED' | 'CONNECTING' | 'DISCONNECTED' = 'DISCONNECTED';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimer: any = null;
  private isExplicitlyClosed = false;

  getStatus(): 'CONNECTED' | 'CONNECTING' | 'DISCONNECTED' {
    return this.currentStatus;
  }

  private setStatus(status: 'CONNECTED' | 'CONNECTING' | 'DISCONNECTED') {
    this.currentStatus = status;
    this.statusListeners.forEach((fn) => fn(status));
  }

  onStatusChange(handler: StatusHandler) {
    this.statusListeners.push(handler);
    handler(this.currentStatus);
    return () => {
      this.statusListeners = this.statusListeners.filter((fn) => fn !== handler);
    };
  }

  connect(customToken?: string) {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.isExplicitlyClosed = false;
    this.setStatus('CONNECTING');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || 'localhost';
    const baseUrl = import.meta.env.VITE_WS_BASE_URL
      ? import.meta.env.VITE_WS_BASE_URL
      : `${protocol}//${host}:8000/ws`;

    const token = customToken || localStorage.getItem('access_token');
    const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : '';
    const wsUrl = `${baseUrl}/tracking${tokenQuery}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.setStatus('CONNECTED');
        console.log('[WebSocket] Connected to Logistics Telemetry Stream');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach((fn) => fn(data));
        } catch (e) {
          console.error('[WebSocket] Message parsing error:', e);
        }
      };

      this.ws.onclose = (event) => {
        this.setStatus('DISCONNECTED');
        this.ws = null;
        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect(customToken);
        }
      };

      this.ws.onerror = (err) => {
        console.warn('[WebSocket] Connection warning/error:', err);
      };
    } catch (e) {
      console.warn('[WebSocket] Init error:', e);
      this.setStatus('DISCONNECTED');
      this.scheduleReconnect(customToken);
    }
  }

  private scheduleReconnect(customToken?: string) {
    if (this.isExplicitlyClosed || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 15000);
    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout(() => {
      this.connect(customToken);
    }, delay);
  }

  subscribe(handler: MessageHandler) {
    this.listeners.push(handler);
    return () => {
      this.listeners = this.listeners.filter((fn) => fn !== handler);
    };
  }

  send(data: object): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  close() {
    this.isExplicitlyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus('DISCONNECTED');
  }
}

export const wsClient = new WebSocketClient();
