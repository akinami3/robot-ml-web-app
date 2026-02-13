# ADR-001: Frontend Framework

## Status
**Accepted**

## Context
We need a frontend framework for a real-time robot control web application with:
- WebSocket real-time communication
- Canvas-based sensor visualization (LiDAR)
- Complex state management (robot state, sensor data streams)
- Form-heavy pages (settings, data management)

## Decision
**React 18 + TypeScript + Vite**

## Alternatives Considered

| Criteria | React | Vue 3 | Svelte | Angular |
|----------|:-----:|:-----:|:------:|:-------:|
| Ecosystem size | ★★★★★ | ★★★★ | ★★★ | ★★★★ |
| TypeScript support | ★★★★★ | ★★★★ | ★★★★ | ★★★★★ |
| Real-time UX | ★★★★★ | ★★★★ | ★★★★ | ★★★★ |
| Learning curve | ★★★ | ★★★★ | ★★★★★ | ★★ |
| Robotics community | ★★★★★ | ★★★ | ★★ | ★★★ |

## Rationale
- Largest ecosystem for robotics-related libraries (Three.js, D3, nipplejs)
- Concurrent rendering (React 18) for high-frequency sensor updates
- Zustand for lightweight state management (simpler than Redux)
- Vite for fast HMR during development
- Strong TypeScript integration
