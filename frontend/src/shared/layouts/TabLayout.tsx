import React from "react";

const TabLayout: React.FC<{ title: string; rightSlot?: React.ReactNode }> = ({
  title,
  rightSlot,
  children
}) => (
  <section className="bg-slate-900/60 border border-slate-800 rounded-xl shadow-lg shadow-slate-900/40">
    <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
      <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
      {rightSlot}
    </header>
    <div className="p-6">{children}</div>
  </section>
);

export default TabLayout;
