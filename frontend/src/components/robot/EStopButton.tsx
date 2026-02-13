import { useRobotStore } from "@/stores/robotStore";
import { cn } from "@/lib/utils";

interface EStopButtonProps {
  robotId?: string;
  onActivate: (robotId?: string) => void;
  onRelease: (robotId?: string) => void;
}

export function EStopButton({ robotId, onActivate, onRelease }: EStopButtonProps) {
  const isActive = useRobotStore((s) => s.isEStopActive);

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={() => (isActive ? onRelease(robotId) : onActivate(robotId))}
        className={cn(
          "relative h-24 w-24 rounded-full border-4 font-bold text-white text-sm uppercase tracking-wider shadow-lg transition-all",
          "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-yellow-400",
          isActive
            ? "animate-estop-pulse border-red-800 bg-red-600 hover:bg-red-700"
            : "border-red-700 bg-red-500 hover:bg-red-600 hover:scale-105 active:scale-95"
        )}
        aria-label={isActive ? "Release Emergency Stop" : "Activate Emergency Stop"}
        role="switch"
        aria-checked={isActive}
      >
        <span className="block leading-tight">
          {isActive ? "RELEASE" : "E-STOP"}
        </span>
      </button>
      <span className="text-xs text-muted-foreground">
        {isActive ? "Emergency stop active" : "Press ESC or click"}
      </span>
    </div>
  );
}
