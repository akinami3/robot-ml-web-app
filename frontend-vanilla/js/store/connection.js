// Connection Store
import { config } from '../config.js';
import { WebSocketService } from '../services/websocket.js';

class ConnectionStore {
    constructor() {
        this.mqttConnected = false;
        this.websocketConnected = false;
        this.ws = null;
        this.statusCheckInterval = null;
        this.listeners = [];
    }

    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    notify() {
        this.listeners.forEach(listener => listener({
            mqttConnected: this.mqttConnected,
            websocketConnected: this.websocketConnected,
        }));
    }

    startMonitoring() {
        const wsUrl = `${config.wsUrl}/api/v1/ws/connection`;
        
        this.ws = new WebSocketService(wsUrl, {
            onOpen: () => {
                this.websocketConnected = true;
                this.updateUI();
                this.requestStatus();
            },
            onMessage: (data) => {
                if (data.type === 'connection_status') {
                    this.mqttConnected = data.data.mqtt || false;
                    this.websocketConnected = data.data.websocket || false;
                    this.updateUI();
                }
            },
            onClose: () => {
                this.websocketConnected = false;
                this.updateUI();
            },
            onError: () => {
                this.websocketConnected = false;
                this.updateUI();
            },
        });

        this.ws.connect();

        // Periodic status check
        this.statusCheckInterval = setInterval(() => {
            this.requestStatus();
        }, 10000);
    }

    stopMonitoring() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    requestStatus() {
        if (this.ws && this.ws.isConnected) {
            this.ws.send({ type: 'status_request' });
        }
    }

    updateUI() {
        // Update MQTT status indicator
        const mqttStatus = document.getElementById('mqttStatus');
        if (mqttStatus) {
            if (this.mqttConnected) {
                mqttStatus.classList.add('connected');
            } else {
                mqttStatus.classList.remove('connected');
            }
        }

        // Update WebSocket status indicator
        const wsStatus = document.getElementById('wsStatus');
        if (wsStatus) {
            if (this.websocketConnected) {
                wsStatus.classList.add('connected');
            } else {
                wsStatus.classList.remove('connected');
            }
        }

        // Notify subscribers
        this.notify();
    }

    get allConnected() {
        return this.mqttConnected && this.websocketConnected;
    }
}

export const connectionStore = new ConnectionStore();
