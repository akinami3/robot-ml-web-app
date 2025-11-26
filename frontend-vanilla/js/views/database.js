// Database View
import { api } from '../services/api.js';
import { config } from '../config.js';
import { WebSocketService } from '../services/websocket.js';

export class DatabaseView {
    constructor() {
        this.isRecording = false;
        this.isPaused = false;
        this.ws = null;
        this.recordedData = [];
    }

    render() {
        const view = document.createElement('div');
        view.className = 'view database-view';
        view.innerHTML = `
            <div class="view-header">
                <h1>Database</h1>
                <p class="subtitle">Record and manage robot data</p>
            </div>

            <div class="panel">
                <h2>Recording Controls</h2>
                
                <div class="data-options">
                    <div class="checkbox-group">
                        <input type="checkbox" id="recordPosition" checked>
                        <label for="recordPosition">Position</label>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="recordOrientation" checked>
                        <label for="recordOrientation">Orientation</label>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="recordBattery" checked>
                        <label for="recordBattery">Battery</label>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="recordCamera">
                        <label for="recordCamera">Camera Images</label>
                    </div>
                </div>

                <div class="recording-controls">
                    <button id="startRecording" class="btn btn-primary">開始</button>
                    <button id="pauseRecording" class="btn btn-secondary" disabled>一時停止</button>
                    <button id="saveRecording" class="btn btn-success" disabled>保存</button>
                    <button id="discardRecording" class="btn btn-danger" disabled>破棄</button>
                    <button id="endRecording" class="btn btn-secondary" disabled>終了</button>
                </div>

                <div id="recordingStatus" class="hidden">
                    <p>Recording in progress... <span id="recordCount">0</span> records</p>
                </div>
            </div>

            <div class="panel">
                <h2>Recorded Data</h2>
                <div id="dataTableContainer">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Position X</th>
                                <th>Position Y</th>
                                <th>Orientation</th>
                                <th>Battery</th>
                            </tr>
                        </thead>
                        <tbody id="dataTableBody">
                            <tr>
                                <td colspan="5" style="text-align: center;">No data recorded</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        return view;
    }

    init() {
        this.setupControls();
    }

    setupControls() {
        const startBtn = document.getElementById('startRecording');
        const pauseBtn = document.getElementById('pauseRecording');
        const saveBtn = document.getElementById('saveRecording');
        const discardBtn = document.getElementById('discardRecording');
        const endBtn = document.getElementById('endRecording');

        if (startBtn) startBtn.addEventListener('click', () => this.startRecording());
        if (pauseBtn) pauseBtn.addEventListener('click', () => this.pauseRecording());
        if (saveBtn) saveBtn.addEventListener('click', () => this.saveRecording());
        if (discardBtn) discardBtn.addEventListener('click', () => this.discardRecording());
        if (endBtn) endBtn.addEventListener('click', () => this.endRecording());
    }

    async startRecording() {
        try {
            const options = {
                record_position: document.getElementById('recordPosition').checked,
                record_orientation: document.getElementById('recordOrientation').checked,
                record_battery: document.getElementById('recordBattery').checked,
                record_camera: document.getElementById('recordCamera').checked,
            };

            await api.post('/api/v1/database/recording/start', options);
            this.isRecording = true;
            this.isPaused = false;
            this.recordedData = [];
            
            this.setupWebSocket();
            this.updateControls();
            
            const status = document.getElementById('recordingStatus');
            if (status) status.classList.remove('hidden');
        } catch (error) {
            console.error('Failed to start recording:', error);
            alert('Failed to start recording');
        }
    }

    async pauseRecording() {
        try {
            await api.post('/api/v1/database/recording/pause');
            this.isPaused = true;
            this.updateControls();
        } catch (error) {
            console.error('Failed to pause recording:', error);
            alert('Failed to pause recording');
        }
    }

    async saveRecording() {
        try {
            await api.post('/api/v1/database/recording/save');
            alert('Recording saved successfully');
            this.endRecording();
        } catch (error) {
            console.error('Failed to save recording:', error);
            alert('Failed to save recording');
        }
    }

    async discardRecording() {
        if (!confirm('Are you sure you want to discard the recording?')) {
            return;
        }

        try {
            await api.post('/api/v1/database/recording/discard');
            this.endRecording();
        } catch (error) {
            console.error('Failed to discard recording:', error);
            alert('Failed to discard recording');
        }
    }

    async endRecording() {
        try {
            await api.post('/api/v1/database/recording/stop');
            this.isRecording = false;
            this.isPaused = false;
            
            if (this.ws) {
                this.ws.close();
            }
            
            this.updateControls();
            
            const status = document.getElementById('recordingStatus');
            if (status) status.classList.add('hidden');
        } catch (error) {
            console.error('Failed to end recording:', error);
            alert('Failed to end recording');
        }
    }

    setupWebSocket() {
        const wsUrl = `${config.wsUrl}/api/v1/ws/database`;
        
        this.ws = new WebSocketService(wsUrl, {
            onMessage: (data) => {
                if (data.type === 'recorded_data') {
                    this.recordedData.push(data.data);
                    this.updateDataTable();
                    this.updateRecordCount();
                }
            },
        });

        this.ws.connect();
    }

    updateControls() {
        const startBtn = document.getElementById('startRecording');
        const pauseBtn = document.getElementById('pauseRecording');
        const saveBtn = document.getElementById('saveRecording');
        const discardBtn = document.getElementById('discardRecording');
        const endBtn = document.getElementById('endRecording');

        if (startBtn) startBtn.disabled = this.isRecording;
        if (pauseBtn) pauseBtn.disabled = !this.isRecording || this.isPaused;
        if (saveBtn) saveBtn.disabled = !this.isRecording;
        if (discardBtn) discardBtn.disabled = !this.isRecording;
        if (endBtn) endBtn.disabled = !this.isRecording;
    }

    updateRecordCount() {
        const countElement = document.getElementById('recordCount');
        if (countElement) {
            countElement.textContent = this.recordedData.length;
        }
    }

    updateDataTable() {
        const tbody = document.getElementById('dataTableBody');
        if (!tbody) return;

        if (this.recordedData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No data recorded</td></tr>';
            return;
        }

        // Show last 10 records
        const recentData = this.recordedData.slice(-10);
        tbody.innerHTML = recentData.map(record => `
            <tr>
                <td>${new Date(record.timestamp).toLocaleTimeString()}</td>
                <td>${record.position_x?.toFixed(2) || '-'}</td>
                <td>${record.position_y?.toFixed(2) || '-'}</td>
                <td>${record.orientation ? (record.orientation * 180 / Math.PI).toFixed(1) + '°' : '-'}</td>
                <td>${record.battery_level || '-'}%</td>
            </tr>
        `).join('');
    }

    cleanup() {
        if (this.ws) {
            this.ws.close();
        }
    }
}
