/**
 * Robot state store using Zustand.
 */

import { create } from "zustand";
import type { Robot, SensorData, VelocityCommand } from "@/types";

interface RobotState {
  robots: Robot[];
  selectedRobotId: string | null;
  latestSensorData: Record<string, Record<string, SensorData>>;
  isEStopActive: boolean;
  lastCommand: VelocityCommand | null;

  setRobots: (robots: Robot[]) => void;
  selectRobot: (id: string | null) => void;
  updateRobotState: (id: string, patch: Partial<Robot>) => void;
  updateSensorData: (robotId: string, data: SensorData) => void;
  setEStop: (active: boolean) => void;
  setLastCommand: (cmd: VelocityCommand | null) => void;

  selectedRobot: () => Robot | undefined;
}

export const useRobotStore = create<RobotState>()((set, get) => ({
  robots: [],
  selectedRobotId: null,
  latestSensorData: {},
  isEStopActive: false,
  lastCommand: null,

  setRobots: (robots) => set({ robots }),

  selectRobot: (id) => set({ selectedRobotId: id }),

  updateRobotState: (id, patch) =>
    set((state) => ({
      robots: state.robots.map((r) =>
        r.id === id ? { ...r, ...patch } : r
      ),
    })),

  updateSensorData: (robotId, data) =>
    set((state) => ({
      latestSensorData: {
        ...state.latestSensorData,
        [robotId]: {
          ...(state.latestSensorData[robotId] || {}),
          [data.sensor_type]: data,
        },
      },
    })),

  setEStop: (active) => set({ isEStopActive: active }),

  setLastCommand: (cmd) => set({ lastCommand: cmd }),

  selectedRobot: () => {
    const state = get();
    return state.robots.find((r) => r.id === state.selectedRobotId);
  },
}));
