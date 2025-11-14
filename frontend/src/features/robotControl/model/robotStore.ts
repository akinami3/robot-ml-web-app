import { create } from "zustand";

import type { VelocityCommand } from "../types";

type SetState<T> = (partial: T | Partial<T> | ((state: T) => T | Partial<T>)) => void;

interface RobotControlState {
  command: VelocityCommand;
  setCommand: (command: VelocityCommand) => void;
}

const createRobotControlStore = (set: SetState<RobotControlState>): RobotControlState => ({
  command: { robotId: "robot-1", linear: 0, angular: 0 },
  setCommand: (command: VelocityCommand) => set({ command })
});

export const useRobotControlStore = create<RobotControlState>(createRobotControlStore);
