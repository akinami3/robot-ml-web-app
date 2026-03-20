// =============================================================================
// Step 4: IMU チャート — 簡易折れ線グラフ
// =============================================================================
//
// 【このファイルの概要】
// IMU（慣性計測装置）の6軸データを折れ線グラフで表示する。
// 直近 N 件のデータをリングバッファに保存し、Canvas に描画する。
//
// 【リングバッファ（Ring Buffer / Circular Buffer）とは？】
// 固定サイズの配列で、末尾に達したら先頭に戻ってデータを上書きする。
// 常に最新 N 件のデータだけを保持し、メモリを節約できる。
//
// ここでは JavaScript の Array + shift/push で簡易実装する。
//
// =============================================================================

export class ImuChart {
  #canvas;
  #ctx;
  #width;
  #height;
  #maxPoints;
  #data;

  // 描画する軸の色設定
  static CHANNELS = [
    { key: "accel_x", label: "Ax", color: "#ff6b6b" },
    { key: "accel_y", label: "Ay", color: "#ffd700" },
    { key: "accel_z", label: "Az", color: "#00d4ff" },
    { key: "gyro_x",  label: "Gx", color: "#ff6bff" },
    { key: "gyro_y",  label: "Gy", color: "#6bff6b" },
    { key: "gyro_z",  label: "Gz", color: "#ffaa00" },
  ];

  // ---------------------------------------------------------------------------
  // constructor
  // ---------------------------------------------------------------------------
  constructor(canvasId, options = {}) {
    this.#canvas = document.getElementById(canvasId);
    if (!this.#canvas) return;

    this.#ctx = this.#canvas.getContext("2d");
    this.#width = options.width || 300;
    this.#height = options.height || 180;
    this.#maxPoints = options.maxPoints || 100;

    this.#canvas.width = this.#width;
    this.#canvas.height = this.#height;

    // 各チャネルのデータ配列を初期化
    // 【Object.fromEntries + map パターン】
    // 配列をオブジェクトに変換する。
    // [["accel_x", []], ["accel_y", []]] → { accel_x: [], accel_y: [] }
    this.#data = {};
    for (const ch of ImuChart.CHANNELS) {
      this.#data[ch.key] = [];
    }

    this.#drawBackground();
  }

  // ---------------------------------------------------------------------------
  // update — 新しい IMU データを追加して再描画
  // ---------------------------------------------------------------------------
  update(imuData) {
    if (!this.#ctx) return;

    // 各チャネルにデータを追加
    for (const ch of ImuChart.CHANNELS) {
      const value = imuData[ch.key];
      if (value !== undefined) {
        const arr = this.#data[ch.key];
        arr.push(value);
        // maxPoints を超えたら古いデータを削除（リングバッファ的動作）
        if (arr.length > this.#maxPoints) {
          arr.shift(); // 先頭を削除（O(n) だが少量なので問題なし）
        }
      }
    }

    this.#draw();
  }

  // ---------------------------------------------------------------------------
  // #draw — グラフを再描画
  // ---------------------------------------------------------------------------
  #draw() {
    const ctx = this.#ctx;
    const w = this.#width;
    const h = this.#height;

    // 背景クリア
    this.#drawBackground();

    // --- ゼロライン ---
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 0.5;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();
    ctx.setLineDash([]);

    // --- 各チャネルの折れ線を描画 ---
    //
    // 【加速度と角速度のスケール】
    // 加速度: -12 ~ 12 m/s²（重力加速度 9.81 を含む）
    // 角速度: -2 ~ 2 rad/s
    // 2つのグループに分けてスケーリングする。
    for (const ch of ImuChart.CHANNELS) {
      const arr = this.#data[ch.key];
      if (arr.length < 2) continue;

      const isAccel = ch.key.startsWith("accel");
      const maxVal = isAccel ? 12.0 : 2.0;

      ctx.strokeStyle = ch.color;
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.8;
      ctx.beginPath();

      for (let i = 0; i < arr.length; i++) {
        const x = (i / this.#maxPoints) * w;
        // 値を画面の中央を基準にマッピング
        const normalized = arr[i] / maxVal; // -1 ~ 1 の範囲に
        const y = h / 2 - normalized * (h / 2 - 10);

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
      ctx.globalAlpha = 1.0;
    }

    // --- 凡例（レジェンド） ---
    this.#drawLegend(ctx);
  }

  // ---------------------------------------------------------------------------
  // #drawLegend — 凡例を描画
  // ---------------------------------------------------------------------------
  #drawLegend(ctx) {
    const fontSize = 9;
    ctx.font = `${fontSize}px monospace`;
    let x = 4;
    const y = this.#height - 4;

    for (const ch of ImuChart.CHANNELS) {
      ctx.fillStyle = ch.color;
      ctx.fillRect(x, y - fontSize + 2, 8, 8);
      x += 10;
      ctx.fillStyle = "#888";
      ctx.fillText(ch.label, x, y);
      x += ctx.measureText(ch.label).width + 6;
    }
  }

  // ---------------------------------------------------------------------------
  // #drawBackground
  // ---------------------------------------------------------------------------
  #drawBackground() {
    const ctx = this.#ctx;
    ctx.fillStyle = "#0a0a1a";
    ctx.fillRect(0, 0, this.#width, this.#height);
  }
}
