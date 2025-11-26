# React Version Quick Start Guide

This guide will help you get the React + TypeScript version running in under 5 minutes.

## ⚡ Quick Start (3 Steps)

```bash
# 1. Navigate to React frontend
cd robot-ml-web-app/frontend-react

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

**Done!** Open http://localhost:3000 in your browser.

## 📋 Prerequisites

Before you start, make sure you have:

- ✅ **Node.js 18+** installed ([Download](https://nodejs.org/))
- ✅ **npm** or **yarn** package manager
- ✅ **Backend server** running on port 8000

Check your Node.js version:
```bash
node --version  # Should be v18.0.0 or higher
npm --version   # Should be 8.0.0 or higher
```

## 🚀 Detailed Setup

### Step 1: Install Dependencies

```bash
cd frontend-react
npm install
```

This installs:
- React 18.2 (UI framework)
- TypeScript 5.2 (type safety)
- Vite 5.0 (build tool)
- Zustand 4.4 (state management)
- React Router 6.20 (routing)
- Axios 1.6 (HTTP client)
- Chart.js 4.4 (charts)
- nipplejs 0.10 (joystick)

**Expected time:** 30-60 seconds

### Step 2: Start Backend Server

The React app needs the backend API to be running.

**Option A: Using existing backend**
```bash
cd ../backend
python -m uvicorn main:app --reload
```

**Option B: Using Docker**
```bash
cd ..
docker-compose up backend
```

Verify backend is running:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Step 3: Start React Dev Server

```bash
npm run dev
```

You'll see:
```
  VITE v5.0.8  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.1.100:3000/
```

**Open http://localhost:3000** in your browser!

## 🎯 First-Time Setup Checklist

- [ ] Node.js 18+ installed
- [ ] Backend server running (port 8000)
- [ ] Dependencies installed (`npm install`)
- [ ] Dev server started (`npm run dev`)
- [ ] Browser opened to http://localhost:3000
- [ ] No console errors in browser DevTools

## 🔧 Configuration

### Environment Variables

Create a `.env` file in `frontend-react/`:

```bash
# API and WebSocket URLs
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

**Note:** Vite requires `VITE_` prefix for environment variables.

### Configuration File

Edit `src/config.ts` directly:

```typescript
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
};
```

## 🧪 Testing the App

### 1. Check Connection Status

- Top-right corner should show:
  - 🟢 **MQTT: Connected** (green)
  - 🟢 **WS: Connected** (green)

If not connected:
```bash
# Check backend logs
cd ../backend
tail -f logs/app.log
```

### 2. Test Each View

**Robot Control** (`/robot-control`):
- ✅ Camera feed displays
- ✅ Joystick appears and is draggable
- ✅ Robot status updates in real-time
- ✅ Navigation form submits

**Database** (`/database`):
- ✅ Recording controls work
- ✅ Data table updates
- ✅ Select options toggle

**ML** (`/ml`):
- ✅ Start training form submits
- ✅ Progress chart displays
- ✅ Real-time updates during training

**Chatbot** (`/chatbot`):
- ✅ Send message works
- ✅ Response displays
- ✅ Enter key submits

## 🐛 Troubleshooting

### Error: "Cannot find module 'react'"

**Cause:** Dependencies not installed.

**Solution:**
```bash
npm install
```

### Error: "EADDRINUSE: address already in use :::3000"

**Cause:** Port 3000 is already in use.

**Solution A:** Kill existing process
```bash
# Linux/Mac
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Solution B:** Use different port
```bash
npm run dev -- --port 3001
```

### Error: "Failed to fetch" in browser console

**Cause:** Backend server not running or wrong URL.

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check `src/config.ts` has correct URLs
3. Check CORS is enabled in backend

### TypeScript Errors in Editor

**Cause:** VSCode/IDE TypeScript server needs restart.

**Solution:**
1. Press `Cmd/Ctrl + Shift + P`
2. Type "TypeScript: Restart TS Server"
3. Press Enter

### React DevTools Not Working

**Cause:** Extension not installed.

**Solution:**
Install React DevTools:
- [Chrome](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
- [Firefox](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/)

## 📦 Production Build

### Build for Production

```bash
npm run build
```

This creates a `dist/` folder with optimized files:
- Minified JavaScript/CSS
- Tree-shaken dependencies
- Optimized images
- Source maps

**Output:**
```
dist/
├── index.html
├── assets/
│   ├── index-abc123.js
│   └── index-def456.css
└── ...
```

### Preview Production Build

```bash
npm run preview
```

Opens production build at http://localhost:4173

### Deploy to Static Hosting

**Netlify:**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd dist
netlify deploy --prod
```

**Vercel:**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

**GitHub Pages:**
```bash
# Build
npm run build

# Push dist/ to gh-pages branch
git subtree push --prefix dist origin gh-pages
```

## 🔄 Development Workflow

### Recommended Workflow

1. **Start backend** (terminal 1)
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

2. **Start frontend** (terminal 2)
   ```bash
   cd frontend-react
   npm run dev
   ```

3. **Make changes** to `src/` files
4. **Auto-reload** - Vite HMR updates instantly
5. **Check TypeScript errors** in editor
6. **Test in browser** - http://localhost:3000

### Useful Commands

```bash
# Development
npm run dev              # Start dev server with HMR

# Building
npm run build            # Production build
npm run preview          # Preview production build

# Code Quality
npm run lint             # Run ESLint
npm run type-check       # Check TypeScript types

# Dependencies
npm install <package>    # Add new dependency
npm update               # Update dependencies
```

## 📚 Next Steps

1. **Read the full README** → `README.md`
2. **Compare implementations** → `COMPARISON.md`
3. **Explore the code** → Start with `src/App.tsx`
4. **Learn React Hooks** → https://react.dev/reference/react
5. **Learn TypeScript** → https://www.typescriptlang.org/docs/

## 💡 Tips

### Hot Module Replacement (HMR)

Vite's HMR is incredibly fast:
- Edit any `.tsx` file → Instant update
- Edit any `.css` file → Instant update
- No page reload needed
- State is preserved

### TypeScript Benefits

TypeScript catches errors before runtime:
```typescript
// ❌ TypeScript error
const status: RobotStatus = { baterry_level: 100 }
//                             ^^ Typo caught!

// ✅ Correct
const status: RobotStatus = { battery_level: 100 }
```

### React DevTools

Use React DevTools to:
- Inspect component hierarchy
- View props and state
- Profile component renders
- Debug hooks

### Zustand DevTools

```typescript
import { devtools } from 'zustand/middleware'

export const useConnectionStore = create(
  devtools((set) => ({
    mqttConnected: false,
    setMqttConnected: (connected) => set({ mqttConnected: connected })
  }))
)
```

Enable Redux DevTools extension to inspect Zustand state!

## 🆘 Getting Help

- **Issues:** Check browser console for errors
- **Logs:** Check backend logs in `backend/logs/`
- **Documentation:** Read `README.md` and `COMPARISON.md`
- **React Docs:** https://react.dev/
- **TypeScript:** https://www.typescriptlang.org/

---

**Happy coding with React! 🚀**
