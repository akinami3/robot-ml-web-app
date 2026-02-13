import { useEffect, useRef, useCallback } from "react";
import nipplejs, { type JoystickManager } from "nipplejs";

interface JoystickControllerProps {
  onMove: (linear_x: number, linear_y: number, angular_z: number) => void;
  onStop: () => void;
  maxLinear?: number;
  maxAngular?: number;
  disabled?: boolean;
}

export function JoystickController({
  onMove,
  onStop,
  maxLinear = 0.5,
  maxAngular = 1.0,
  disabled = false,
}: JoystickControllerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const managerRef = useRef<JoystickManager | null>(null);

  const handleMove = useCallback(
    (_: unknown, data: { distance: number; angle: { radian: number } }) => {
      if (disabled) return;
      const force = Math.min(data.distance / 75, 1);
      const angle = data.angle.radian;

      const linear_x = Math.sin(angle) * force * maxLinear;
      const angular_z = -Math.cos(angle) * force * maxAngular;

      onMove(linear_x, 0, angular_z);
    },
    [disabled, maxLinear, maxAngular, onMove]
  );

  useEffect(() => {
    if (!containerRef.current) return;

    const manager = nipplejs.create({
      zone: containerRef.current,
      mode: "static",
      position: { left: "50%", top: "50%" },
      color: disabled ? "#999" : "#3b82f6",
      size: 120,
    });

    managerRef.current = manager;
    manager.on("move", handleMove as never);
    manager.on("end", () => onStop());

    return () => {
      manager.destroy();
    };
  }, [disabled, handleMove, onStop]);

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        ref={containerRef}
        className="relative h-40 w-40 rounded-full border-2 border-dashed border-muted-foreground/30"
        style={{ touchAction: "none" }}
      />
      <span className="text-xs text-muted-foreground">
        {disabled ? "Control disabled" : "Drag to move"}
      </span>
    </div>
  );
}
