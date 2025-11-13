import { create } from "zustand";

import { VelocityCommand } from "../shared/types/robot";

interface RobotState {
  velocity: VelocityCommand;
  setVelocity: (command: VelocityCommand) => void;
}

export const useRobotStore = create<RobotState>((set) => ({
  velocity: { robotId: "robot-1", linear: 0, angular: 0 },
  setVelocity: (command: VelocityCommand) => set({ velocity: command })
}));
