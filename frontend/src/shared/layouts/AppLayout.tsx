import React from "react";

import Header from "../components/Header";
import TabNav from "../components/TabNav";

const TABS = [
  { label: "Robot Control", path: "/" },
  { label: "Data Browser", path: "/database" },
  { label: "ML Pipeline", path: "/ml" },
  { label: "Chatbot", path: "/chat" }
];

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
    <Header title="Robot ML Control Center" subtitle="統合ロボット・データ・ML・チャット管理" />
    <TabNav tabs={TABS} />
    <main className="flex-1 overflow-y-auto px-8 py-6 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      {children}
    </main>
  </div>
);

export default AppLayout;
