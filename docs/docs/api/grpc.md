# gRPC Services

!!! note "Status"
    gRPC interface is defined in proto files but the client implementation is a placeholder. Future versions will use generated protobuf stubs.

## Proto Definitions

### gateway_service.proto

```protobuf
service GatewayService {
  rpc SendCommand(CommandRequest) returns (CommandResponse);
  rpc EmergencyStopRobot(EmergencyStopRequest) returns (EmergencyStopResponse);
  rpc EmergencyStopAll(EmergencyStopAllRequest) returns (EmergencyStopResponse);
  rpc GetRobotStatus(GetRobotStatusRequest) returns (RobotStatusResponse);
  rpc ListConnectedRobots(ListRobotsRequest) returns (ListRobotsResponse);
  rpc StreamSensorData(StreamSensorRequest) returns (stream SensorData);
  rpc AcquireOperationLock(LockRequest) returns (LockResponse);
  rpc ReleaseOperationLock(LockRequest) returns (LockResponse);
}
```

### sensor.proto

Defines: `LaserScan`, `PointCloud`, `Imu`, `CompressedImage`, `Odometry`, `BatteryState`, `NavSatFix`, and a unified `SensorData` envelope with `oneof` for all sensor types.

### command.proto

Defines: `VelocityCommand`, `NavigationGoal`, `NavigationCancel`, `WaypointNavigation`, `EmergencyStop`, `RobotStatus`, `OperationLock`.
