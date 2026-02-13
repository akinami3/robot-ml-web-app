import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/primitives";

interface IMUChartProps {
  /** Array of { t, ax, ay, az, gx, gy, gz } history */
  data: Array<{
    t: number;
    ax?: number;
    ay?: number;
    az?: number;
    gx?: number;
    gy?: number;
    gz?: number;
  }>;
}

export function IMUChart({ data }: IMUChartProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">IMU</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <p className="mb-1 text-xs text-muted-foreground">Accelerometer (m/s²)</p>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="t" tick={false} />
                <YAxis width={40} fontSize={10} />
                <Tooltip />
                <Legend iconSize={8} wrapperStyle={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="ax" stroke="#ef4444" dot={false} strokeWidth={1.5} name="X" />
                <Line type="monotone" dataKey="ay" stroke="#22c55e" dot={false} strokeWidth={1.5} name="Y" />
                <Line type="monotone" dataKey="az" stroke="#3b82f6" dot={false} strokeWidth={1.5} name="Z" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div>
            <p className="mb-1 text-xs text-muted-foreground">Gyroscope (rad/s)</p>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="t" tick={false} />
                <YAxis width={40} fontSize={10} />
                <Tooltip />
                <Legend iconSize={8} wrapperStyle={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="gx" stroke="#f97316" dot={false} strokeWidth={1.5} name="X" />
                <Line type="monotone" dataKey="gy" stroke="#a855f7" dot={false} strokeWidth={1.5} name="Y" />
                <Line type="monotone" dataKey="gz" stroke="#06b6d4" dot={false} strokeWidth={1.5} name="Z" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
