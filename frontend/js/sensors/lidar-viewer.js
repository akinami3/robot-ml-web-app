// =============================================================================
// Step 4: LiDAR ビューア — Canvas 2D によるリアルタイム点群描画
// =============================================================================
//
// 【Canvas 2D API とは？】
// HTML の <canvas> 要素に2Dグラフィックスを描画するAPI。
// ゲーム、グラフ、データ可視化などに使われる。
//
// 基本的な使い方:
//   const canvas = document.getElementById("myCanvas");
//   const ctx = canvas.getContext("2d");  // 2D描画コンテキストを取得
//   ctx.fillRect(10, 10, 50, 50);        // 矩形を描画
//
// 【座標系】
// Canvas の座標系は左上が原点 (0,0):
//   → X軸は右方向が正
//   ↓ Y軸は下方向が正
// ロボットの座標系は:
//   → X軸は前方が正
//   ↑ Y軸は左方が正
// 変換が必要！
//
// 【極座標 → 直交座標変換】
// LiDARデータは極座標 (angle, range) で来る。
// Canvas に描画するには直交座標 (x, y) に変換する:
//   x = range × cos(angle)
//   y = range × sin(angle)
//
// =============================================================================

export class LidarViewer {
  #canvas;
  #ctx;
  #size;

  // ---------------------------------------------------------------------------
  // constructor — キャンバスの初期化
  // ---------------------------------------------------------------------------
  //
  // 【引数】
  // canvasId: <canvas> 要素のID
  // size: キャンバスの描画解像度（ピクセル）
  constructor(canvasId, size = 300) {
    this.#canvas = document.getElementById(canvasId);
    if (!this.#canvas) return;

    this.#ctx = this.#canvas.getContext("2d");
    this.#size = size;

    // 描画解像度を設定
    // 【width/height 属性 vs CSS サイズ】
    // canvas.width = 描画バッファの解像度（ピクセル数）
    // CSS width = 表示サイズ
    // 両方設定してクリアな表示にする。
    this.#canvas.width = size;
    this.#canvas.height = size;

    this.#drawBackground();
  }

  // ---------------------------------------------------------------------------
  // update — LiDAR データを受け取って描画
  // ---------------------------------------------------------------------------
  //
  // 【描画の流れ】
  // 1. 背景をクリア（前回の描画を消す）
  // 2. グリッド（同心円）を描画
  // 3. レーザーの点を1つずつ極座標→直交座標変換して描画
  // 4. ロボットの位置（中心）を描画
  update(data) {
    if (!this.#ctx || !data.ranges) return;

    const ctx = this.#ctx;
    const center = this.#size / 2;
    const maxRange = data.max_range || 10.0;

    // スケール: メートル → ピクセル
    // 描画領域 = size の半分（中心から端まで）
    const scale = (this.#size / 2 - 10) / maxRange;

    // --- 1. 背景クリア ---
    this.#drawBackground();

    // --- 2. グリッド描画（同心円） ---
    this.#drawGrid(ctx, center, scale, maxRange);

    // --- 3. LiDAR 点群を描画 ---
    //
    // 【beginPath / arc / fill パターン】
    // Canvas で点（円）を描くには:
    //   ctx.beginPath();    // 新しいパスを開始
    //   ctx.arc(x, y, r, 0, 2π);  // 円を定義
    //   ctx.fill();         // 塗りつぶし
    ctx.fillStyle = "#00ff88";

    const ranges = data.ranges;
    const angles = data.angles;
    const numPoints = Math.min(ranges.length, angles.length);

    for (let i = 0; i < numPoints; i++) {
      const r = ranges[i];
      if (r < (data.min_range || 0.1) || r > maxRange) continue;

      // 極座標→直交座標変換
      const angle = angles[i];
      const x = center + r * Math.cos(angle) * scale;
      const y = center - r * Math.sin(angle) * scale; // Y軸反転（Canvas座標系）

      ctx.beginPath();
      ctx.arc(x, y, 1.5, 0, Math.PI * 2);
      ctx.fill();
    }

    // --- 4. ロボット位置（中心の三角形） ---
    this.#drawRobot(ctx, center);
  }

  // ---------------------------------------------------------------------------
  // プライベートメソッド
  // ---------------------------------------------------------------------------

  #drawBackground() {
    const ctx = this.#ctx;
    ctx.fillStyle = "#0a0a1a";
    ctx.fillRect(0, 0, this.#size, this.#size);
  }

  // #drawGrid — 距離を示す同心円を描画
  //
  // 【setLineDash とは？】
  // 線を破線にする。[5, 5] は「5px描画, 5px空ける」のパターン。
  #drawGrid(ctx, center, scale, maxRange) {
    ctx.strokeStyle = "#1a3a2a";
    ctx.lineWidth = 0.5;
    ctx.setLineDash([3, 3]);

    // 1m 刻みの同心円
    for (let d = 1; d <= maxRange; d += 1) {
      const r = d * scale;
      ctx.beginPath();
      ctx.arc(center, center, r, 0, Math.PI * 2);
      ctx.stroke();
    }

    // 十字線
    ctx.beginPath();
    ctx.moveTo(center, 0);
    ctx.lineTo(center, this.#size);
    ctx.moveTo(0, center);
    ctx.lineTo(this.#size, center);
    ctx.stroke();

    ctx.setLineDash([]); // 破線をリセット

    // 距離ラベル
    ctx.fillStyle = "#334433";
    ctx.font = "10px monospace";
    ctx.fillText("1m", center + 1 * scale + 2, center - 2);
    ctx.fillText("3m", center + 3 * scale + 2, center - 2);
    ctx.fillText("5m", center + 5 * scale + 2, center - 2);
  }

  // #drawRobot — ロボットを三角形で描画
  #drawRobot(ctx, center) {
    ctx.fillStyle = "#00d4ff";
    ctx.beginPath();
    ctx.moveTo(center + 8, center);     // 前方（右向き）
    ctx.lineTo(center - 5, center - 5); // 左後
    ctx.lineTo(center - 5, center + 5); // 右後
    ctx.closePath();
    ctx.fill();
  }
}
