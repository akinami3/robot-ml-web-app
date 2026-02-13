import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { StatusBar } from "@/components/robot/StatusBar";
import { useWebSocket } from "@/hooks/useWebSocket";

export function AppLayout() {
  const { isConnected, reconnectCount } = useWebSocket();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <StatusBar isConnected={isConnected} reconnectCount={reconnectCount} />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
