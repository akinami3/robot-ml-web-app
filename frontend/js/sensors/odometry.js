// =============================================================================
// Step 4: オドメトリ（走行距離計）ビューア — 位置と速度の表示
// =============================================================================
//
// 【オドメトリとは？】
// ロボットの車輪の回転数から推定した位置・姿勢のこと。
// 現実のロボットでは累積誤差が出るため、SLAM（LiDAR ベース）と
// 組み合わせて補正する。ここでは MockAdapter が生成するデータを表示。
//
// 【表示内容】
// 1. ミニマップ — Canvas に移動軌跡を描画
// 2. 数値表示 — 位置 (x, y)、角度 θ、速度 (linear, angular)
//
// 【Canvas の座標変換】
// ロボット座標系: 右が +X、上が +Y（数学的座標系）
// Canvas 座標系:  右が +X、下が +Y
// → Y 軸を反転して描画する
// =============================================================================

export class OdometryViewer {
  #canvas;
  #ctx;
  #valuesEl;
  #trail = [];            // 軌跡を保存する配列
  #maxTrailLength = 300;  // 最大何点まで軌跡を保存するか

  // 表示スケール（ワールド座標 → ピクセル）
  #scale = 30;  // 1m = 30px

  constructor(canvasId, valuesContainerId) {
    this.#canvas = document.getElementById(canvasId);
    this.#valuesEl = document.getElementById(valuesContainerId);

    if (this.#canvas) {
      this.#ctx = this.#canvas.getContext("2d");
      this.#drawEmpty();
    }
  }

  // ---------------------------------------------------------------------------
  // update — オドメトリデータを受け取って表示更新
  // ---------------------------------------------------------------------------
  update(data) {
    // 軌跡に現在位置を追加
    this.#trail.push({ x: data.pos_x || 0, y: data.pos_y || 0 });
    if (this.#trail.length > this.#maxTrailLength) {
      this.#trail.shift();
    }

    this.#drawMap(data);
    this.#drawValues(data);
  }

  // ---------------------------------------------------------------------------
  // #drawMap — ミニマップに軌跡とロボットを描画
  // ---------------------------------------------------------------------------
  #drawMap(data) {
    const ctx = this.#ctx;
    if (!ctx) return;

    const w = this.#canvas.width;
    const h = this.#canvas.height;

    // 背景クリア
    ctx.fillStyle = "#0a1a0a";
    ctx.fillRect(0, 0, w, h);

    // グリッド（1m 間隔）
    ctx.strokeStyle = "rgba(0, 255, 0, 0.1)";
    ctx.lineWidth = 1;
    const gridPx = this.#scale;

    // 中心を Canvas の中央に設定
    const cx = w / 2;
    const cy = h / 2;

    // 垂直線
    for (let x = cx % gridPx; x < w; x += gridPx) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    // 水平線
    for (let y = cy % gridPx; y < h; y += gridPx) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // 原点の十字線
    ctx.strokeStyle = "rgba(0, 255, 0, 0.3)";
    ctx.beginPath();
    ctx.moveTo(cx, 0);
    ctx.lineTo(cx, h);
    ctx.moveTo(0, cy);
    ctx.lineTo(w, cy);
    ctx.stroke();

    // 軌跡を描画（薄い緑のライン）
    if (this.#trail.length > 1) {
      ctx.beginPath();
      ctx.strokeStyle = "rgba(0, 212, 255, 0.4)";
      ctx.lineWidth = 1.5;

      const first = this.#trail[0];
      ctx.moveTo(cx + first.x * this.#scale, cy - first.y * this.#scale); // Y反転

      for (let i = 1; i < this.#trail.length; i++) {
        const pt = this.#trail[i];
        ctx.lineTo(cx + pt.x * this.#scale, cy - pt.y * this.#scale);
      }
      ctx.stroke();
    }

    // ロボット（三角形）の描画
    const px = data.pos_x || 0;
    const py = data.pos_y || 0;
    const theta = data.theta || 0;

    const rx = cx + px * this.#scale;
    const ry = cy - py * this.#scale;
    const size = 8;

    ctx.save();
    ctx.translate(rx, ry);
    // Canvas は時計回りが正、ロボット座標系は反時計回りが正
    // さらに Y 軸反転しているので -theta をそのまま使う
    ctx.rotate(-theta);

    ctx.beginPath();
    ctx.moveTo(size * 1.5, 0);           // 前方（進行方向）
    ctx.lineTo(-size, -size);              // 左後ろ
    ctx.lineTo(-size, size);               // 右後ろ
    ctx.closePath();

    ctx.fillStyle = "#00d4ff";
    ctx.fill();
    ctx.strokeStyle = "#00ff88";
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.restore();
  }

  // ---------------------------------------------------------------------------
  // #drawValues — 数値データを HTML で表示
  // ---------------------------------------------------------------------------
  #drawValues(data) {
    if (!this.#valuesEl) return;

    const formatNum = (v) => (v || 0).toFixed(3);
    const thetaDeg = ((data.theta || 0) * 180 / Math.PI).toFixed(1);

    this.#valuesEl.innerHTML = `
      <div class="value-grid">
        <div class="value-item">
          <span class="value-label">X</span>
          <span class="value-num">${formatNum(data.pos_x)} m</span>
        </div>
        <div class="value-item">
          <span class="value-label">Y</span>
          <span class="value-num">${formatNum(data.pos_y)} m</span>
        </div>
        <div class="value-item">
          <span class="value-label">θ</span>
          <span class="value-num">${thetaDeg}°</span>
        </div>
        <div class="value-item">
          <span class="value-label">速度</span>
          <span class="value-num">${formatNum(data.speed)} m/s</span>
        </div>
        <div class="value-item">
          <span class="value-label">直進</span>
          <span class="value-num">${formatNum(data.linear_x)} m/s</span>
        </div>
        <div class="value-item">
          <span class="value-label">旋回</span>
          <span class="value-num">${formatNum(data.angular_z)} rad/s</span>
        </div>
      </div>
    `;
  }

  // ---------------------------------------------------------------------------
  // #drawEmpty — 初期状態の描画
  // ---------------------------------------------------------------------------
  #drawEmpty() {
    const ctx = this.#ctx;
    if (!ctx) return;
    const w = this.#canvas.width;
    const h = this.#canvas.height;
    ctx.fillStyle = "#0a1a0a";
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#555";
    ctx.font = "12px monospace";
    ctx.textAlign = "center";
    ctx.fillText("Waiting for odometry data...", w / 2, h / 2);
  }
}
