// =============================================================================
// robotStore.ts — ロボットの状態を管理するストア
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、アプリケーション内のロボットに関するすべての状態を管理します。
// - どんなロボットが登録されているか（robots リスト）
// - 現在どのロボットが選択されているか（selectedRobotId）
// - 各ロボットのセンサーデータ（latestSensorData）
// - 緊急停止（E-Stop）の状態
// - 最後に送った速度コマンド
//
// 【なぜこのファイルが必要？】
// ロボットの情報は、ダッシュボード、手動操作画面、センサー表示画面など
// 複数のページ/コンポーネントで必要です。
// Zustandストアに集約することで、どこからでも同じデータにアクセスでき、
// データの一貫性が保たれます。
//
// 【authStoreとの違い】
// - authStore: persist（永続化）ミドルウェアを使用 → ページリロードでも状態維持
// - robotStore: persistを使わない → ページリロードで状態リセット
//   （センサーデータなどリアルタイムデータは保存する必要がないため）
// =============================================================================

// ---------------------------------------------------------------------------
// 【インポート】
// ---------------------------------------------------------------------------

// create: Zustandストアを作成する関数
// 前のファイル（authStore.ts）でも使った、状態の入れ物を作る関数
import { create } from "zustand";

// Robot: ロボットの情報を表す型（名前、ID、接続状態など）
// SensorData: センサーデータの型（sensor_type、値、タイムスタンプなど）
// VelocityCommand: ロボットに送る速度指令の型（前進速度、回転速度など）
// 「type」キーワードで型のみインポート — 実行時にはコードに含まれない
import type { Robot, SensorData, VelocityCommand } from "@/types";

// ---------------------------------------------------------------------------
// 【インターフェース定義】RobotState — ロボットストアの設計図
// ---------------------------------------------------------------------------
// ストアが持つデータ（状態）と、それを操作する関数（アクション）を定義
// ---------------------------------------------------------------------------
interface RobotState {
  // --- データ（状態） ---

  // robots: 登録されているすべてのロボットのリスト
  // Robot[] は「Robotオブジェクトの配列」を意味する
  // 例: [{ id: "r1", name: "ロボA", ... }, { id: "r2", name: "ロボB", ... }]
  robots: Robot[];

  // selectedRobotId: 現在ユーザーが選択しているロボットのID
  // nullの場合は何も選択されていない状態
  selectedRobotId: string | null;

  // latestSensorData: 各ロボットの最新センサーデータ
  //
  // 【Record型の説明（初心者向け）】
  // Record<キーの型, 値の型> は「辞書」のような型です
  // ここでは二重の Record:
  //   外側のキー = ロボットID（例: "robot-1"）
  //   内側のキー = センサータイプ（例: "lidar", "camera"）
  //   値 = SensorData オブジェクト
  //
  // 例:
  // {
  //   "robot-1": { "lidar": { sensor_type: "lidar", ... }, "camera": { ... } },
  //   "robot-2": { "imu": { sensor_type: "imu", ... } }
  // }
  latestSensorData: Record<string, Record<string, SensorData>>;

  // isEStopActive: 緊急停止（Emergency Stop）が有効かどうか
  // true = 緊急停止中（ロボットが停止している）
  // false = 通常運転中
  // 安全のため、緊急停止ボタンはロボット操作画面で常に表示される
  isEStopActive: boolean;

  // lastCommand: 最後にロボットに送った速度コマンド
  // UIで「現在の速度」を表示するために使う
  // null = まだコマンドを送っていない、または停止中
  lastCommand: VelocityCommand | null;

  // --- アクション（状態を変更する関数） ---

  // setRobots: サーバーから取得したロボットリストで一括更新する
  setRobots: (robots: Robot[]) => void;

  // selectRobot: ユーザーが操作対象のロボットを選択/解除する
  selectRobot: (id: string | null) => void;

  // updateRobotState: 特定ロボットの情報を部分的に更新する
  // Partial<Robot>: Robotの一部のプロパティだけ渡せばOK
  updateRobotState: (id: string, patch: Partial<Robot>) => void;

  // updateSensorData: 特定ロボットのセンサーデータを更新する
  // WebSocketなどからリアルタイムデータが届いたときに使う
  updateSensorData: (robotId: string, data: SensorData) => void;

  // setEStop: 緊急停止の状態を切り替える
  setEStop: (active: boolean) => void;

  // setLastCommand: 最後に送った速度コマンドを記録する（nullで停止を表す）
  setLastCommand: (cmd: VelocityCommand | null) => void;

  // selectedRobot: 現在選択されているロボットオブジェクトを取得するヘルパー
  // これは「計算された値」— selectedRobotIdを元にrobotsリストから検索する
  selectedRobot: () => Robot | undefined;
}

