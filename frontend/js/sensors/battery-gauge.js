// =============================================================================
// Step 4: バッテリーゲージ — SVG による円形ゲージ
// =============================================================================
//
// 【SVG（Scalable Vector Graphics）とは？】
// XMLベースのベクター画像フォーマット。HTMLに直接埋め込める。
// Canvas との違い:
//   - Canvas: ピクセル単位の描画（ラスタ）。アニメーション向き。
//   - SVG: 図形をオブジェクトとして定義（ベクタ）。UIパーツ向き。
//
// ここでは SVG の <circle> + stroke-dasharray でリングゲージを実現する。
//
// 【stroke-dasharray/stroke-dashoffset トリック】
// 円の周囲長（circumference = 2πr）を dasharray に設定し、
// dashoffset で「描画しない部分」の長さを指定する。
// これにより、円弧の一部だけが描画される → 進捗バーになる。
//
// =============================================================================

export class BatteryGauge {
  #container;
  #percentEl;
  #voltageEl;
  #tempEl;
  #circle;
  #circumference;

  constructor(containerId) {
    this.#container = document.getElementById(containerId);
    if (!this.#container) return;

    // SVGの半径と周囲長
    const radius = 50;
    this.#circumference = 2 * Math.PI * radius;

    // SVG を生成して DOM に挿入
    this.#container.innerHTML = this.#createSVG(radius);

    // 要素への参照を取得
    this.#circle = this.#container.querySelector(".gauge-circle");
    this.#percentEl = this.#container.querySelector(".gauge-percent");
    this.#voltageEl = this.#container.querySelector(".gauge-voltage");
    this.#tempEl = this.#container.querySelector(".gauge-temp");

    // 初期状態
    if (this.#circle) {
      this.#circle.style.strokeDasharray = `${this.#circumference}`;
      this.#circle.style.strokeDashoffset = `${this.#circumference}`;
    }
  }

  // ---------------------------------------------------------------------------
  // update — バッテリーデータを受け取って表示更新
  // ---------------------------------------------------------------------------
  update(data) {
    if (!this.#container) return;

    const pct = data.percentage || 0;
    const voltage = data.voltage || 0;
    const temp = data.temperature || 0;

    // パーセント表示
    if (this.#percentEl) {
      this.#percentEl.textContent = `${pct.toFixed(0)}%`;
    }

    // 電圧と温度
    if (this.#voltageEl) this.#voltageEl.textContent = `${voltage.toFixed(1)}V`;
    if (this.#tempEl) this.#tempEl.textContent = `${temp.toFixed(1)}°C`;

    // 円弧の更新
    // offset = circumference × (1 - 進捗率)
    // 進捗率 0% → offset = circumference（全く描画しない）
    // 進捗率 100% → offset = 0（全て描画）
    if (this.#circle) {
      const offset = this.#circumference * (1 - pct / 100);
      this.#circle.style.strokeDashoffset = `${offset}`;

      // 残量に応じて色を変える
      if (pct > 50) {
        this.#circle.style.stroke = "#28a745";
      } else if (pct > 20) {
        this.#circle.style.stroke = "#ffc107";
      } else {
        this.#circle.style.stroke = "#dc3545";
      }
    }
  }

  // ---------------------------------------------------------------------------
  // #createSVG — SVG の HTML 文字列を生成
  // ---------------------------------------------------------------------------
  //
  // 【SVG の構造】
  // <svg viewBox="0 0 120 140">  ← 仮想座標系
  //   <circle>                   ← 背景リング（灰色）
  //   <circle class="gauge">     ← 進捗リング（色が変わる）
  //   <text>                     ← パーセント表示
  // </svg>
  //
  // 【viewBox とは？】
  // SVG 内部の座標系。実際の表示サイズに関係なく、
  // この座標系内のサイズで図形を配置する。
  // CSS で width:100% にすると、コンテナに合わせて自動拡縮される。
  #createSVG(radius) {
    const cx = 60;
    const cy = 60;
    const size = 120;

    return `
      <svg viewBox="0 0 ${size} ${size + 30}" style="width:100%; max-width:200px; display:block; margin:0 auto;">
        <!-- 背景リング -->
        <circle cx="${cx}" cy="${cy}" r="${radius}"
          fill="none" stroke="#1a3a2a" stroke-width="8" />
        <!-- 進捗リング -->
        <circle class="gauge-circle" cx="${cx}" cy="${cy}" r="${radius}"
          fill="none" stroke="#28a745" stroke-width="8"
          stroke-linecap="round"
          transform="rotate(-90 ${cx} ${cy})"
          style="transition: stroke-dashoffset 0.5s ease, stroke 0.5s ease;" />
        <!-- パーセント表示 -->
        <text class="gauge-percent" x="${cx}" y="${cy + 5}"
          text-anchor="middle" fill="#00d4ff"
          font-size="22" font-weight="bold" font-family="monospace">
          --%
        </text>
        <!-- 電圧 -->
        <text class="gauge-voltage" x="${cx - 20}" y="${size + 16}"
          text-anchor="middle" fill="#888" font-size="11" font-family="monospace">
          --V
        </text>
        <!-- 温度 -->
        <text class="gauge-temp" x="${cx + 20}" y="${size + 16}"
          text-anchor="middle" fill="#888" font-size="11" font-family="monospace">
          --°C
        </text>
      </svg>
    `;
  }
}
