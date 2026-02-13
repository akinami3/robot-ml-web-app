import { useState, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from "@/components/ui/primitives";
import { EStopButton } from "@/components/robot/EStopButton";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useRobotStore } from "@/stores/robotStore";
import { MapPin, Navigation as NavIcon, X } from "lucide-react";

export function NavigationPage() {
  const selectedRobotId = useRobotStore((s) => s.selectedRobotId);
  const { sendNavGoal, sendEStop, releaseEStop } = useWebSocket();

  const [goalX, setGoalX] = useState("0");
  const [goalY, setGoalY] = useState("0");
  const [goalTheta, setGoalTheta] = useState("0");
  const [navStatus, setNavStatus] = useState<"idle" | "navigating">("idle");

  const handleSendGoal = useCallback(() => {
    if (!selectedRobotId) return;
    sendNavGoal(selectedRobotId, parseFloat(goalX), parseFloat(goalY), parseFloat(goalTheta));
    setNavStatus("navigating");
  }, [selectedRobotId, goalX, goalY, goalTheta, sendNavGoal]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Navigation</h1>

      {!selectedRobotId && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-800 dark:border-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-200">
          Select a robot from the Dashboard first.
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Goal setting */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MapPin className="h-4 w-4" />
              Navigation Goal
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-muted-foreground">X (m)</label>
                <Input type="number" step="0.1" value={goalX} onChange={(e) => setGoalX(e.target.value)} />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Y (m)</label>
                <Input type="number" step="0.1" value={goalY} onChange={(e) => setGoalY(e.target.value)} />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">θ (rad)</label>
                <Input type="number" step="0.1" value={goalTheta} onChange={(e) => setGoalTheta(e.target.value)} />
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={handleSendGoal} disabled={!selectedRobotId} className="gap-2">
                <NavIcon className="h-4 w-4" />
                Send Goal
              </Button>
              {navStatus === "navigating" && (
                <Button variant="outline" onClick={() => setNavStatus("idle")} className="gap-2">
                  <X className="h-4 w-4" />
                  Cancel
                </Button>
              )}
            </div>

            {navStatus === "navigating" && (
              <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-800 dark:bg-blue-900/20 dark:text-blue-200">
                Navigating to ({goalX}, {goalY}, {goalTheta})...
              </div>
            )}

            {/* Map placeholder */}
            <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/20">
              <p className="text-sm text-muted-foreground">Map visualization (future)</p>
            </div>
          </CardContent>
        </Card>

        {/* E-Stop */}
        <Card className="flex items-center justify-center">
          <CardContent className="py-8">
            <EStopButton
              robotId={selectedRobotId ?? undefined}
              onActivate={sendEStop}
              onRelease={releaseEStop}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
