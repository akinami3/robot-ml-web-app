import { Wifi, WifiOff, Battery, BatteryWarning, Bot } from "lucide-react";
import { Badge } from "@/components/ui/primitives";
import { useRobotStore } from "@/stores/robotStore";
import { robotStateColor } from "@/lib/utils";

interface StatusBarProps {
  isConnected: boolean;
  reconnectCount: number;
}

export function StatusBar({ isConnected, reconnectCount }: StatusBarProps) {
  const robots = useRobotStore((s) => s.robots);
  const selectedId = useRobotStore((s) => s.selectedRobotId);
  const latestSensor = useRobotStore((s) => s.latestSensorData);

  const robot = robots.find((r) => r.id === selectedId);
  const battery = selectedId ? latestSensor[selectedId]?.battery : undefined;
  const batteryLevel = battery ? ((battery as unknown as Record<string, number>).percentage ?? 0) : 0;

  return (
    <div className="flex h-10 items-center gap-4 border-b bg-card px-4 text-sm">
      {/* Connection */}
      <div className="flex items-center gap-1.5">
        {isConnected ? (
          <Wifi className="h-4 w-4 text-green-500" />
        ) : (
          <WifiOff className="h-4 w-4 text-destructive" />
        )}
        <span className={isConnected ? "text-green-600 dark:text-green-400" : "text-destructive"}>
          {isConnected ? "Connected" : reconnectCount > 0 ? `Reconnecting (${reconnectCount})` : "Disconnected"}
        </span>
      </div>

      {/* Robot info */}
      {robot && (
        <>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-1.5">
            <Bot className="h-4 w-4" />
            <span className="font-medium">{robot.name}</span>
            <Badge variant="outline" className={robotStateColor(robot.state)}>
              {robot.state}
            </Badge>
          </div>

          {/* Battery */}
          <div className="flex items-center gap-1.5">
            {batteryLevel > 20 ? (
              <Battery className="h-4 w-4 text-green-500" />
            ) : (
              <BatteryWarning className="h-4 w-4 text-yellow-500" />
            )}
            <span>{batteryLevel.toFixed(0)}%</span>
          </div>
        </>
      )}
    </div>
  );
}
