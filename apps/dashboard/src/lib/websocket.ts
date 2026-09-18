import { useEffect, useRef, useState } from 'react';

export interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: any) => void;
  reconnectInterval?: number;
}

export function useWebSocket({ url, onMessage, reconnectInterval = 3000 }: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let unmounted = false;

    function connect() {
      if (typeof window === 'undefined') return;

      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const fullUrl = url.startsWith('ws') ? url : `${wsProtocol}//${window.location.hostname}:8000${url}`;

      try {
        const ws = new WebSocket(fullUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!unmounted) {
            setIsConnected(true);
          }
        };

        ws.onmessage = (event) => {
          if (onMessage && !unmounted) {
            try {
              const parsed = JSON.parse(event.data);
              onMessage(parsed);
            } catch (e) {
              onMessage(event.data);
            }
          }
        };

        ws.onclose = () => {
          if (!unmounted) {
            setIsConnected(false);
            reconnectTimerRef.current = setTimeout(connect, reconnectInterval);
          }
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        if (!unmounted) {
          setIsConnected(false);
          reconnectTimerRef.current = setTimeout(connect, reconnectInterval);
        }
      }
    }

    connect();

    return () => {
      unmounted = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url]);

  const send = (data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  };

  return { isConnected, send };
}
