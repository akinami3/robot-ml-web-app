import React from "react";

interface ConnectionStatusProps {
  label: string;
  connected: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ label, connected }) => {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span
        className={`w-2.5 h-2.5 rounded-full ${connected ? "bg-emerald-400" : "bg-rose-400"}`}
      />
      <span className="text-slate-300">{label}</span>
      <span className={`text-xs uppercase tracking-wide ${connected ? "text-emerald-300" : "text-rose-300"}`}>
        {connected ? "Connected" : "Disconnected"}
      </span>
    </div>
  );
};

export default ConnectionStatus;
