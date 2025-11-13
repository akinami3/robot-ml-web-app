import React from "react";

const LoadingSpinner: React.FC = () => (
  <div className="inline-flex items-center gap-2 text-slate-300">
    <span className="w-3 h-3 border-2 border-t-transparent border-cyan-400 rounded-full animate-spin" />
    <span className="text-xs uppercase tracking-wide">Loading</span>
  </div>
);

export default LoadingSpinner;
