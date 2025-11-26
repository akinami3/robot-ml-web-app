# Robot ML Web Application - Vanilla JavaScript Version

This is a vanilla JavaScript implementation of the Robot ML Web Application, converted from the original Vue.js version.

## 🚀 Features

All features from the Vue.js version are preserved:

- **ロボット制御**: Real-time joystick control, camera feed, robot status monitoring
- **データベース**: Record and manage robot data with selective saving
- **機械学習**: Train ML models with real-time progress visualization
- **チャットボット**: RAG-based chatbot for Q&A

## 🏗️ Technology Stack

### Frontend
- **Pure JavaScript** (ES6 modules)
- **No Framework Dependencies** - Vanilla JavaScript only
- **External Libraries**:
  - axios 1.6.2 (HTTP client)
  - Chart.js 4.4.0 (Visualization)
  - nipplejs 0.10.1 (Joystick control)

### Backend
Same as original - FastAPI backend is unchanged.

## 📁 Project Structure

```
frontend-vanilla/
├── index.html          # Main HTML file
├── css/
│   ├── main.css        # Main styles
│   └── components.css  # Component styles
└── js/
    ├── app.js          # Application entry point
    ├── config.js       # Configuration
    ├── router.js       # Client-side routing
    ├── components/
    │   └── header.js   # Header component
    ├── services/
    │   ├── api.js      # API service
    │   └── websocket.js # WebSocket service
    ├── store/
    │   └── connection.js # Connection state management
    └── views/
        ├── robot-control.js # Robot control view
        ├── database.js      # Database view
        ├── ml.js           # Machine learning view
        └── chatbot.js      # Chatbot view
```

## 🛠️ Setup & Installation

### Option 1: Using Python HTTP Server

```bash
cd frontend-vanilla
python -m http.server 3000
```

Then access http://localhost:3000

### Option 2: Using Node.js HTTP Server

```bash
cd frontend-vanilla
npx http-server -p 3000 -c-1
```

### Option 3: Using VS Code Live Server

1. Install "Live Server" extension in VS Code
2. Right-click on `index.html`
3. Select "Open with Live Server"

### Option 4: Using Nginx

Create nginx configuration:

```nginx
server {
    listen 3000;
    server_name localhost;
    
    root /path/to/frontend-vanilla;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 🔧 Configuration

Edit `js/config.js` to change API and WebSocket URLs:

```javascript
export const config = {
    apiUrl: 'http://localhost:8000',
    wsUrl: 'ws://localhost:8000',
};
```

## 📊 Architecture Differences from Vue.js Version

### State Management
- **Vue**: Pinia stores with reactive state
- **Vanilla**: Custom store classes with manual DOM updates

### Routing
- **Vue**: Vue Router with component-based routing
- **Vanilla**: Custom hash-based router

### Components
- **Vue**: Single File Components (.vue files)
- **Vanilla**: ES6 classes with render() methods

### Reactivity
- **Vue**: Automatic reactive updates
- **Vanilla**: Manual DOM manipulation and updates

## 🎮 Usage

Same as Vue.js version:

1. Make sure the backend is running on `http://localhost:8000`
2. Open the frontend in your browser
3. Navigate using the header menu
4. All features work identically to the Vue version

## 🔌 API Communication

The vanilla JS version communicates with the same FastAPI backend:

- REST API: HTTP requests via axios/fetch
- Real-time: WebSocket connections
- Same endpoints and data formats as Vue version

## ⚡ Performance

Benefits of vanilla JavaScript:

- **Smaller bundle size** (no Vue framework overhead)
- **Faster initial load** (no framework compilation)
- **Direct DOM manipulation** (no virtual DOM)

Trade-offs:

- More boilerplate code
- Manual state management
- More verbose than Vue's declarative syntax

## 🧪 Testing

To test:

1. Start the backend server
2. Start the frontend server
3. Test each view:
   - Robot Control: Check joystick, status updates, camera feed
   - Database: Test recording controls
   - ML: Test training form and chart
   - Chatbot: Send messages and receive responses

## 📝 Development Notes

### Adding New Views

1. Create a new view class in `js/views/`
2. Implement `render()` and `init()` methods
3. Register the route in `js/app.js`

Example:

```javascript
export class NewView {
    render() {
        const view = document.createElement('div');
        view.className = 'view';
        view.innerHTML = `<h1>New View</h1>`;
        return view;
    }
    
    init() {
        // Initialize event listeners
    }
    
    cleanup() {
        // Cleanup resources
    }
}
```

### WebSocket Pattern

```javascript
import { WebSocketService } from '../services/websocket.js';

this.ws = new WebSocketService(wsUrl, {
    onMessage: (data) => {
        // Handle messages
    },
    onOpen: () => {
        // Handle connection open
    },
});

this.ws.connect();
```

## 🤝 Contributing

This vanilla JS version maintains feature parity with the Vue.js version. When adding features:

1. Keep the same API contracts
2. Maintain similar UX
3. Follow the established patterns
4. Update both versions when possible

## 📧 License

Same as main project - MIT License
