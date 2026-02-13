# REST API Reference

## Authentication

All endpoints (except login/register) require `Authorization: Bearer <token>` header.

### POST /api/v1/auth/login

```json
// Request
{ "username": "admin", "password": "secret" }

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/register

```json
// Request
{ "username": "operator1", "email": "op@example.com", "password": "pass123" }

// Response 201
{ "id": "uuid", "username": "operator1", "role": "viewer" }
```

### GET /api/v1/auth/me
Returns current user profile.

### POST /api/v1/auth/refresh
Refresh access token using refresh token.

---

## Robots

### GET /api/v1/robots
List all robots. Query params: `state`, `skip`, `limit`.

### POST /api/v1/robots
Create robot. Requires `operator` role.

```json
{ "name": "my_robot", "model": "turtlebot3", "adapter_type": "mock", "adapter_config": {} }
```

### GET /api/v1/robots/{id}
### PUT /api/v1/robots/{id}
### DELETE /api/v1/robots/{id}

---

## Sensors

### GET /api/v1/sensors/data
Query sensor data. Params: `robot_id`, `sensor_type`, `start_time`, `end_time`, `skip`, `limit`.

### GET /api/v1/sensors/latest/{robot_id}
Latest sensor data per type for a robot.

### GET /api/v1/sensors/aggregated
TimescaleDB time_bucket aggregation. Params: `robot_id`, `sensor_type`, `start_time`, `end_time`, `bucket_interval`.

---

## Datasets

### GET /api/v1/datasets
### POST /api/v1/datasets

```json
{ "name": "training_v1", "description": "...", "tags": ["lidar", "indoor"] }
```

### GET /api/v1/datasets/{id}
### DELETE /api/v1/datasets/{id}
### GET /api/v1/datasets/{id}/export?format=parquet

Supported formats: `csv`, `parquet`, `json`.

---

## Recordings

### POST /api/v1/recordings/start

```json
{
  "robot_id": "uuid",
  "name": "session_001",
  "config": {
    "sensor_types": ["lidar", "imu", "odometry"],
    "max_frequency_hz": 10
  }
}
```

### POST /api/v1/recordings/{id}/stop
### GET /api/v1/recordings
### GET /api/v1/recordings/{id}

---

## RAG

### POST /api/v1/rag/documents/upload
Multipart form upload. Accepts PDF, TXT, MD files.

### GET /api/v1/rag/documents
### DELETE /api/v1/rag/documents/{id}

### POST /api/v1/rag/query

```json
{ "query": "How does the LiDAR sensor work?", "top_k": 5 }
```

### POST /api/v1/rag/query/stream
SSE streaming version of RAG query.

---

## Audit

### GET /api/v1/audit
Admin only. Params: `user_id`, `action`, `start_time`, `end_time`, `skip`, `limit`.

---

## Users (Admin)

### GET /api/v1/users
### POST /api/v1/users
### PUT /api/v1/users/{id}
### DELETE /api/v1/users/{id}

---

## Health

### GET /health
Basic health check.

### GET /ready
Readiness probe (DB + Redis connectivity).
