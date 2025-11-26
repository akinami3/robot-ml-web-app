// Robot Control View
import { config } from '../config.js';
import { api } from '../services/api.js';
import { WebSocketService } from '../services/websocket.js';

export class RobotControlView {
    constructor() {
        this.robotStatus = null;
        this.cameraImage = '';
        this.isNavigating = false;
        this.ws = null;
        this.joystick = null;
        
        this.goalX = 0;
        this.goalY = 0;
        this.goalOrientation = 0;
    }

    render() {
        const view = document.createElement('div');
        view.className = 'view robot-control-view';
        view.innerHTML = `
            <div class="view-header">
                <h1>Robot Control</h1>
                <p class="subtitle">Control the robot and monitor its status in real-time</p>
            </div>

            <div class="control-grid">
                <!-- Robot Status Panel -->
                <div class="panel status-panel">
                    <h2>Robot Status</h2>
                    <div id="robotStatusContent">
                        <div class="no-status">
                            <p>No robot status available</p>
                        </div>
                    </div>
                </div>

                <!-- Camera Feed -->
                <div class="panel camera-feed">
                    <div id="cameraContent" class="camera-placeholder">
                        <p>No camera feed available</p>
                    </div>
                </div>

                <!-- Joystick Control -->
                <div class="joystick-container">
                    <h2>Joystick Control</h2>
                    <div id="joystick"></div>
                    <div class="joystick-info">
                        <p>Drag to control robot movement</p>
                    </div>
                </div>

                <!-- Navigation Panel -->
                <div class="panel navigation-panel">
                    <h2>Navigation</h2>
                    <form id="goalForm" class="goal-form">
                        <div class="form-group">
                            <label>Target X (m)</label>
                            <input type="number" step="0.1" class="input" id="goalX" value="0">
                        </div>
                        <div class="form-group">
                            <label>Target Y (m)</label>
                            <input type="number" step="0.1" class="input" id="goalY" value="0">
                        </div>
                        <div class="form-group">
                            <label>Orientation (°)</label>
                            <input type="number" step="1" class="input" id="goalOrientation" value="0">
                        </div>
                        <div class="button-group">
                            <button type="submit" class="btn btn-primary" id="setGoalBtn">Set Goal</button>
                            <button type="button" class="btn btn-danger" id="cancelGoalBtn" disabled>Cancel</button>
                        </div>
                    </form>
                    <div id="navigatingStatus" class="navigating-status hidden">
                        <span class="pulse-dot"></span>
                        <span>Navigating to goal...</span>
                    </div>
                </div>
            </div>
        `;
        return view;
    }

    init() {
        this.setupWebSocket();
        this.setupJoystick();
        this.setupNavigationForm();
    }

    setupWebSocket() {
        const wsUrl = `${config.wsUrl}/api/v1/ws/robot`;
        
        this.ws = new WebSocketService(wsUrl, {
            onMessage: (data) => {
                if (data.type === 'robot_status') {
                    this.robotStatus = data.data;
                    this.updateStatusDisplay();
                } else if (data.type === 'camera_image') {
                    this.cameraImage = data.data.image;
                    this.updateCameraDisplay();
                } else if (data.type === 'navigation_status') {
                    this.isNavigating = data.data.status === 'active';
                    this.updateNavigationStatus();
                }
            },
        });

        this.ws.connect();
    }

    setupJoystick() {
        if (!window.nipplejs) {
            console.error('nipplejs not loaded');
            return;
        }

        const joystickElement = document.getElementById('joystick');
        if (!joystickElement) return;

        const manager = nipplejs.create({
            zone: joystickElement,
            mode: 'static',
            position: { left: '50%', top: '50%' },
            color: '#2563eb',
            size: 150,
        });

        manager.on('move', (evt, data) => {
            const force = data.force;
            const angle = data.angle.radian;
            
            const vx = Math.cos(angle) * force;
            const vy = Math.sin(angle) * force;
            
            this.sendVelocity(vx, vy, 0, 0);
        });

        manager.on('end', () => {
            this.sendVelocity(0, 0, 0, 0);
        });

        this.joystick = manager;
    }

