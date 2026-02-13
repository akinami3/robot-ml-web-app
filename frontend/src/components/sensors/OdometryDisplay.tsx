import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";
import { ArrowUp, RotateCw } from "lucide-react";

interface OdometryDisplayProps {
  x: number;
  y: number;
  theta: number;
  linearVelocity: number;
  angularVelocity: number;
}

export function OdometryDisplay({ x, y, theta, linearVelocity, angularVelocity }: OdometryDisplayProps) {
  const thetaDeg = ((theta * 180) / Math.PI).toFixed(1);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Odometry</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Position</p>
            <p className="font-mono text-sm">
              X: {x.toFixed(3)} m
            </p>
            <p className="font-mono text-sm">
              Y: {y.toFixed(3)} m
            </p>
            <p className="font-mono text-sm">
              θ: {thetaDeg}°
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Velocity</p>
            <div className="flex items-center gap-1">
              <ArrowUp className="h-3 w-3" />
              <span className="font-mono text-sm">{linearVelocity.toFixed(3)} m/s</span>
            </div>
            <div className="flex items-center gap-1">
              <RotateCw className="h-3 w-3" />
              <span className="font-mono text-sm">{angularVelocity.toFixed(3)} rad/s</span>
            </div>
          </div>
        </div>

        {/* Mini compass */}
        <div className="mt-3 flex justify-center">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="35" fill="none" stroke="currentColor" opacity={0.2} strokeWidth="1" />
            <g transform={`rotate(${-theta * 180 / Math.PI}, 40, 40)`}>
              <polygon points="40,10 35,30 45,30" fill="#3b82f6" />
              <polygon points="40,70 35,50 45,50" fill="#94a3b8" />
            </g>
          </svg>
        </div>
      </CardContent>
    </Card>
  );
}
