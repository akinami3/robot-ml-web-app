// Example: How to create a new view in Vanilla JS

// 1. Create a new file: js/views/my-view.js
export class MyView {
    constructor() {
        // Initialize component state
        this.data = null;
        this.ws = null;
    }

    // Required: Render method that returns DOM element
    render() {
        const view = document.createElement('div');
        view.className = 'view my-view';
        view.innerHTML = `
            <div class="view-header">
                <h1>My View</h1>
                <p class="subtitle">Description of my view</p>
            </div>

            <div class="panel">
                <h2>Content</h2>
                <div id="myContent">
                    <!-- Dynamic content will be inserted here -->
                </div>
                <button id="myButton" class="btn btn-primary">Click Me</button>
            </div>
        `;
        return view;
    }

    // Required: Initialize event listeners and setup
    init() {
        this.setupEventListeners();
        this.loadData();
    }

    setupEventListeners() {
        const button = document.getElementById('myButton');
        if (button) {
            button.addEventListener('click', () => this.handleClick());
        }
    }

    async loadData() {
        try {
            // Import API service
            const { api } = await import('../services/api.js');
            const response = await api.get('/api/v1/my-endpoint');
            this.data = response;
            this.updateUI();
        } catch (error) {
            console.error('Failed to load data:', error);
        }
    }

    handleClick() {
        alert('Button clicked!');
    }

    updateUI() {
        const content = document.getElementById('myContent');
        if (content && this.data) {
            content.innerHTML = `<p>Data: ${JSON.stringify(this.data)}</p>`;
        }
    }

    // Optional: Setup WebSocket connection
    async setupWebSocket() {
        const { config } = await import('../config.js');
        const { WebSocketService } = await import('../services/websocket.js');
        
        const wsUrl = `${config.wsUrl}/api/v1/ws/my-endpoint`;
        
        this.ws = new WebSocketService(wsUrl, {
            onMessage: (data) => {
                console.log('Received:', data);
                this.handleWebSocketMessage(data);
            },
            onOpen: () => {
                console.log('WebSocket connected');
            },
        });

        this.ws.connect();
    }

    handleWebSocketMessage(data) {
        // Handle incoming WebSocket messages
        if (data.type === 'update') {
            this.data = data.payload;
            this.updateUI();
        }
    }

    // Required: Cleanup resources when view is unmounted
    cleanup() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// 2. Register the view in js/app.js
// import { MyView } from './views/my-view.js';
// router.register('my-view', MyView);

// 3. Add navigation link in index.html
// <a href="#my-view" class="nav-link" data-route="my-view">My View</a>

// 4. Add styles in css/components.css
// .my-view {
//     /* View-specific styles */
// }
