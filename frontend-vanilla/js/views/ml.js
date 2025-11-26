// Machine Learning View
import { api } from '../services/api.js';
import { config } from '../config.js';
import { WebSocketService } from '../services/websocket.js';

export class MLView {
    constructor() {
        this.isTraining = false;
        this.ws = null;
        this.chart = null;
        this.trainingData = {
            epochs: [],
            trainLoss: [],
            valLoss: [],
        };
    }

    render() {
        const view = document.createElement('div');
        view.className = 'view ml-view';
        view.innerHTML = `
            <div class="view-header">
                <h1>Machine Learning</h1>
                <p class="subtitle">Train and evaluate ML models</p>
            </div>

            <div class="panel">
                <h2>Training Configuration</h2>
                
                <form id="trainingForm" class="training-form">
                    <div class="form-group">
                        <label>Dataset</label>
                        <select class="input" id="datasetSelect">
                            <option value="dataset1">Dataset 1</option>
                            <option value="dataset2">Dataset 2</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Model Type</label>
                        <select class="input" id="modelSelect">
                            <option value="cnn">CNN</option>
                            <option value="resnet">ResNet</option>
                            <option value="mobilenet">MobileNet</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Batch Size</label>
                        <input type="number" class="input" id="batchSize" value="32" min="1">
                    </div>

                    <div class="form-group">
                        <label>Epochs</label>
                        <input type="number" class="input" id="epochs" value="10" min="1">
                    </div>

                    <div class="form-group">
                        <label>Learning Rate</label>
                        <input type="number" class="input" id="learningRate" value="0.001" step="0.0001">
                    </div>

                    <div class="form-group">
                        <label>Optimizer</label>
                        <select class="input" id="optimizer">
                            <option value="adam">Adam</option>
                            <option value="sgd">SGD</option>
                            <option value="rmsprop">RMSprop</option>
                        </select>
                    </div>
                </form>

                <div class="button-group" style="margin-top: 1.5rem;">
                    <button id="startTraining" class="btn btn-primary">トレーニング開始</button>
                    <button id="stopTraining" class="btn btn-danger" disabled>トレーニング停止</button>
                </div>

                <div id="trainingStatus" class="hidden navigating-status" style="margin-top: 1rem;">
                    <span class="pulse-dot"></span>
                    <span>Training in progress...</span>
                </div>
            </div>

            <div class="panel">
                <h2>Training Progress</h2>
                <div class="chart-container">
                    <canvas id="trainingChart"></canvas>
                </div>
            </div>
        `;
        return view;
    }

    init() {
        this.setupControls();
        this.setupChart();
    }

    setupControls() {
        const startBtn = document.getElementById('startTraining');
        const stopBtn = document.getElementById('stopTraining');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startTraining());
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopTraining());
        }
    }

    setupChart() {
        const canvas = document.getElementById('trainingChart');
        if (!canvas || !window.Chart) return;

        const ctx = canvas.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Training Loss',
                        data: [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                    },
                    {
                        label: 'Validation Loss',
                        data: [],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Training & Validation Loss',
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Loss',
                        },
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Epoch',
                        },
                    },
                },
            },
        });
    }

    async startTraining() {
        try {
            const config = {
                dataset: document.getElementById('datasetSelect').value,
                model_type: document.getElementById('modelSelect').value,
                batch_size: parseInt(document.getElementById('batchSize').value),
                epochs: parseInt(document.getElementById('epochs').value),
                learning_rate: parseFloat(document.getElementById('learningRate').value),
                optimizer: document.getElementById('optimizer').value,
            };

            await api.post('/api/v1/ml/training/start', config);
            this.isTraining = true;
            this.trainingData = { epochs: [], trainLoss: [], valLoss: [] };
            
            this.setupWebSocket();
            this.updateControls();
            
            const status = document.getElementById('trainingStatus');
            if (status) status.classList.remove('hidden');
        } catch (error) {
            console.error('Failed to start training:', error);
            alert('Failed to start training');
        }
    }

    async stopTraining() {
        try {
            await api.post('/api/v1/ml/training/stop');
            this.endTraining();
        } catch (error) {
            console.error('Failed to stop training:', error);
            alert('Failed to stop training');
        }
    }

    setupWebSocket() {
        const wsUrl = `${config.wsUrl}/api/v1/ws/ml`;
        
        this.ws = new WebSocketService(wsUrl, {
            onMessage: (data) => {
                if (data.type === 'training_progress') {
                    this.updateTrainingProgress(data.data);
                } else if (data.type === 'training_complete') {
                    this.endTraining();
                    alert('Training completed successfully!');
                }
            },
        });

        this.ws.connect();
    }

    updateTrainingProgress(data) {
        this.trainingData.epochs.push(data.epoch);
        this.trainingData.trainLoss.push(data.train_loss);
        this.trainingData.valLoss.push(data.val_loss);

        if (this.chart) {
            this.chart.data.labels = this.trainingData.epochs;
            this.chart.data.datasets[0].data = this.trainingData.trainLoss;
            this.chart.data.datasets[1].data = this.trainingData.valLoss;
            this.chart.update();
        }
    }

    endTraining() {
        this.isTraining = false;
        
        if (this.ws) {
            this.ws.close();
        }
        
        this.updateControls();
        
        const status = document.getElementById('trainingStatus');
        if (status) status.classList.add('hidden');
    }

    updateControls() {
        const startBtn = document.getElementById('startTraining');
        const stopBtn = document.getElementById('stopTraining');
        const formInputs = document.querySelectorAll('#trainingForm input, #trainingForm select');

        if (startBtn) startBtn.disabled = this.isTraining;
        if (stopBtn) stopBtn.disabled = !this.isTraining;
        
        formInputs.forEach(input => {
            input.disabled = this.isTraining;
        });
    }

    cleanup() {
        if (this.ws) {
            this.ws.close();
        }
        if (this.chart) {
            this.chart.destroy();
        }
    }
}
