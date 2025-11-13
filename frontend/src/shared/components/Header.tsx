import React from "react";

interface HeaderProps {
  title: string;
  subtitle?: string;
}

const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  return (
    <header className="px-8 py-6 border-b border-slate-700 bg-slate-900/60 backdrop-blur">
      <h1 className="text-2xl font-semibold text-slate-100">{title}</h1>
      {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
    </header>
  );
};

export default Header;
