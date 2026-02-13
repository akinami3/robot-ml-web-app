/**
 * WebSocket hook for real-time robot communication via Gateway.
 * Supports MessagePack and JSON encoding with auto-reconnect.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useRobotStore } from "@/stores/robotStore";
import type { Robot, SensorData, WSMessage } from "@/types";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8080/ws";
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;
const PING_INTERVAL = 30000;

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectCount, setReconnectCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval>>();
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const accessToken = useAuthStore((s) => s.accessToken);
  const updateSensorData = useRobotStore((s) => s.updateSensorData);
  const updateRobotState = useRobotStore((s) => s.updateRobotState);
  const setEStop = useRobotStore((s) => s.setEStop);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setReconnectCount(0);

      // Authenticate
      if (accessToken) {
        send({ type: "auth", payload: { token: accessToken } });
      }

      // Start ping
      pingIntervalRef.current = setInterval(() => {
        send({ type: "ping", payload: {} });
      }, PING_INTERVAL);
    };

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        handleMessage(msg);
      } catch {
        // Try msgpack decode fallback if needed
        console.warn("Failed to parse WebSocket message");
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      clearInterval(pingIntervalRef.current);

      // Auto-reconnect
      if (reconnectCount < MAX_RECONNECT_ATTEMPTS) {
        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectCount((c) => c + 1);
          connect();
        }, RECONNECT_DELAY);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [accessToken, reconnectCount]);

  const handleMessage = useCallback(
    (msg: WSMessage) => {
      switch (msg.type) {
        case "sensor_data": {
          const data = msg.payload as unknown as SensorData;
          if (msg.robot_id) {
            updateSensorData(msg.robot_id, data);
          }
          break;
        }
        case "robot_status": {
          if (msg.robot_id) {
            updateRobotState(msg.robot_id, msg.payload as Partial<Robot>);
          }
          break;
        }
        case "estop_response": {
          setEStop(!!msg.payload.active);
          break;
        }
        case "error": {
          console.error("WebSocket error:", msg.payload);
          break;
        }
        default:
          break;
      }
    },
    [updateSensorData, updateRobotState, setEStop]
  );

  const send = useCallback((msg: WSMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const disconnect = useCallback(() => {
    clearInterval(pingIntervalRef.current);
    clearTimeout(reconnectTimeoutRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  // Send velocity command
  const sendVelocity = useCallback(
    (robotId: string, linear_x: number, linear_y: number, angular_z: number) => {
      send({
        type: "velocity_cmd",
        robot_id: robotId,
        payload: { linear_x, linear_y, angular_z },
      });
    },
    [send]
  );

  // Send E-Stop
  const sendEStop = useCallback(
    (robotId?: string) => {
      send({
        type: "estop",
        robot_id: robotId,
        payload: { activate: true },
      });
    },
    [send]
  );

  // Release E-Stop
  const releaseEStop = useCallback(
    (robotId?: string) => {
      send({
        type: "estop",
        robot_id: robotId,
        payload: { activate: false },
      });
    },
    [send]
  );

  // Send navigation goal
  const sendNavGoal = useCallback(
    (robotId: string, x: number, y: number, theta: number) => {
      send({
        type: "nav_goal",
        robot_id: robotId,
        payload: { x, y, theta },
      });
    },
    [send]
  );

  // Lifecycle
  useEffect(() => {
    if (accessToken) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [accessToken]);

  return {
    isConnected,
    reconnectCount,
    send,
    sendVelocity,
    sendEStop,
    releaseEStop,
    sendNavGoal,
    connect,
    disconnect,
  };
}
