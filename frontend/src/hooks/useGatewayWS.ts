'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuthStore } from '@/hooks/useAuth';

const GATEWAY_WS_URL = process.env.NEXT_PUBLIC_GATEWAY_WS_URL || 'ws://localhost:8082/ws';

// Message types
export type MessageType =
  | 'subscribe'
  | 'unsubscribe'
  | 'command'
  | 'set_recording'
  | 'robot_status'
  | 'command_response'
  | 'error'
  | 'recording_status';

export interface Position {
  x: number;
  y: number;
  theta: number;
}

export interface RobotStatusData {
  id: string;
  name: string;
  vendor: string;
  model: string;
  state: string;
  battery: number;
  position: Position;
  is_online: boolean;
  last_seen: number;
  current_mission_id?: string;
  sensor_data?: Record<string, number>;
  control_data?: Record<string, number>;
}

export interface WSMessage {
  type: MessageType;
  robot_id?: string;
  robot_ids?: string[];
  command?: string;
  params?: Record<string, unknown>;
  data?: RobotStatusData | unknown;
  success?: boolean;
  error?: string;
  timestamp: number;
  recording?: boolean;
}

interface UseGatewayWSOptions {
  robotIds?: string[];
  onRobotStatus?: (robotId: string, status: RobotStatusData) => void;
  onCommandResponse?: (msg: WSMessage) => void;
  onError?: (error: string) => void;
  onRecordingStatus?: (robotId: string, recording: boolean) => void;
  autoConnect?: boolean;
}

export function useGatewayWS(options: UseGatewayWSOptions = {}) {
  const {
    robotIds,
    onRobotStatus,
    onCommandResponse,
    onError,
    onRecordingStatus,
    autoConnect = true,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [robotStatuses, setRobotStatuses] = useState<Record<string, RobotStatusData>>({});
  const [recordingState, setRecordingState] = useState<Record<string, boolean>>({});

  // Get auth token
  const token = useAuthStore((state) => state.token);

  const connect = useCallback(() => {
    if (!token) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const url = `${GATEWAY_WS_URL}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);

      // Subscribe to robots if specified
      if (robotIds && robotIds.length > 0) {
        ws.send(
          JSON.stringify({
            type: 'subscribe',
            robot_ids: robotIds,
            timestamp: Date.now(),
          })
        );
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);

        switch (msg.type) {
          case 'robot_status': {
            const status = msg.data as RobotStatusData;
            if (status && msg.robot_id) {
              setRobotStatuses((prev) => ({
                ...prev,
                [msg.robot_id!]: status,
              }));
              onRobotStatus?.(msg.robot_id, status);
            }
            break;
          }
          case 'command_response':
            onCommandResponse?.(msg);
            break;
          case 'error':
            onError?.(msg.error || 'Unknown error');
            break;
          case 'recording_status':
            if (msg.robot_id) {
              setRecordingState((prev) => ({
                ...prev,
                [msg.robot_id!]: msg.recording ?? false,
              }));
              onRecordingStatus?.(msg.robot_id, msg.recording ?? false);
            }
            break;
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Auto-reconnect after 3 seconds
      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.('WebSocket connection error');
    };

    wsRef.current = ws;
  }, [token, robotIds, onRobotStatus, onCommandResponse, onError, onRecordingStatus]);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Send robot command directly to Gateway
  const sendCommand = useCallback(
    (robotId: string, command: string, params?: Record<string, unknown>) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        onError?.('WebSocket not connected');
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: 'command',
          robot_id: robotId,
          command,
          params: params || {},
          timestamp: Date.now(),
        })
      );
    },
    [onError]
  );

  // Toggle data recording ON/OFF
  const setRecording = useCallback(
    (robotId: string, recording: boolean) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        onError?.('WebSocket not connected');
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: 'set_recording',
          robot_id: robotId,
          recording,
          timestamp: Date.now(),
        })
      );
    },
    [onError]
  );

  // Subscribe/unsubscribe to robots
  const subscribe = useCallback((ids: string[]) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(
      JSON.stringify({
        type: 'subscribe',
        robot_ids: ids,
        timestamp: Date.now(),
      })
    );
  }, []);

  const unsubscribe = useCallback((ids: string[]) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(
      JSON.stringify({
        type: 'unsubscribe',
        robot_ids: ids,
        timestamp: Date.now(),
      })
    );
  }, []);

  // Auto-connect
  useEffect(() => {
    if (autoConnect && token) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [autoConnect, token, connect, disconnect]);

  return {
    isConnected,
    robotStatuses,
    recordingState,
    sendCommand,
    setRecording,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
  };
}
