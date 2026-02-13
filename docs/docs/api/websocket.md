# WebSocket Protocol

## Connection

```
ws://gateway:8080/ws
```

## Authentication

After connection, send an auth message:

```json
{ "type": "auth", "payload": { "token": "JWT_ACCESS_TOKEN" } }
```

## Message Format

JSON (default) or MessagePack (binary). The gateway auto-detects encoding.

```typescript
interface WSMessage {
  type: string;
  robot_id?: string;
  payload: Record<string, unknown>;
  timestamp?: string;
}
```

## Client → Gateway Messages

### velocity_cmd
```json
{
  "type": "velocity_cmd",
  "robot_id": "uuid",
  "payload": { "linear_x": 0.3, "linear_y": 0.0, "angular_z": 0.5 }
}
```

### estop
```json
{
  "type": "estop",
  "robot_id": "uuid",
  "payload": { "activate": true }
}
```

### nav_goal
```json
{
  "type": "nav_goal",
  "robot_id": "uuid",
  "payload": { "x": 1.5, "y": 2.0, "theta": 0.0 }
}
```

## Gateway → Client Messages

### sensor_data
```json
{
  "type": "sensor_data",
  "robot_id": "uuid",
  "payload": {
    "sensor_type": "lidar",
    "data": { "ranges": [1.2, 1.5, ...], "angle_min": -3.14, "angle_max": 3.14 }
  }
}
```

### robot_status
```json
{
  "type": "robot_status",
  "robot_id": "uuid",
  "payload": { "state": "moving", "battery_level": 85.2 }
}
```

### error
```json
{
  "type": "error",
  "payload": { "code": "ESTOP_ACTIVE", "message": "Emergency stop is active" }
}
```

## Safety Pipeline

All velocity commands pass through the safety pipeline before reaching the robot:

1. **E-Stop Check** → reject if active
2. **Operation Lock** → reject if locked by another user
3. **Velocity Limiter** → clamp to max linear/angular limits
4. **Timeout Watchdog** → auto-zero if no command in 500ms
