# Robot ML Web Application - React Version

This is a React + TypeScript implementation of the Robot ML Web Application.

## 🚀 Features

All features from the Vue.js and Vanilla JS versions:

- **ロボット制御**: Real-time joystick control, camera feed, robot status monitoring
- **データベース**: Record and manage robot data with selective saving
- **機械学習**: Train ML models with real-time progress visualization  
- **チャットボット**: RAG-based chatbot for Q&A

## 🏗️ Technology Stack

### Frontend
- **Framework**: React 18.2
- **Language**: TypeScript 5.2
- **Build Tool**: Vite 5.0
- **State Management**: Zustand 4.4
- **Router**: React Router 6.20
- **HTTP Client**: Axios 1.6
- **Visualization**: Chart.js 4.4 + react-chartjs-2
- **Joystick**: nipplejs 0.10

### Backend
Same as original - FastAPI backend is unchanged.

## 📁 Project Structure

```
frontend-react/
├── index.html                  # HTML entry point
├── package.json                # Dependencies
├── tsconfig.json              # TypeScript config
├── vite.config.ts             # Vite config
└── src/
    ├── main.tsx               # App entry point
    ├── App.tsx                # Root component
    ├── App.css                # App styles
    ├── index.css              # Global styles
    ├── config.ts              # Configuration
    ├── components/
    │   └── layout/
    │       ├── Header.tsx     # Header component
    │       └── Header.css     # Header styles
    ├── services/
    │   └── api.ts             # API client (Axios)
    ├── stores/
    │   └── connectionStore.ts # Connection state (Zustand)
    └── views/
        ├── RobotControlView.tsx
        ├── DatabaseView.tsx
        ├── MLView.tsx
        ├── ChatbotView.tsx
        └── Views.css
```

## 🛠️ Setup & Installation

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend-react

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 🔧 Configuration

Edit `src/config.ts` to change API and WebSocket URLs:

```typescript
export const config = {
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000',
};
```

Or use environment variables (`.env`):

```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 📊 Comparison with Other Versions

| Feature | Vanilla JS | React | Vue.js |
|---------|-----------|-------|--------|
| Framework | None | React 18 | Vue 3 |
| Bundle Size | ~180KB | ~220KB | ~450KB |
| Build Required | ❌ | ✅ | ✅ |
| TypeScript | ❌ | ✅ | ✅ |
| State Management | Custom | Zustand | Pinia |
| Router | Custom | React Router | Vue Router |
| Component Pattern | Classes | Hooks | Composition API |
| Learning Curve | Easy | Medium | Medium |
| Development Speed | Slow | Fast | Fast |
| Reactivity | Manual | Hooks | Automatic |

## 🎯 Why React Version?

### Advantages

✅ **Large Ecosystem**: Huge community and library support  
✅ **JSX**: Direct JavaScript in templates (no template syntax)  
✅ **Hooks**: Modern, reusable state logic  
✅ **Zustand**: Simple, lightweight state management  
✅ **Type Safety**: Full TypeScript support  
✅ **Performance**: Virtual DOM optimization  
✅ **Job Market**: Most popular framework  

### When to Choose React

- Building large-scale applications
- Team familiar with React ecosystem
- Need extensive third-party libraries
- Want component-based architecture
- TypeScript is a priority

## 💡 Key Implementation Details

### 1. State Management with Zustand

```typescript
// stores/connectionStore.ts
export const useConnectionStore = create<ConnectionState>((set) => ({
  mqttConnected: false,
  setMqttConnected: (connected) => set({ mqttConnected: connected }),
}))

// Usage in component
const { mqttConnected, setMqttConnected } = useConnectionStore()
```

### 2. React Hooks for WebSocket

```typescript
useEffect(() => {
  const ws = new WebSocket(wsUrl)
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    setRobotStatus(data)
  }
  return () => ws.close()
}, [])
```

### 3. React Router for Navigation

```typescript
<Routes>
  <Route path="/robot-control" element={<RobotControlView />} />
  <Route path="/database" element={<DatabaseView />} />
</Routes>
```

### 4. TypeScript Interfaces

```typescript
interface RobotStatus {
  position_x: number
  position_y: number
  orientation: number
  battery_level: number
  is_moving: boolean
}
```

## 🔄 Comparison with Vanilla JS

### Code Comparison

**Vanilla JS:**
```javascript
// Manual DOM updates
function updateStatus() {
  const el = document.getElementById('status');
  el.textContent = `Battery: ${robotStatus.battery_level}%`;
}
```

**React:**
```tsx
// Automatic re-render
<div>Battery: {robotStatus?.battery_level}%</div>
```

### State Management

**Vanilla JS:**
```javascript
class Store {
  constructor() {
    this.data = null;
  }
  update(newData) {
    this.data = newData;
    this.updateUI(); // Manual
  }
}
```

**React:**
```typescript
const [data, setData] = useState(null);
// Automatic re-render on setData()
```

## 📚 Learning Resources

- [React Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Zustand Guide](https://zustand-demo.pmnd.rs/)
- [React Router](https://reactrouter.com/)
- [Vite Guide](https://vitejs.dev/)

## 🧪 Testing

```bash
# Type checking
npm run type-check

# Linting
npm run lint
```

## 🚀 Deployment

### Static Hosting (Netlify, Vercel)

```bash
npm run build
# Upload dist/ folder
```

### Docker

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🤝 Contributing

When adding features:
1. Use TypeScript for type safety
2. Follow React best practices
3. Use Zustand for global state
4. Keep components focused and small
5. Add proper TypeScript types

## 📝 License

MIT License (same as main project)

---

**Built with ⚛️ React + TypeScript**
