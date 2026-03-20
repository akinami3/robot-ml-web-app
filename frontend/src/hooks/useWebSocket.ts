/**
 * useWebSocket.ts - WebSocketによるリアルタイムロボット通信カスタムフック
 *
 * =====================================================================
 * 📁 ファイルの概要（このファイルが何をするか）
 * =====================================================================
 * このファイルは、WebSocketを使ってロボットとリアルタイム通信を行う
 * カスタムフックを定義しています。
 *
 * 💡 WebSocket とは？
 * - HTTP通信は「リクエスト→レスポンス」の1回限りの通信ですが、
 *   WebSocketは一度接続すると、双方向でデータを送受信し続けられます
 * - チャットアプリやリアルタイムゲームなどで使われる技術です
 * - ロボットのセンサーデータをリアルタイムで受信するのに最適です
 *
 * 💡 このフックが提供する機能：
 * 1. Gatewayサーバーへの WebSocket 接続管理
 * 2. 自動再接続（接続が切れたら自動で再接続を試みる）
 * 3. Ping/Pong ハートビート（接続が生きているか定期的に確認）
 * 4. ロボットへの速度コマンド送信
 * 5. 緊急停止（E-Stop）の送信・解除
 * 6. ナビゲーション目標地点の送信
 * 7. センサーデータの受信と状態更新
 *
 * 💡 デザインパターン：
 * - Adapter パターン: WebSocket APIを使いやすいインターフェースに変換
 * - Observer パターン: メッセージを受信したら対応するストアを更新
 * - State Machine パターン: 接続状態の管理（接続中/切断/再接続中）
 * =====================================================================
 */

// === インポート部分 ===

// useCallback: 関数をメモ化（同じ関数を使い回す）するフック
// useEffect: 副作用（WebSocket接続の開始/終了）を管理するフック
// useRef: 再レンダリングを引き起こさない値の参照を保持するフック
//   - WebSocketインスタンスやタイマーIDなど、画面に表示しない値に使う
//   - useRef で保持した値（.current）が変わっても、画面は再描画されない
// useState: コンポーネントの「状態」を管理するフック
//   - 値が変わると画面が再描画される（useRefとの違い）
import { useCallback, useEffect, useRef, useState } from "react";

// useAuthStore: 認証情報（ログイン状態、アクセストークン）を管理するZustandストア
// - Zustand: Reactの状態管理ライブラリ（Redux より軽量でシンプル）
// - (s) => s.accessToken のように、必要な値だけを取り出す「セレクター」を使う
import { useAuthStore } from "@/stores/authStore";

// useRobotStore: ロボットの状態（センサーデータ、接続状態など）を管理するストア
import { useRobotStore } from "@/stores/robotStore";

// 型のインポート（type キーワード付き）
// - type をつけると「型情報だけのインポート」になり、実行時にはコードに含まれない
// - ビルドサイズの最適化に貢献します
// - Robot: ロボットの情報を表す型
// - SensorData: センサーデータを表す型
// - WSMessage: WebSocketメッセージを表す型
import type { Robot, SensorData, WSMessage } from "@/types";

// =====================================================================
// 🔧 定数の定義（設定値）
// =====================================================================
// const: 再代入できない変数宣言（定数）
// - 大文字のスネークケース（UPPER_SNAKE_CASE）は「定数」の慣例的な命名規則

// WebSocket サーバーのURL
// import.meta.env.VITE_WS_URL: 環境変数から読み込む（.envファイルに定義）
// || "ws://localhost:8080/ws": 環境変数が未設定の場合のデフォルト値
// - ws:// はWebSocketプロトコル（HTTPの ws 版）
// - wss:// はセキュアなWebSocket（HTTPSの ws 版）
const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8080/ws";

// 再接続の待機時間（ミリ秒）: 3000ms = 3秒
// - 接続が切れたとき、3秒待ってから再接続を試みる
const RECONNECT_DELAY = 3000;

// 最大再接続回数: 10回まで自動再接続を試みる
// - 無限に再接続を繰り返すのを防ぐため
// - サーバーが完全にダウンしている場合に無駄なリトライを避ける
const MAX_RECONNECT_ATTEMPTS = 10;

