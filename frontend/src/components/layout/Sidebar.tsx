import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Gamepad2,
  Navigation,
  Activity,
  Database,
  MessageSquare,
  Settings,
  LogOut,
  Bot,
  ChevronLeft,
} from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/control", label: "Manual Control", icon: Gamepad2, role: "operator" },
  { to: "/navigation", label: "Navigation", icon: Navigation, role: "operator" },
  { to: "/sensors", label: "Sensor View", icon: Activity },
  { to: "/data", label: "Data Management", icon: Database },
  { to: "/rag", label: "RAG Chat", icon: MessageSquare },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const hasRole = useAuthStore((s) => s.hasRole);

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r bg-card transition-all duration-200",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Header */}
      <div className="flex h-14 items-center justify-between border-b px-3">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <Bot className="h-6 w-6 text-primary" />
            <span className="font-semibold text-sm">Robot AI</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="rounded-md p-1.5 hover:bg-accent"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 p-2">
        {navItems
          .filter((item) => !item.role || hasRole(item.role as "admin" | "operator" | "viewer"))
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
      </nav>

      {/* User */}
      <div className="border-t p-2">
        {!collapsed && user && (
          <div className="mb-2 px-3 text-xs text-muted-foreground">
            <p className="font-medium text-foreground">{user.username}</p>
            <p className="capitalize">{user.role}</p>
          </div>
        )}
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
