import React from "react";
import { NavLink } from "react-router-dom";

interface TabNavProps {
  tabs: { label: string; path: string }[];
}

const TabNav: React.FC<TabNavProps> = ({ tabs }) => (
  <nav className="flex gap-4 px-8 py-3 bg-slate-900/70 border-b border-slate-800">
    {tabs.map((tab) => (
      <NavLink
        key={tab.path}
        to={tab.path}
        className={({ isActive }) =>
          `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            isActive ? "bg-cyan-500/20 text-cyan-300" : "text-slate-400 hover:text-slate-100"
          }`
        }
      >
        {tab.label}
      </NavLink>
    ))}
  </nav>
);

export default TabNav;
