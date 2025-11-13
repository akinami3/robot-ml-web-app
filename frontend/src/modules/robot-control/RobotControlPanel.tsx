import React, { useState } from "react";

import TabLayout from "../../shared/layouts/TabLayout";
import { VelocityCommand } from "../../shared/types/robot";
import { log } from "../../shared/utils/logger";

const RobotControlPanel: React.FC = () => {
  const [command, setCommand] = useState<VelocityCommand>({ robotId: "robot-1", linear: 0, angular: 0 });

  const handleSend = () => {
    log("send velocity", command);
    // TODO: integrate with backend
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
            onChange={(event) => setCommand({ ...command, robotId: event.target.value })}
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-400">Linear Velocity (m/s)</span>
          <input
            type="number"
            className="bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-slate-100"
            value={command.linear}
            step="0.1"
            onChange={(event) => setCommand({ ...command, linear: Number(event.target.value) })}
          />
        </label>
        <label className="flex flex-col gap-2">
          <span className="text-sm text-slate-400">Angular Velocity (rad/s)</span>
          <input
            type="number"
            className="bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-slate-100"
            value={command.angular}
            step="0.1"
            onChange={(event) => setCommand({ ...command, angular: Number(event.target.value) })}
          />
        </label>
      </div>
    </TabLayout>
  );
};

export default RobotControlPanel;
