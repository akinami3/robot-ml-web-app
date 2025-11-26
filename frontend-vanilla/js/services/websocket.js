// WebSocket Service
export class WebSocketService {
    constructor(url, options = {}) {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = options.reconnectInterval || 5000;
        this.onMessage = options.onMessage || (() => {});
        this.onOpen = options.onOpen || (() => {});
        this.onClose = options.onClose || (() => {});
        this.onError = options.onError || (() => {});
        this.shouldReconnect = true;
        this.reconnectTimeout = null;
    }

    connect() {
        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = (event) => {
                console.log(`WebSocket connected: ${this.url}`);
                if (this.reconnectTimeout) {
                    clearTimeout(this.reconnectTimeout);
                    this.reconnectTimeout = null;
                }
                this.onOpen(event);
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.onMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error(`WebSocket error: ${this.url}`, error);
                this.onError(error);
            };

            this.ws.onclose = (event) => {
                console.log(`WebSocket closed: ${this.url}`);
                this.onClose(event);
                
                if (this.shouldReconnect) {
                    this.reconnectTimeout = setTimeout(() => {
                        console.log(`Attempting to reconnect: ${this.url}`);
                        this.connect();
                    }, this.reconnectInterval);
                }
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket is not connected');
        }
    }

    close() {
        this.shouldReconnect = false;
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    get isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}
