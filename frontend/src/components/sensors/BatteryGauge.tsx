import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";
import { Battery, BatteryCharging, BatteryWarning } from "lucide-react";
import { cn } from "@/lib/utils";

interface BatteryGaugeProps {
  percentage: number;
  voltage: number;
  isCharging?: boolean;
}

export function BatteryGauge({ percentage, voltage, isCharging = false }: BatteryGaugeProps) {
  const color =
    percentage > 50 ? "bg-green-500" : percentage > 20 ? "bg-yellow-500" : "bg-red-500";

  const Icon = isCharging ? BatteryCharging : percentage > 20 ? Battery : BatteryWarning;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Battery</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-3">
        <Icon className={cn("h-10 w-10", percentage > 50 ? "text-green-500" : percentage > 20 ? "text-yellow-500" : "text-red-500")} />

        {/* Bar */}
        <div className="h-3 w-full rounded-full bg-muted">
          <div
            className={cn("h-full rounded-full transition-all", color)}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>

        <div className="flex w-full justify-between text-sm">
          <span className="font-mono font-semibold">{percentage.toFixed(1)}%</span>
          <span className="font-mono text-muted-foreground">{voltage.toFixed(2)} V</span>
        </div>

        {isCharging && (
          <span className="text-xs text-green-600 dark:text-green-400">Charging</span>
        )}
      </CardContent>
    </Card>
  );
}