// Ping（ピング）の送信間隔（ミリ秒）: 30000ms = 30秒
// - 30秒ごとに「まだ接続していますよ」というメッセージを送る
// - サーバー側でタイムアウトして切断されるのを防ぐ
// - 💡 ハートビート: 心拍のように定期的に信号を送って接続の生存確認を行う仕組み
const PING_INTERVAL = 30000;

// =====================================================================
// 🌐 useWebSocket カスタムフック本体
// =====================================================================
export function useWebSocket() {
  // ─── useState: レンダリングに影響する状態の管理 ───
  // useState<型>(初期値) → [現在の値, 値を更新する関数] を返す
  // - 値が変わると、このフックを使っているコンポーネントが再レンダリングされる

  // isConnected: WebSocket が接続中かどうか（UI表示に使う）
  const [isConnected, setIsConnected] = useState(false);
  // reconnectCount: 再接続の試行回数（UIに表示してユーザーに状況を伝える）
  const [reconnectCount, setReconnectCount] = useState(0);

  // ─── useRef: レンダリングに影響しない値の管理 ───
  // useRef<型>(初期値) → { current: 値 } を返す
  // - .current プロパティで値にアクセス・更新する
  // - 値が変わっても再レンダリングされない（パフォーマンスに良い）

  // wsRef: WebSocket インスタンスへの参照
  // - WebSocket | null: WebSocketオブジェクトか null（未接続時）
  const wsRef = useRef<WebSocket | null>(null);

  // pingIntervalRef: setInterval のタイマーIDを保持
  // - ReturnType<typeof setInterval>: setInterval が返す型を自動推論
  //   → Node.js では NodeJS.Timeout、ブラウザでは number
  const pingIntervalRef = useRef<ReturnType<typeof setInterval>>();

  // reconnectTimeoutRef: setTimeout のタイマーIDを保持
  // - 再接続のタイマーをキャンセルするために保持する
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // ─── Zustandストアからの値の取得 ───
  // (s) => s.xxx という書き方は「セレクター関数」
  // - ストア全体から必要な値だけを選択的に取り出す
  // - これにより、不要な再レンダリングを防ぐ（選択した値が変わったときだけ再レンダリング）

  // アクセストークン: WebSocket接続時の認証に使用
  const accessToken = useAuthStore((s) => s.accessToken);
  // センサーデータ更新関数: 新しいセンサーデータを受信したときに呼ぶ
  const updateSensorData = useRobotStore((s) => s.updateSensorData);
  // ロボット状態更新関数: ロボットのステータスが変わったときに呼ぶ
  const updateRobotState = useRobotStore((s) => s.updateRobotState);
  // 緊急停止状態の設定関数
  const setEStop = useRobotStore((s) => s.setEStop);

  // ===================================================================
  // 🔌 connect - WebSocket接続を開始する関数
  // ===================================================================
  // 💡 WebSocket API のライフサイクル（生存期間の各段階）：
  //
  //   [1] new WebSocket(url) → 接続を開始
  //       ↓
  //   [2] ws.onopen → 接続が確立されたときに呼ばれる
  //       ↓
  //   [3] ws.onmessage → メッセージを受信するたびに呼ばれる（繰り返し）
  //       ↓
  //   [4] ws.onclose → 接続が閉じられたときに呼ばれる
  //
  //   ※ ws.onerror → エラーが発生したときに呼ばれる（どの段階でも起こりうる）
  const connect = useCallback(() => {
    // 既に接続中なら何もしない（二重接続を防止）
    // ?.（オプショナルチェーン）: wsRef.current が null でもエラーにならない
    // WebSocket.OPEN: WebSocketの接続状態を表す定数（1 = 接続中）
    // 他の状態: CONNECTING(0), CLOSING(2), CLOSED(3)
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // ─── 新しいWebSocket接続を作成 ───
    // new WebSocket(url): WebSocket接続を開始する
    // - この時点ではまだ接続は完了していない（非同期処理）
    // - 接続が完了すると ws.onopen が呼ばれる
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws; // ref に保存して、他の関数からアクセスできるようにする

    // ─── onopen: 接続が確立されたとき ───
    // WebSocketハンドシェイク（サーバーとの握手）が成功したときに実行される
    ws.onopen = () => {
      // 接続状態を true に更新（UIに反映される）
      setIsConnected(true);
      // 再接続カウントをリセット（接続成功したので）
      setReconnectCount(0);

      // ─── 認証メッセージの送信 ───
      // WebSocket 接続後、最初にアクセストークンを送ってユーザーを認証する
      // - REST APIと違い、WebSocketではヘッダーを後から送れないため、
      //   最初のメッセージとして認証情報を送るのが一般的なパターン
      if (accessToken) {
        send({ type: "auth", payload: { token: accessToken } });
      }

      // ─── Ping ハートビートの開始 ───
      // setInterval(関数, 間隔ms): 指定した間隔で関数を繰り返し実行する
      // - 30秒ごとに "ping" メッセージをサーバーに送信
      // - サーバーは "pong" を返すことで、接続が生きていることを確認
      // - 多くのプロキシやファイアウォールは、一定時間通信がないと
      //   接続を切断するため、定期的な通信が必要
      // - returnされるIDを保存して、後でclearIntervalで停止できるようにする
      pingIntervalRef.current = setInterval(() => {
        send({ type: "ping", payload: {} });
      }, PING_INTERVAL);
    };

    // ─── onmessage: メッセージを受信したとき ───
    // サーバーからデータが届くたびに呼ばれるイベントハンドラ
    // - event.data: 受信したデータ（文字列またはバイナリ）
    ws.onmessage = (event) => {
      try {
        // JSON.parse(): JSON文字列をJavaScriptオブジェクトに変換
        // - 例: '{"type":"sensor_data","payload":{...}}'
        //   → { type: "sensor_data", payload: {...} }
        // - as WSMessage: TypeScriptに「この値はWSMessage型です」と伝える（型アサーション）
        const msg: WSMessage = JSON.parse(event.data);
        // パースに成功したら、メッセージを処理する
        handleMessage(msg);
      } catch {
        // JSON.parse が失敗した場合（不正なJSON文字列の場合）
        // - MessagePack（バイナリ形式のシリアライゼーション）の可能性もある
        // - 本番環境ではここにMessagePackのデコード処理を追加する
        console.warn("Failed to parse WebSocket message");
      }
    };

    // ─── onclose: 接続が閉じられたとき ───
    // サーバーが切断した場合や、ネットワークエラーが発生した場合に呼ばれる
    ws.onclose = () => {
      // 接続状態を false に更新
      setIsConnected(false);

      // clearInterval(): setInterval で開始したタイマーを停止する
      // - 接続が切れたら、Pingの送信を止める（送り先がないので）
      clearInterval(pingIntervalRef.current);

      // ─── 自動再接続の処理 ───
      // 💡 再接続パターン（Reconnection Pattern）:
      // - 接続が切れたとき、一定時間待ってから自動的に再接続を試みる
      // - 最大試行回数（MAX_RECONNECT_ATTEMPTS）を超えたら停止する
      // - RECONNECT_DELAY（3秒）の間隔を空けることで、
      //   サーバーに負荷をかけすぎないようにする
      if (reconnectCount < MAX_RECONNECT_ATTEMPTS) {
        // setTimeout(関数, 遅延ms): 指定時間後に関数を1回だけ実行する
        // - setInterval との違い: setTimeout は1回だけ、setInterval は繰り返し
        reconnectTimeoutRef.current = setTimeout(() => {
          // 再接続カウントを1増やす
          // (c) => c + 1: 前の値（c）に1を足す関数型更新
          // - setReconnectCount(reconnectCount + 1) と書くと
          //   古い値を参照する可能性があるため、関数型更新が安全
          setReconnectCount((c) => c + 1);
          // 再接続を実行
          connect();
        }, RECONNECT_DELAY);
      }
    };

    // ─── onerror: エラーが発生したとき ───
    // WebSocket通信中にエラーが発生した場合に呼ばれる
    // - エラーの詳細情報は取得できない（セキュリティ上の理由）
    // - 一般的には、接続を閉じて onclose で再接続処理を行う
    ws.onerror = () => {
      ws.close(); // 接続を閉じる → onclose が呼ばれる → 再接続処理へ
    };
  }, [accessToken, reconnectCount]);
  // 依存配列: accessToken または reconnectCount が変わったら関数を再作成

  // ===================================================================
  // 📨 handleMessage - 受信メッセージの処理（メッセージルーター）
  // ===================================================================
  // メッセージの type フィールドに基づいて、適切な処理に振り分ける
  // 💡 これは「ルーティング」パターン: メッセージの種類に応じて処理を分岐させる
  const handleMessage = useCallback(
    (msg: WSMessage) => {
      switch (msg.type) {
        // ── センサーデータの受信 ──
        case "sensor_data": {
          // as unknown as SensorData: 二段階の型アサーション
          // - payload は Record<string, unknown> 型なので、
          //   直接 SensorData にキャストできない
          // - まず unknown に変換してから SensorData に変換する
          const data = msg.payload as unknown as SensorData;
          if (msg.robot_id) {
            // ロボットIDに紐づくセンサーデータをストアに更新
            updateSensorData(msg.robot_id, data);
          }
          break;
        }
        // ── ロボットステータスの受信 ──
        case "robot_status": {
          if (msg.robot_id) {
            // Partial<Robot>: Robot型のすべてのプロパティをオプショナル（省略可能）にした型
            // - ステータス更新では、変更されたフィールドだけが送られてくるため
            updateRobotState(msg.robot_id, msg.payload as Partial<Robot>);
          }
          break;
        }
        // ── 緊急停止レスポンスの受信 ──
        case "estop_response": {
          // !!: 値を boolean に変換するイディオム（二重否定）
          // - 例: !!(undefined) → false, !!(true) → true, !!("text") → true
          setEStop(!!msg.payload.active);
          break;
        }
        // ── エラーメッセージの受信 ──
        case "error": {
          // console.error: ブラウザのコンソールにエラーメッセージを出力
          console.error("WebSocket error:", msg.payload);
          break;
        }
        // ── 未知のメッセージタイプ ──
        default:
          // 処理しないメッセージは無視する
          break;
      }
    },
    // 依存配列: ストアの更新関数が変わったら再作成
    [updateSensorData, updateRobotState, setEStop]
  );

  // ===================================================================
  // 📤 send - メッセージを送信する関数
  // ===================================================================
  const send = useCallback((msg: WSMessage) => {
    // WebSocket が接続中のときだけ送信する
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // JSON.stringify(): JavaScriptオブジェクトをJSON文字列に変換
      // - 例: { type: "ping", payload: {} }
      //   → '{"type":"ping","payload":{}}'
      // - WebSocketはテキストまたはバイナリデータしか送れないため、
      //   オブジェクトを文字列に変換する必要がある
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);
  // 依存配列が空: この関数は一度だけ作成され、再作成されない
  // - wsRef は useRef なので、参照自体は変わらない（.current が変わるだけ）

  // ===================================================================
  // 🔌 disconnect - WebSocket接続を切断する関数
  // ===================================================================
  const disconnect = useCallback(() => {
    // clearInterval(): Ping ハートビートのタイマーを停止
    // - 接続を切断するので、Pingを送る必要がなくなる
    clearInterval(pingIntervalRef.current);

    // clearTimeout(): 再接続のタイマーをキャンセル
    // - 手動で切断する場合、自動再接続は不要
    // 💡 clearInterval と clearTimeout の違い：
    //   - clearInterval: setInterval（繰り返し）のタイマーを停止
    //   - clearTimeout: setTimeout（1回限り）のタイマーをキャンセル
    clearTimeout(reconnectTimeoutRef.current);

    // WebSocket接続を閉じる
    // ?.（オプショナルチェーン）: wsRef.current が null でもエラーにならない
    wsRef.current?.close();
    // ref を null にリセット（ガベージコレクションでメモリ解放）
    wsRef.current = null;
    // 接続状態を false に更新
    setIsConnected(false);
  }, []);

  // ===================================================================
  // 🚀 sendVelocity - ロボットへ速度コマンドを送信する関数
  // ===================================================================
  // ロボットの移動速度を指定して送信する
  // - linear_x: 前後方向の速度（正=前進、負=後退）
  // - linear_y: 左右方向の速度（通常は0、オムニホイールロボット用）
  // - angular_z: 回転速度（正=反時計回り、負=時計回り）
  const sendVelocity = useCallback(
    (robotId: string, linear_x: number, linear_y: number, angular_z: number) => {
      send({
        type: "velocity_cmd",   // メッセージの種類: 速度コマンド
        robot_id: robotId,       // どのロボットに送るか
        payload: { linear_x, linear_y, angular_z },
        // ↑ ショートハンドプロパティ: キー名と変数名が同じ場合の省略記法
        // { linear_x: linear_x, linear_y: linear_y, angular_z: angular_z } と同じ
      });
    },
    [send] // send関数が変わったら再作成（実際にはsendは空の依存配列なので変わらない）
  );

  // ===================================================================
  // 🚨 sendEStop - 緊急停止を送信する関数
  // ===================================================================
  // E-Stop（Emergency Stop）: 緊急停止
  // - ロボットの動作を即座に停止させる安全機能
  // - robotId?: string の ?（オプショナルパラメータ）は省略可能を意味する
  //   → 全ロボットを一括停止する場合は省略
  const sendEStop = useCallback(
    (robotId?: string) => {
      send({
        type: "estop",
        robot_id: robotId,
        payload: { activate: true }, // true = 緊急停止を有効化
      });
    },
    [send]
  );

  // ===================================================================
  // ✅ releaseEStop - 緊急停止を解除する関数
  // ===================================================================
  // 緊急停止状態を解除して、ロボットが再び動けるようにする
  const releaseEStop = useCallback(
    (robotId?: string) => {
      send({
        type: "estop",
        robot_id: robotId,
        payload: { activate: false }, // false = 緊急停止を解除
      });
    },
    [send]
  );

  // ===================================================================
  // 🗺️ sendNavGoal - ナビゲーション目標地点を送信する関数
  // ===================================================================
  // ロボットに「この座標に移動して」という目標を送信する
  // - x, y: 目標地点の座標（メートル単位）
  // - theta: 到着時の向き（ラジアン単位、0=前向き）
  const sendNavGoal = useCallback(
    (robotId: string, x: number, y: number, theta: number) => {
      send({
        type: "nav_goal",
        robot_id: robotId,
        payload: { x, y, theta },
      });
    },
    [send]
  );

  // ===================================================================
  // 🔄 Lifecycle（ライフサイクル）管理
  // ===================================================================
  // コンポーネントのマウント/アンマウント時に接続/切断を自動管理
  useEffect(() => {
    // アクセストークンがある（ログイン済み）場合のみ接続
    if (accessToken) {
      connect();
    }
    // クリーンアップ関数: コンポーネントがアンマウントされるときに切断
    // - これにより、画面遷移時に不要なWebSocket接続が残るのを防ぐ
    return () => {
      disconnect();
    };
  }, [accessToken]);
  // 依存配列: accessToken が変わったら（ログイン/ログアウト時）再実行

  // ===================================================================
  // 📦 戻り値: フックの利用者に公開する値と関数
  // ===================================================================
  // このフックを使うコンポーネントは、以下の値と関数にアクセスできる
  // 例: const { isConnected, sendVelocity } = useWebSocket();
  return {
    isConnected,      // 接続中かどうか（boolean）
    reconnectCount,   // 再接続の試行回数（number）
    send,             // 汎用メッセージ送信関数
    sendVelocity,     // 速度コマンド送信関数
    sendEStop,        // 緊急停止送信関数
    releaseEStop,     // 緊急停止解除関数
    sendNavGoal,      // ナビゲーション目標送信関数
    connect,          // 手動接続関数
    disconnect,       // 手動切断関数
  };
}
