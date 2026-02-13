import { useState } from "react";
import { useRobotStore } from "@/stores/robotStore";
import { LiDARViewer } from "@/components/sensors/LiDARViewer";
import { IMUChart } from "@/components/sensors/IMUChart";
import { OdometryDisplay } from "@/components/sensors/OdometryDisplay";
import { BatteryGauge } from "@/components/sensors/BatteryGauge";
import { Select } from "@/components/ui/primitives";

export function SensorViewPage() {
  const robots = useRobotStore((s) => s.robots);
  const selectedId = useRobotStore((s) => s.selectedRobotId);
  const setSelected = useRobotStore((s) => s.selectRobot);
  const latestSensor = useRobotStore((s) => s.latestSensorData);

  const data = selectedId ? latestSensor[selectedId] ?? {} : {};

  const lidar = data.lidar as { ranges?: number[] } | undefined;
  const imu = data.imu as { ax?: number; ay?: number; az?: number; gx?: number; gy?: number; gz?: number } | undefined;
  const odom = data.odometry as { x?: number; y?: number; theta?: number; linear_velocity?: number; angular_velocity?: number } | undefined;
  const battery = data.battery as { percentage?: number; voltage?: number; is_charging?: boolean } | undefined;

  // Keep IMU history in state
  const [imuHistory] = useState<Array<{ t: number; ax?: number; ay?: number; az?: number; gx?: number; gy?: number; gz?: number }>>([]);
  if (imu) {
    imuHistory.push({ t: Date.now(), ...imu });
    if (imuHistory.length > 200) imuHistory.splice(0, imuHistory.length - 200);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Sensor View</h1>
        <Select
          value={selectedId ?? ""}
          onChange={(e) => setSelected(e.target.value || null)}
          className="w-48"
        >
          <option value="">Select robot</option>
          {robots.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </Select>
      </div>

      {!selectedId ? (
        <p className="text-sm text-muted-foreground">Select a robot to view sensor data.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <LiDARViewer ranges={lidar?.ranges ?? []} />
          <IMUChart data={imuHistory} />
          <OdometryDisplay
            x={odom?.x ?? 0}
            y={odom?.y ?? 0}
            theta={odom?.theta ?? 0}
            linearVelocity={odom?.linear_velocity ?? 0}
            angularVelocity={odom?.angular_velocity ?? 0}
          />
          <BatteryGauge
            percentage={battery?.percentage ?? 0}
            voltage={battery?.voltage ?? 0}
            isCharging={battery?.is_charging ?? false}
          />
        </div>
      )}
    </div>
  );
}
