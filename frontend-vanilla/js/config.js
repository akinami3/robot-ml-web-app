// Configuration
export const config = {
    apiUrl: window.location.hostname === 'localhost' 
        ? 'http://localhost:8000' 
        : `http://${window.location.hostname}:8000`,
    wsUrl: window.location.hostname === 'localhost' 
        ? 'ws://localhost:8000' 
        : `ws://${window.location.hostname}:8000`,
};