// ---------------------------------------------------------------------------
// 【ストアの作成】useRobotStore — ロボット状態を管理するZustandストア
// ---------------------------------------------------------------------------
//
// 【authStoreとの構造の違い】
// - authStoreは create<型>()(persist((set, get) => ({...}), {...}))
//   → persistミドルウェアでlocalStorageに永続化
// - robotStoreは create<型>()((set, get) => ({...}))
//   → persistなし（リアルタイムデータなので永続化不要）
//
// 【コンポーネントでの使い方】
// const robots = useRobotStore((s) => s.robots);           // ロボットリスト取得
// const selectRobot = useRobotStore((s) => s.selectRobot); // アクション取得
// ---------------------------------------------------------------------------
export const useRobotStore = create<RobotState>()((set, get) => ({
  // --- 初期状態 ---
  // アプリ起動時は、ロボットのデータはまだサーバーから取得していない
  robots: [],              // 空のロボットリスト
  selectedRobotId: null,   // 何も選択されていない
  latestSensorData: {},    // センサーデータなし（空のオブジェクト）
  isEStopActive: false,    // 緊急停止は無効
  lastCommand: null,       // コマンド未送信

  // -------------------------------------------------------------------
  // 【アクション: setRobots】ロボット一覧を設定する
  // -------------------------------------------------------------------
  // サーバーからロボットリストを取得したとき、ストア内のリストを丸ごと置き換える
  // set({ robots }) は set({ robots: robots }) の省略記法
  setRobots: (robots) => set({ robots }),

  // -------------------------------------------------------------------
  // 【アクション: selectRobot】ロボットを選択する
  // -------------------------------------------------------------------
  // ユーザーがUI上でロボットをクリックしたとき呼ばれる
  // null を渡すと選択解除になる
  selectRobot: (id) => set({ selectedRobotId: id }),

  // -------------------------------------------------------------------
  // 【アクション: updateRobotState】ロボット情報を部分更新する
  // -------------------------------------------------------------------
  // 特定のロボットの一部のプロパティだけを更新したいときに使う
  //
  // 【Partial<Robot> とは？】
  // TypeScriptの Partial<T> は、Tのすべてのプロパティをオプション（省略可能）にする
  // 例: Robot が { id: string, name: string, status: string } なら
  //     Partial<Robot> は { id?: string, name?: string, status?: string }
  //     → 一部だけ指定すればOK: { status: "connected" }
  //
  // 【set((state) => ({...})) — 関数形式のset】
  // 現在の状態 (state) を元に新しい状態を計算する必要があるため、
  // set に関数を渡している（現在のrobots配列が必要だから）
  //
  // 【map() メソッドの説明】
  // 配列の各要素に対して関数を実行し、新しい配列を返す
  // IDが一致するロボットだけ情報を更新し、他はそのまま返す
  //
  // 【三項演算子 条件 ? 値A : 値B】
  // r.id === id ? { ...r, ...patch } : r
  // → IDが一致 → スプレッド構文でpatchの値を上書きした新オブジェクト
  // → IDが不一致 → そのまま r を返す
  updateRobotState: (id, patch) =>
    set((state) => ({
      robots: state.robots.map((r) =>
        r.id === id ? { ...r, ...patch } : r
      ),
    })),

  // -------------------------------------------------------------------
  // 【アクション: updateSensorData】センサーデータを更新する
  // -------------------------------------------------------------------
  // WebSocketなどからリアルタイムデータが届いたとき、該当ロボットのデータを更新
  //
  // 【スプレッド構文（...）の説明 — 初心者向け】
  // ... は「展開」する構文で、オブジェクトや配列のコピーを作るときに使います
  // 例: const old = { a: 1, b: 2 };
  //     const updated = { ...old, b: 3 };  // → { a: 1, b: 3 }
  //     ↑ oldの内容をコピーしつつ、bだけ上書き
  //
  // 【この処理の流れ】
  // 1. state.latestSensorData 全体をコピー（他のロボットのデータを保持）
  // 2. [robotId] のデータだけ更新:
  //    - 既存のセンサーデータをコピー（|| {} で存在しない場合は空オブジェクト）
  //    - [data.sensor_type] をキーにして新しい SensorData を保存
  //
  // 【[robotId] と [data.sensor_type] — 計算されたプロパティ名】
  // オブジェクトのキーに変数の値を使いたいとき、[] で囲む
  // 例: const key = "temperature";
  //     const obj = { [key]: 25 };  // → { temperature: 25 }
  updateSensorData: (robotId, data) =>
    set((state) => ({
      latestSensorData: {
        // 既存のすべてのロボットのセンサーデータをコピー
        ...state.latestSensorData,
        // 指定されたロボットIDのデータだけ更新
        [robotId]: {
          // そのロボットの既存データをコピー（なければ空オブジェクト）
          ...(state.latestSensorData[robotId] || {}),
          // sensor_type をキーにして新データを保存
          [data.sensor_type]: data,
        },
      },
    })),

  // -------------------------------------------------------------------
  // 【アクション: setEStop】緊急停止の状態を変更する
  // -------------------------------------------------------------------
  // 緊急停止ボタンが押された/解除されたときに呼ばれる
  // true: ロボットを緊急停止させる
  // false: 緊急停止を解除する
  setEStop: (active) => set({ isEStopActive: active }),

  // -------------------------------------------------------------------
  // 【アクション: setLastCommand】最後のコマンドを記録する
  // -------------------------------------------------------------------
  // UIでの表示用（「現在の速度: 前進 0.5 m/s」など）
  // null を渡すと「コマンドなし」= 停止状態
  setLastCommand: (cmd) => set({ lastCommand: cmd }),

  // -------------------------------------------------------------------
  // 【ヘルパー: selectedRobot】選択中のロボットオブジェクトを返す
  // -------------------------------------------------------------------
  // selectedRobotId（文字列ID）から、対応する Robot オブジェクトを検索して返す
  //
  // 【get() の使い方】
  // get() でストアの現在の状態全体を取得する
  // ここでは robots 配列と selectedRobotId の両方が必要なので、まとめて取得
  //
  // 【find() メソッド】
  // 配列から条件に一致する最初の要素を返す。見つからなければ undefined
  // 例: [1, 2, 3].find(x => x === 2) → 2
  selectedRobot: () => {
    const state = get();
    return state.robots.find((r) => r.id === state.selectedRobotId);
  },
}));
