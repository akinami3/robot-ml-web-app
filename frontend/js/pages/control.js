// =============================================================================
// Step 6: リアルタイム制御ページ（Step 5 の内容をページモジュール化）
// =============================================================================
//
// 【ページモジュール化とは？】
// Step 5 では index.html に全ての UI が書かれていた。
// Step 6 ではルーターを導入し、「ページ」として分離する。
// ただし、リアルタイム制御はページ遷移しても WebSocket が切れないように注意。
//
// このページの HTML は基本的に Step 5 の内容をそのまま含む。
// ただし、H1 や固定 HTML 要素ではなく、container の中に描画する。
//
// =============================================================================

export function renderControlPage(container) {
  container.innerHTML = `
    <div class="page-header">
      <h2>🎮 リアルタイム制御</h2>
    </div>

    <div class="help">
      💡 <strong>安全パイプライン:</strong> コマンドは E-Stop → 速度制限 → アダプターの順でチェック。<br>
      E-Stop 発動中は <kbd>WASD</kbd> コマンドが拒否されます。解除ボタンで復帰。
    </div>

    <!-- 接続状態 -->
    <div class="status">
      <div id="statusDot" class="status-dot"></div>
      <span id="statusText">未接続</span>
    </div>

    <!-- コントロールボタン -->
    <div class="controls">
      <button id="btnConnect" class="btn-connect" onclick="connectWebSocket()">
        🔌 WS接続
      </button>
      <button id="btnDisconnect" class="btn-disconnect" onclick="disconnectWebSocket()" disabled>
        ❌ WS切断
      </button>
      <span style="color: #444;">|</span>
      <button id="btnRobotConnect" class="btn-robot-connect" onclick="sendRobotConnect()" disabled>
        🤖 ロボット接続
      </button>
      <button id="btnRobotDisconnect" class="btn-robot-disconnect" onclick="sendRobotDisconnect()" disabled>
        ⛔ ロボット切断
      </button>
      <button id="btnKeyboard" class="btn-keyboard" onclick="toggleKeyboardControl()" disabled>
        🎮 キーボード OFF
      </button>
    </div>

    <!-- 安全パネル -->
    <div class="safety-panel">
      <div class="safety-header"><h3>🛡️ 安全パネル</h3></div>
      <div class="safety-grid">
        <div class="safety-item">
          <div id="estopIndicator" class="estop-indicator">✅ 正常</div>
        </div>
        <div class="safety-item safety-buttons">
          <button id="btnEStop" class="btn-estop" onclick="sendEStop()" disabled title="緊急停止">
            🛑 E-STOP
          </button>
          <button id="btnEStopRelease" class="btn-estop-release" onclick="sendEStopRelease()" disabled title="E-Stop 解除">
            ✅ 解除
          </button>
        </div>
        <div class="safety-item">
          <div class="safety-label">速度制限</div>
          <div id="velocityLimits" class="safety-value">-- m/s | -- rad/s</div>
        </div>
        <div class="safety-item">
          <div class="safety-label">アダプター</div>
          <div id="adapterName" class="safety-value">--</div>
        </div>
        <div class="safety-item">
          <div class="safety-label">ロボット状態</div>
          <div id="robotStatus" class="safety-value">🔴 未接続</div>
        </div>
      </div>
    </div>

    <!-- センサーダッシュボード -->
    <div class="dashboard-grid">
      <div class="sensor-card">
        <div class="card-header">
          <h3>📡 LiDAR</h3>
          <span class="card-badge" id="lidarHz">0 Hz</span>
        </div>
        <div class="canvas-container">
          <canvas id="lidarCanvas" width="400" height="400"></canvas>
        </div>
      </div>

      <div class="sensor-card">
        <div class="card-header">
          <h3>🧭 IMU（慣性計測装置）</h3>
          <span class="card-badge" id="imuHz">0 Hz</span>
        </div>
        <div class="canvas-container">
          <canvas id="imuCanvas" width="400" height="250"></canvas>
        </div>
        <div id="imuLegend"></div>
      </div>

      <div class="sensor-card">
        <div class="card-header">
          <h3>📍 オドメトリ</h3>
          <span class="card-badge" id="odomHz">0 Hz</span>
        </div>
        <div class="canvas-container">
          <canvas id="odomCanvas" width="400" height="300"></canvas>
        </div>
        <div id="odomValues"></div>
      </div>

      <div class="sensor-card">
        <div class="card-header">
          <h3>🔋 バッテリー</h3>
          <span class="card-badge" id="batteryHz">0 Hz</span>
        </div>
        <div id="batteryGauge"></div>
      </div>

      <div class="sensor-card">
        <div class="card-header">
          <h3>🎮 キーボード操作</h3>
        </div>
        <div class="keyboard">
          <div class="wasd-grid">
            <div id="keyW" class="key key-w">W</div>
            <div id="keyA" class="key">A</div>
            <div id="keyS" class="key">S</div>
            <div id="keyD" class="key">D</div>
            <div id="keySpace" class="key key-space">SPACE</div>
          </div>
          <div id="lastCommand" class="last-command">キーボードをONにして操作</div>
        </div>
      </div>
    </div>

    <!-- メッセージログ -->
    <h2>📋 メッセージログ</h2>
    <div id="messages" class="messages"></div>
    <div id="counter" class="counter">送信: 0 | 受信: 0</div>
  `;
}