    setupNavigationForm() {
        const form = document.getElementById('goalForm');
        const cancelBtn = document.getElementById('cancelGoalBtn');

        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleSetGoal();
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', async () => {
                await this.handleCancelGoal();
            });
        }
    }

    sendVelocity(vx, vy, vz, angular) {
        if (this.ws && this.ws.isConnected) {
            this.ws.send({
                type: 'velocity_command',
                data: { vx, vy, vz, angular },
            });
        }
    }

    async handleSetGoal() {
        const goalX = parseFloat(document.getElementById('goalX').value);
        const goalY = parseFloat(document.getElementById('goalY').value);
        const goalOrientation = parseFloat(document.getElementById('goalOrientation').value);

        try {
            await api.post('/api/v1/robot/control/navigate', {
                target_x: goalX,
                target_y: goalY,
                target_orientation: (goalOrientation * Math.PI) / 180,
            });
            this.isNavigating = true;
            this.updateNavigationStatus();
        } catch (error) {
            alert('Failed to set navigation goal');
        }
    }

    async handleCancelGoal() {
        try {
            await api.delete('/api/v1/robot/control/navigate');
            this.isNavigating = false;
            this.updateNavigationStatus();
        } catch (error) {
            alert('Failed to cancel navigation');
        }
    }

    updateStatusDisplay() {
        const statusContent = document.getElementById('robotStatusContent');
        if (!statusContent) return;

        if (this.robotStatus) {
            const batteryColor = this.getBatteryColor(this.robotStatus.battery_level);
            
            statusContent.innerHTML = `
                <div class="status-info">
                    <div class="status-item-row">
                        <span class="label">Position X:</span>
                        <span class="value">${this.robotStatus.position_x.toFixed(2)} m</span>
                    </div>
                    <div class="status-item-row">
                        <span class="label">Position Y:</span>
                        <span class="value">${this.robotStatus.position_y.toFixed(2)} m</span>
                    </div>
                    <div class="status-item-row">
                        <span class="label">Orientation:</span>
                        <span class="value">${(this.robotStatus.orientation * 180 / Math.PI).toFixed(1)}°</span>
                    </div>
                    <div class="status-item-row">
                        <span class="label">Battery:</span>
                        <span class="value" style="color: ${batteryColor}">
                            ${this.robotStatus.battery_level}%
                        </span>
                    </div>
                    <div class="status-item-row">
                        <span class="label">Moving:</span>
                        <span class="value">${this.robotStatus.is_moving ? 'Yes' : 'No'}</span>
                    </div>
                </div>
            `;
        }
    }

    updateCameraDisplay() {
        const cameraContent = document.getElementById('cameraContent');
        if (!cameraContent) return;

        if (this.cameraImage) {
            cameraContent.innerHTML = `<img src="data:image/jpeg;base64,${this.cameraImage}" alt="Camera Feed">`;
        }
    }

    updateNavigationStatus() {
        const setGoalBtn = document.getElementById('setGoalBtn');
        const cancelGoalBtn = document.getElementById('cancelGoalBtn');
        const navigatingStatus = document.getElementById('navigatingStatus');

        if (setGoalBtn) {
            setGoalBtn.disabled = this.isNavigating;
        }

        if (cancelGoalBtn) {
            cancelGoalBtn.disabled = !this.isNavigating;
        }

        if (navigatingStatus) {
            if (this.isNavigating) {
                navigatingStatus.classList.remove('hidden');
            } else {
                navigatingStatus.classList.add('hidden');
            }
        }
    }

    getBatteryColor(level) {
        if (level > 60) return 'green';
        if (level > 30) return 'orange';
        return 'red';
    }

    cleanup() {
        if (this.ws) {
            this.ws.close();
        }
        if (this.joystick) {
            this.joystick.destroy();
        }
    }
}
