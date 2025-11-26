// Main Application
import { connectionStore } from './store/connection.js';
import { Header } from './components/header.js';
import { router } from './router.js';
import { RobotControlView } from './views/robot-control.js';
import { DatabaseView } from './views/database.js';
import { MLView } from './views/ml.js';
import { ChatbotView } from './views/chatbot.js';

class App {
    constructor() {
        this.header = null;
    }

    init() {
        // Initialize connection monitoring
        connectionStore.startMonitoring();

        // Initialize header
        this.header = new Header();

        // Register routes
        router.register('robot-control', RobotControlView);
        router.register('database', DatabaseView);
        router.register('machine-learning', MLView);
        router.register('chatbot', ChatbotView);

        // Handle cleanup on page unload
        window.addEventListener('beforeunload', () => {
            connectionStore.stopMonitoring();
        });
    }
}

// Start the application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const app = new App();
        app.init();
    });
} else {
    const app = new App();
    app.init();
}
