import { useCallback, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";
import { EStopButton } from "@/components/robot/EStopButton";
import { JoystickController } from "@/components/robot/JoystickController";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useKeyboardControl } from "@/hooks/useKeyboardControl";
import { useRobotStore } from "@/stores/robotStore";
import { useAuthStore } from "@/stores/authStore";

const LINEAR_SPEED = 0.3;
const ANGULAR_SPEED = 0.8;

export function ManualControlPage() {
  const selectedRobotId = useRobotStore((s) => s.selectedRobotId);
  const isEStopActive = useRobotStore((s) => s.isEStopActive);
  const lastCommand = useRobotStore((s) => s.lastCommand);
  const setLastCommand = useRobotStore((s) => s.setLastCommand);
  const canControl = useAuthStore((s) => s.canControlRobot);
  const { sendVelocity, sendEStop, releaseEStop } = useWebSocket();
  const [keyboardEnabled, setKeyboardEnabled] = useState(true);

  const disabled = !selectedRobotId || isEStopActive || !canControl();

  const move = useCallback(
    (lx: number, ly: number, az: number) => {
      if (disabled || !selectedRobotId) return;
      sendVelocity(selectedRobotId, lx, ly, az);
      setLastCommand({ linear_x: lx, linear_y: ly, angular_z: az });
    },
    [disabled, selectedRobotId, sendVelocity, setLastCommand]
  );

  const stop = useCallback(() => {
    if (!selectedRobotId) return;
    sendVelocity(selectedRobotId, 0, 0, 0);
    setLastCommand({ linear_x: 0, linear_y: 0, angular_z: 0 });
  }, [selectedRobotId, sendVelocity, setLastCommand]);

  useKeyboardControl({
    onForward: () => move(LINEAR_SPEED, 0, 0),
    onBackward: () => move(-LINEAR_SPEED, 0, 0),
    onLeft: () => move(0, 0, ANGULAR_SPEED),
    onRight: () => move(0, 0, -ANGULAR_SPEED),
    onStop: stop,
    onEStop: () => sendEStop(selectedRobotId ?? undefined),
    enabled: keyboardEnabled && !disabled,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Manual Control</h1>

      {!selectedRobotId && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-800 dark:border-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-200">
          Select a robot from the Dashboard first.
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Joystick */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Joystick</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4">
            <JoystickController
              onMove={(lx, _ly, az) => move(lx, 0, az)}
              onStop={stop}
              disabled={disabled}
            />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={keyboardEnabled}
                onChange={(e) => setKeyboardEnabled(e.target.checked)}
                className="rounded"
              />
              Keyboard (WASD / Arrows)
            </label>
          </CardContent>
        </Card>

        {/* Velocity display */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Velocity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 font-mono text-sm">
            <VelocityBar label="Linear X" value={lastCommand?.linear_x ?? 0} max={1} />
            <VelocityBar label="Linear Y" value={lastCommand?.linear_y ?? 0} max={1} />
            <VelocityBar label="Angular Z" value={lastCommand?.angular_z ?? 0} max={2} />
          </CardContent>
        </Card>

        {/* E-Stop */}
        <Card className="flex items-center justify-center lg:col-span-1">
          <CardContent className="py-8">
            <EStopButton
              robotId={selectedRobotId ?? undefined}
              onActivate={sendEStop}
              onRelease={releaseEStop}
            />
          </CardContent>
        </Card>
      </div>

      <div className="rounded-md border p-3 text-xs text-muted-foreground">
        <strong>Keyboard shortcuts:</strong> W/↑ Forward · S/↓ Backward · A/← Turn Left · D/→ Turn Right · Space Stop · ESC Emergency Stop
      </div>
    </div>
  );
}

function VelocityBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = (Math.abs(value) / max) * 100;
  const isNegative = value < 0;

  return (
    <div>
      <div className="flex justify-between text-xs">
        <span>{label}</span>
        <span>{value.toFixed(3)}</span>
      </div>
      <div className="mt-1 flex h-2 overflow-hidden rounded-full bg-muted">
        <div className="w-1/2" />
        <div className="relative w-1/2">
          {!isNegative && (
            <div
              className="absolute left-0 h-full rounded-r-full bg-primary transition-all"
              style={{ width: `${pct}%` }}
            />
          )}
        </div>
      </div>
      <div className="flex h-2 overflow-hidden rounded-full bg-muted" style={{ marginTop: -8 }}>
        <div className="relative w-1/2">
          {isNegative && (
            <div
              className="absolute right-0 h-full rounded-l-full bg-primary transition-all"
              style={{ width: `${pct}%` }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
