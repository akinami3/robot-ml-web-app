// =============================================================================
// SensorViewPage.tsx — センサービューページ
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、ロボットのセンサーデータをリアルタイムで表示するページです。
// LiDAR（レーザー距離センサー）、IMU（慣性計測装置）、オドメトリ（走行距離計）、
// バッテリー情報の4種類のセンサーデータを可視化します。
//
// 【このページの役割】
// - ユーザーがロボットを選択すると、そのロボットのセンサーデータが表示される
// - 各センサーデータは専用のコンポーネント（LiDARViewer、IMUChart等）で可視化
// - データはZustandストア（robotStore）からリアルタイムで取得される
//
// 【主な技術的ポイント】
// - Zustandストアからの状態読み取り（useRobotStore）
// - 型アサーション（as）を使ったデータの型指定
// - Optional Chaining（?.）で安全にプロパティアクセス
// - Nullish Coalescing（??）でデフォルト値を設定
// - useState で IMU の履歴データを保持
// =============================================================================

// ---------------------------------------------------------------------------
// インポート部分
// ---------------------------------------------------------------------------

// 【useState】Reactの基本フック。コンポーネント内で「状態（state）」を管理する。
// 状態が変わると、コンポーネントが自動的に再レンダリング（再描画）される。
// ここではIMUセンサーの履歴データを保持するために使う。
import { useState } from "react";

// 【useRobotStore】Zustand（状態管理ライブラリ）で作成したカスタムストア。
// ロボットの一覧、選択中のロボットID、最新センサーデータなど、
// アプリ全体で共有したいロボット関連の状態を管理している。
// 引数にセレクター関数 (s) => s.xxx を渡すことで、必要な部分だけを取り出せる。
import { useRobotStore } from "@/stores/robotStore";

// 【LiDARViewer】LiDARセンサーのデータを視覚的に表示するコンポーネント。
// LiDAR = Light Detection And Ranging（光検出と測距）。
// レーザーを照射して周囲の障害物までの距離を測定するセンサー。
// ranges配列（各方向への距離データ）を受け取って描画する。
import { LiDARViewer } from "@/components/sensors/LiDARViewer";

// 【IMUChart】IMUセンサーのデータをグラフ（チャート）で表示するコンポーネント。
// IMU = Inertial Measurement Unit（慣性計測装置）。
// 加速度（ax, ay, az）とジャイロ（角速度: gx, gy, gz）を測定する。
// 時系列のデータ配列を受け取り、折れ線グラフなどで表示する。
import { IMUChart } from "@/components/sensors/IMUChart";

// 【OdometryDisplay】オドメトリ（走行距離計）データを表示するコンポーネント。
// オドメトリ = ロボットの位置(x, y)、向き(theta)、速度を推定するシステム。
// 車輪の回転数などから現在位置を計算する。
import { OdometryDisplay } from "@/components/sensors/OdometryDisplay";

// 【BatteryGauge】バッテリー残量をゲージ（メーター）で表示するコンポーネント。
// パーセンテージ、電圧、充電中かどうかの情報を表示する。
import { BatteryGauge } from "@/components/sensors/BatteryGauge";

// 【Select】HTMLの<select>要素をスタイリングしたUIコンポーネント。
// ドロップダウンメニュー（選択肢リスト）を表示するために使用する。
// ここではロボットの選択用ドロップダウンに使う。
import { Select } from "@/components/ui/primitives";

