import React from "react";

import TabLayout from "../../../shared/layouts/TabLayout";
import { log } from "../../../shared/utils/logger";
import { useRobotControlStore } from "../model/robotStore";
import type { VelocityCommand } from "../types";

const RobotControlPanel: React.FC = () => {
  const { command, setCommand } = useRobotControlStore();

  const updateField = <K extends keyof VelocityCommand>(key: K, value: VelocityCommand[K]) => {
    setCommand({ ...command, [key]: value });
  };

  const handleSend = () => {
    // TODO: integrate with backend transport (WebSocket)
    log("send velocity", command);
  };

  return (
    <TabLayout
      title="ロボット手動制御"
      rightSlot={
        <button
          className="px-3 py-2 bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 rounded-md"
          onClick={handleSend}
        >
          Send Command
        </button>
      }
    >
      <div className="grid grid-cols-3 gap-4">
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-400">Robot ID</span>
          <input
            className="bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-slate-100"
            value={command.robotId}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              updateField("robotId", event.target.value)
            }
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-400">Linear Velocity (m/s)</span>
          <input
            type="number"
            className="bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-slate-100"
            value={command.linear}
            step="0.1"
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              updateField("linear", Number(event.target.value))
            }
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-400">Angular Velocity (rad/s)</span>
          <input
            type="number"
            className="bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-slate-100"
            value={command.angular}
            step="0.1"
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              updateField("angular", Number(event.target.value))
            }
          />
        </label>
      </div>
    </TabLayout>
  );
};

export default RobotControlPanel;
