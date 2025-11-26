// Header Component
import { api } from '../services/api.js';

export class Header {
    constructor() {
        this.simulatorRunning = false;
        this.init();
    }

    init() {
        const startBtn = document.getElementById('startSimulator');
        const stopBtn = document.getElementById('stopSimulator');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startSimulator());
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopSimulator());
        }
    }

    async startSimulator() {
        try {
            await api.post('/api/v1/robot/simulator/start');
            this.simulatorRunning = true;
            this.updateButtons();
        } catch (error) {
            console.error('Failed to start simulator:', error);
            alert('シミュレータの起動に失敗しました');
        }
    }

    async stopSimulator() {
        try {
            await api.post('/api/v1/robot/simulator/stop');
            this.simulatorRunning = false;
            this.updateButtons();
        } catch (error) {
            console.error('Failed to stop simulator:', error);
            alert('シミュレータの停止に失敗しました');
        }
    }

    updateButtons() {
        const startBtn = document.getElementById('startSimulator');
        const stopBtn = document.getElementById('stopSimulator');

        if (startBtn) {
            startBtn.disabled = this.simulatorRunning;
        }

        if (stopBtn) {
            stopBtn.disabled = !this.simulatorRunning;
        }
    }
}