// =============================================================================
// SensorViewPage コンポーネント（メインのページコンポーネント）
// =============================================================================
//
// 【コンポーネントとは？】
// Reactでは、UIの部品を「コンポーネント」と呼ぶ。
// 関数として定義し、JSX（HTMLに似た構文）を返す。
// このコンポーネントはページ全体を構成する「ページコンポーネント」。
//
// 【export function とは？】
// export: 他のファイルからこの関数を使えるようにする（公開する）
// function: 関数を定義するキーワード
// SensorViewPage: 関数名（Reactコンポーネントは大文字始まり）
// =============================================================================
export function SensorViewPage() {
  // ---------------------------------------------------------------------------
  // Zustandストアからの状態取得
  // ---------------------------------------------------------------------------
  //
  // 【useRobotStore((s) => s.xxx) のパターン】
  // useRobotStore はZustandのフック。引数にセレクター関数を渡す。
  // (s) => s.robots は「ストアの状態 s から robots プロパティだけを取り出す」という意味。
  // こうすることで、robots が変わった時だけこのコンポーネントが再レンダリングされる。
  // （他の状態が変わっても無駄に再描画されない = パフォーマンス最適化）

  // robots: 登録されている全ロボットの配列
  const robots = useRobotStore((s) => s.robots);

  // selectedId: 現在選択されているロボットのID（未選択ならnull）
  const selectedId = useRobotStore((s) => s.selectedRobotId);

  // setSelected: ロボットを選択するための関数（IDを渡すとそのロボットが選択される）
  const setSelected = useRobotStore((s) => s.selectRobot);

  // latestSensor: 各ロボットの最新センサーデータ（ロボットIDをキーとした辞書型）
  const latestSensor = useRobotStore((s) => s.latestSensorData);

  // ---------------------------------------------------------------------------
  // 選択中ロボットのセンサーデータを取得
  // ---------------------------------------------------------------------------
  //
  // 【三項演算子（条件 ? 値A : 値B）】
  // selectedId が存在する場合 → latestSensor[selectedId] を取得
  // selectedId が null/undefined の場合 → 空オブジェクト {} を使用
  //
  // 【?? 演算子（Nullish Coalescing / ヌリッシュ合体演算子）】
  // 左側が null または undefined の場合に、右側の値を使う。
  // latestSensor[selectedId] ?? {} は「データがなければ空オブジェクト」という意味。
  // || (OR演算子) と似ているが、?? は 0 や "" を有効な値として扱う点が異なる。
  const data = selectedId ? latestSensor[selectedId] ?? {} : {};

  // ---------------------------------------------------------------------------
  // 型アサーション（as）でセンサーデータの型を明示的に指定
  // ---------------------------------------------------------------------------
  //
  // 【型アサーション（Type Assertion）とは？】
  // TypeScriptの機能で、「この値はこの型だよ」とコンパイラに教える。
  // data.lidar はany型だが、実際にはranges配列を持つオブジェクトなので、
  // as { ranges?: number[] } | undefined と書いて型を明示する。
  //
  // 【| undefined とは？】
  // TypeScriptのユニオン型。「この型 OR undefined（値なし）」を意味する。
  // センサーデータが存在しない可能性があるため、undefinedも許容する。

  // lidar: LiDARセンサーデータ（ranges = 各方向への距離の配列）
  const lidar = data.lidar as { ranges?: number[] } | undefined;

  // imu: IMUセンサーデータ
  // ax, ay, az = X/Y/Z軸の加速度（acceleration）
  // gx, gy, gz = X/Y/Z軸の角速度（gyroscope）
  const imu = data.imu as { ax?: number; ay?: number; az?: number; gx?: number; gy?: number; gz?: number } | undefined;

  // odom: オドメトリデータ
  // x, y = ロボットの推定位置座標
  // theta = ロボットの向き（ラジアン）
  // linear_velocity = 直線速度（m/s）
  // angular_velocity = 角速度（rad/s）
  const odom = data.odometry as { x?: number; y?: number; theta?: number; linear_velocity?: number; angular_velocity?: number } | undefined;

  // battery: バッテリー情報
  // percentage = 残量パーセント
  // voltage = 電圧（ボルト）
  // is_charging = 充電中かどうか（true/false）
  const battery = data.battery as { percentage?: number; voltage?: number; is_charging?: boolean } | undefined;

  // ---------------------------------------------------------------------------
  // IMU履歴データの管理
  // ---------------------------------------------------------------------------
  //
  // 【useState でIMU履歴を保持する理由】
  // IMUデータはリアルタイムで次々届くが、グラフ表示には過去のデータも必要。
  // 配列を state として保持し、新しいデータが来たらpushで追加する。
  //
  // 【useState<Array<...>>([])】
  // <Array<...>> はジェネリクスで、配列の要素の型を指定。
  // 初期値 [] は空の配列。
  // imuHistory: 現在のIMU履歴データの配列
  // ※注意: useState の第二返り値（setter）を使わず、配列を直接操作（push/splice）している。
  //   これはReactのベストプラクティスではないが、パフォーマンス的に有利な場合がある。
  //   （毎フレーム新しい配列を作るとGCが多発するため）

  // Keep IMU history in state
  const [imuHistory] = useState<Array<{ t: number; ax?: number; ay?: number; az?: number; gx?: number; gy?: number; gz?: number }>>([]);

  // 【IMUデータが存在する場合、履歴に追加する処理】
  // imu が truthy（nullでもundefinedでもない）なら、タイムスタンプ付きで追加。
  // Date.now() は現在のミリ秒タイムスタンプを返す。
  // ...imu はスプレッド演算子で、imuオブジェクトの全プロパティを展開する。
  // 例: { t: 1700000000000, ax: 0.1, ay: 0.2, az: 9.8, gx: 0, gy: 0, gz: 0 }
  if (imu) {
    imuHistory.push({ t: Date.now(), ...imu });
    // 履歴が200件を超えたら、古いデータを削除して200件に維持する
    // splice(0, 削除数) で配列の先頭から指定数だけ削除する
    if (imuHistory.length > 200) imuHistory.splice(0, imuHistory.length - 200);
  }

  // ---------------------------------------------------------------------------
  // JSX（レンダリング部分）
  // ---------------------------------------------------------------------------
  //
  // 【JSXとは？】
  // JavaScriptの中にHTMLのような構文を書ける拡張構文。
  // Reactコンポーネントのreturn文でUIの構造を定義する。
  // className はHTMLのclass属性の代わり（classはJSの予約語なので）。
  //
  // 【Tailwind CSSのクラス名】
  // space-y-6: 子要素間に縦方向の余白（1.5rem = 24px）
  // flex: フレックスボックスレイアウト
  // items-center: 垂直方向の中央揃え
  // justify-between: 左右に分散配置
  // text-2xl: テキストサイズ（1.5rem）
  // font-bold: 太字
  // grid: CSSグリッドレイアウト
  // gap-4: グリッドアイテム間の隙間（1rem）
  // md:grid-cols-2: 中サイズ画面以上で2列レイアウト
  // xl:grid-cols-3: 大サイズ画面以上で3列レイアウト
  return (
    <div className="space-y-6">
      {/* ヘッダー部分：タイトルとロボット選択ドロップダウン */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Sensor View</h1>

        {/* 【Select コンポーネント】ロボット選択用ドロップダウン */}
        {/* value: 現在選択されている値 */}
        {/* onChange: 選択が変わった時に呼ばれる関数 */}
        {/* e.target.value: 選択された<option>のvalue属性の値 */}
        {/* || null: 空文字列("")の場合はnullに変換（「未選択」状態にする） */}
        <Select
          value={selectedId ?? ""}
          onChange={(e) => setSelected(e.target.value || null)}
          className="w-48"
        >
          <option value="">Select robot</option>
          {/* 【.map()】配列の各要素に対して処理を行い、新しい配列を返す */}
          {/* ここではrobots配列の各ロボットに対して<option>要素を生成する */}
          {/* key={r.id}: Reactがリスト要素を効率的に管理するための一意キー */}
          {robots.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </Select>
      </div>

      {/* 【条件付きレンダリング】 */}
      {/* !selectedId: ロボットが未選択の場合 → メッセージ表示 */}
      {/* selectedId がある場合 → センサーデータのグリッド表示 */}
      {!selectedId ? (
        // ロボット未選択時のメッセージ
        <p className="text-sm text-muted-foreground">Select a robot to view sensor data.</p>
      ) : (
        // ロボット選択済み: 4つのセンサーコンポーネントをグリッドで表示
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {/* LiDARビューア: 距離データの配列を渡す */}
          {/* lidar?.ranges: Optional Chaining。lidarがundefinedなら?.以降は評価されずundefinedを返す */}
          {/* ?? []: Nullish Coalescing。undefinedなら空配列を使う */}
          <LiDARViewer ranges={lidar?.ranges ?? []} />

          {/* IMUチャート: 時系列のIMU履歴データを渡す */}
          <IMUChart data={imuHistory} />

          {/* オドメトリ表示: 位置・速度データを個別のプロパティとして渡す */}
          {/* odom?.x ?? 0: odomがundefinedならx=0、odomが存在してもxがundefinedなら0 */}
          <OdometryDisplay
            x={odom?.x ?? 0}
            y={odom?.y ?? 0}
            theta={odom?.theta ?? 0}
            linearVelocity={odom?.linear_velocity ?? 0}
            angularVelocity={odom?.angular_velocity ?? 0}
          />

          {/* バッテリーゲージ: 残量・電圧・充電状態を渡す */}
          <BatteryGauge
            percentage={battery?.percentage ?? 0}
            voltage={battery?.voltage ?? 0}
            isCharging={battery?.is_charging ?? false}
          />
        </div>
      )}
    </div>
  );
}
