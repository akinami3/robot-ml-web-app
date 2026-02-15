/**
 * index.ts - Robot AI Web アプリケーションの共有型定義ファイル
 *
 * =====================================================================
 * 📁 ファイルの概要（このファイルが何をするか）
 * =====================================================================
 * このファイルは、アプリケーション全体で使用する TypeScript の「型」を
 * 一箇所にまとめて定義しています。
 *
 * 💡 TypeScript の「型」とは？
 * - JavaScriptには型がなく、変数にどんな値でも入れられます
 * - TypeScriptでは「この変数は文字列だけ」「この変数は数値だけ」のように
 *   型を指定できます
 * - 型を指定することで、コードを書いている段階で間違いを発見でき、
 *   実行時のバグを大幅に減らせます
 *
 * 💡 type vs interface の違い：
 * - type（型エイリアス）: 既存の型に名前をつける。ユニオン型（|）が使える
 *   例: type Color = "red" | "blue" | "green"
 * - interface（インターフェース）: オブジェクトの形（構造）を定義する
 *   例: interface User { name: string; age: number; }
 * - どちらもオブジェクトの型定義に使えますが、typeはユニオン型にも使えます
 * - 一般的な使い分け：
 *   - オブジェクトの型定義 → interface
 *   - ユニオン型や型の別名 → type
 *
 * 💡 export とは？
 * - export をつけると、他のファイルから import して使えるようになる
 * - export がないと、このファイル内でしか使えない（プライベート）
 *
 * 💡 なぜ型を1つのファイルにまとめるのか？
 * - 型の定義が散らばると、同じ型を何度も定義してしまう
 * - 1箇所で管理すれば、変更があっても1つのファイルを修正すればOK
 * - チーム開発で「この型はどこにある？」と迷わない
 * =====================================================================
 */

// ─── Auth（認証）関連の型 ──────────────────────────────────────────

/**
 * UserRole - ユーザーの役割（権限レベル）を定義する型
 *
 * 💡 文字列リテラル型（String Literal Type）:
 * - 通常の string 型は「任意の文字列」を許容しますが、
 *   文字列リテラル型は「特定の文字列のみ」を許容します
 * - "admin" | "operator" | "viewer" → この3つの文字列だけが有効
 *
 * 💡 ユニオン型（|）:
 * - | は「または」を意味する型演算子
 * - A | B → A型またはB型のどちらか
 * - 例: string | number → 文字列または数値
 *
 * 各役割の意味：
 * - "admin" : 管理者（全操作が可能）
 * - "operator" : オペレーター（ロボット操作が可能）
 * - "viewer" : 閲覧者（データの閲覧のみ可能）
 */
export type UserRole = "admin" | "operator" | "viewer";

/**
 * User - ユーザー情報を表すインターフェース
 *
 * 💡 interface の各フィールドの書き方：
 * フィールド名: 型;
 * - 型の種類: string（文字列）, number（数値）, boolean（真偽値）など
 */
export interface User {
  id: string;          // ユーザーの一意な識別子（UUID形式の文字列）
  username: string;    // ユーザー名（ログインに使用）
  email: string;       // メールアドレス
  role: UserRole;      // ユーザーの役割（上で定義した UserRole 型を使用）
  is_active: boolean;  // アカウントが有効かどうか（true=有効、false=無効）
  created_at: string;  // アカウント作成日時（ISO 8601形式の文字列）
}

/**
 * AuthTokens - 認証トークン情報を表すインターフェース
 *
 * 💡 JWT（JSON Web Token）認証の仕組み：
 * 1. ユーザーがログインすると、サーバーがトークン（暗号化された認証情報）を発行
 * 2. クライアントはこのトークンをAPI呼び出し時に添付して、本人確認を行う
 * 3. access_token の有効期限が切れたら、refresh_token で新しいトークンを取得
 */
export interface AuthTokens {
  access_token: string;   // APIアクセス用トークン（短い有効期限）
  refresh_token: string;  // トークン更新用トークン（長い有効期限）
  token_type: string;     // トークンの種類（通常は "Bearer"）
  expires_in: number;     // アクセストークンの有効期限（秒数）
}

// ─── Robot（ロボット）関連の型 ─────────────────────────────────────────

/**
 * RobotState - ロボットの状態を定義する型
 *
 * 💡 ステートマシン（State Machine）パターン：
 * - ロボットは常に以下の状態のうち1つにある
 * - 状態に応じてUIの表示（色やアイコン）を変える
 * - 無効な状態遷移を型レベルで防止できる
 *
 * ユニオン型で定義することで、例えば以下のような誤りをコンパイル時に検出：
 *   const state: RobotState = "running"; // エラー！ "running" は定義されていない
 */
export type RobotState =
  | "disconnected"       // 切断中（通信不能）
  | "connecting"         // 接続中（通信を確立中）
  | "idle"               // アイドル（接続済みだが停止中）
  | "moving"             // 移動中（動作中）
  | "error"              // エラー（異常が発生）
  | "emergency_stopped"; // 緊急停止中（E-Stopが有効）

/**
 * Robot - ロボットの情報を表すインターフェース
 *
 * 💡 null とは？
 * - 「値がない」ことを明示的に表す特別な値
 * - number | null → 数値か、または値がない
 * - バッテリー残量が不明な場合は null、100%なら 100 のように使う
 *
 * 💡 string[] とは？
 * - string の配列（複数の文字列を格納するリスト）
 * - 例: ["navigation", "manipulation", "lidar"]
 */
export interface Robot {
  id: string;                     // ロボットの一意な識別子
  name: string;                   // ロボットの表示名（例: "搬送ロボット1号"）
  adapter_type: string;           // 接続アダプターの種類（例: "ros2", "mujoco"）
  state: RobotState;              // 現在の状態（上で定義した RobotState 型）
  capabilities: string[];         // ロボットの機能一覧（配列）
  battery_level: number | null;   // バッテリー残量（0-100%、不明時はnull）
  last_seen: string | null;       // 最後に通信した日時（未接続時はnull）
  created_at: string;             // 登録日時
}

// ─── Sensor Data（センサーデータ）関連の型 ───────────────────────────────

/**
 * SensorType - センサーの種類を定義する型
 *
 * ロボットに搭載される様々なセンサーの種類
 * 各センサーが何を測定するか：
 */
export type SensorType =
  | "lidar"        // LiDAR（レーザー光で周囲の距離を測定する）
  | "camera"       // カメラ（画像や映像を取得する）
  | "imu"          // IMU（加速度・角速度を測定する慣性計測装置）
  | "odometry"     // オドメトリ（車輪の回転から移動距離を推定する）
  | "battery"      // バッテリー（電池残量を監視する）
  | "gps"          // GPS（位置情報を取得する）
  | "point_cloud"  // ポイントクラウド（3D空間の点群データ）
  | "joint_state"; // ジョイントステート（ロボットアームの関節角度）

/**
 * SensorData - センサーデータを表すインターフェース
 *
 * 💡 Record<string, unknown> とは？
 * - Record<K, V>: キーの型がK、値の型がVのオブジェクト型
 * - Record<string, unknown>: 任意の文字列キーに対して、任意の型の値を持つ
 * - unknown型: どんな値でも入る（any と似ているが、使う前に型チェックが必要）
 * - センサーの種類によってデータの構造が異なるため、柔軟な型を使っている
 *   例: LiDARは距離の配列、カメラは画像データ、IMUは加速度ベクトルなど
 *
 * 💡 オプショナルフィールド（?）とは？（session_id の例）
 * - session_id: string | null → 値は必ず存在するが、null の可能性がある
 * - age?: number → age フィールド自体が存在しない可能性がある（省略可能）
 * - この違いは重要です！
 */
export interface SensorData {
  id: string;                       // センサーデータの一意な識別子
  robot_id: string;                 // このデータを送信したロボットのID
  sensor_type: SensorType;          // センサーの種類（上で定義した SensorType 型）
  data: Record<string, unknown>;    // センサーデータ本体（構造はセンサーにより異なる）
  timestamp: string;                // データ取得時刻（ISO 8601形式）
  session_id: string | null;        // 記録セッションID（記録中でなければ null）
  sequence_number: number;          // 連番（データの順序を保証するため）
}

// ─── WebSocket Messages（WebSocketメッセージ）関連の型 ────────────────────

/**
 * WSMessageType - WebSocketメッセージの種類を定義する型
 *
 * クライアント（フロントエンド）とサーバー（バックエンド）間で
 * やり取りされるメッセージの種類：
 */
export type WSMessageType =
  | "auth"           // 認証要求（クライアント→サーバー）
  | "auth_response"  // 認証レスポンス（サーバー→クライアント）
  | "ping"           // 死活確認要求（クライアント→サーバー）
  | "pong"           // 死活確認応答（サーバー→クライアント）
  | "velocity_cmd"   // 速度コマンド（クライアント→ロボット）
  | "nav_goal"       // ナビゲーション目標（クライアント→ロボット）
  | "nav_cancel"     // ナビゲーションキャンセル（クライアント→ロボット）
  | "estop"          // 緊急停止（クライアント→ロボット）
  | "estop_response" // 緊急停止応答（ロボット→クライアント）
  | "lock_acquire"   // ロボット操作権の取得要求
  | "lock_release"   // ロボット操作権の解放
  | "lock_response"  // ロボット操作権の応答
  | "sensor_data"    // センサーデータ（ロボット→クライアント）
  | "robot_status"   // ロボット状態更新（ロボット→クライアント）
  | "error";         // エラー通知

/**
 * WSMessage - WebSocketメッセージの構造を定義するインターフェース
 *
 * 💡 オプショナルプロパティ（?）:
 * - robot_id?: string → robot_id は省略可能（なくてもOK）
 * - timestamp?: number → timestamp も省略可能
 * - 認証メッセージなど、ロボットに紐づかないメッセージでは省略される
 */
export interface WSMessage {
  type: WSMessageType;                // メッセージの種類（必須）
  robot_id?: string;                  // 対象ロボットID（省略可能）
  payload: Record<string, unknown>;   // メッセージの内容（構造はtypeにより異なる）
  timestamp?: number;                 // タイムスタンプ（Unix時間、省略可能）
}

/**
 * VelocityCommand - 速度コマンドの構造を定義するインターフェース
 *
 * ロボットへ送信する移動速度の指定
 * - ROS（Robot Operating System）の geometry_msgs/Twist と同じ概念
 */
export interface VelocityCommand {
  linear_x: number;   // 前後方向の速度（m/s）: 正=前進、負=後退
  linear_y: number;   // 左右方向の速度（m/s）: 通常は0（オムニホイール用）
  angular_z: number;  // 回転速度（rad/s）: 正=反時計回り、負=時計回り
}

/**
 * NavigationGoal - ナビゲーション目標地点の構造を定義するインターフェース
 *
 * ロボットに「ここに移動して」という目標地点を指定する
 */
export interface NavigationGoal {
  x: number;       // 目標地点のX座標（メートル）
  y: number;       // 目標地点のY座標（メートル）
  theta: number;   // 到着時の向き（ラジアン、0=前向き、π/2=左向き）
}

// ─── Dataset（データセット）関連の型 ───────────────────────────────────

/**
 * Dataset - データセット情報を表すインターフェース
 *
 * 💡 データセットとは？
 * - ロボットのセンサーデータを集めたもの
 * - 機械学習の訓練データとして使用する
 * - 例: 「倉庫A内のLiDARとカメラデータ1000件」
 *
 * 💡 string[] と string の違い：
 * - string: 1つの文字列 → "lidar"
 * - string[]: 文字列の配列（リスト）→ ["lidar", "camera", "imu"]
 * - []: 配列の型を示すTypeScriptの記法
 */
export interface Dataset {
  id: string;                       // データセットの一意な識別子
  name: string;                     // データセット名（例: "倉庫走行データ2026"）
  description: string;              // データセットの説明文
  owner_id: string;                 // 作成者のユーザーID
  status: string;                   // 状態（例: "recording", "completed"）
  sensor_types: string[];           // 含まれるセンサー種類のリスト
  robot_ids: string[];              // データを収集したロボットIDのリスト
  start_time: string | null;        // 記録開始時刻（未開始ならnull）
  end_time: string | null;          // 記録終了時刻（記録中ならnull）
  record_count: number;             // 記録されたデータの件数
  size_bytes: number;               // データサイズ（バイト単位）
  tags: string[];                   // タグ（分類用ラベル）のリスト
  created_at: string;               // データセット作成日時
}

// ─── Recording（記録セッション）関連の型 ─────────────────────────────────

/**
 * RecordingSession - データ記録セッションを表すインターフェース
 *
 * 💡 セッション（Session）とは？
 * - 一連の記録操作のまとまり
 * - 「記録開始」から「記録終了」までの期間
 * - 1回の記録セッションで複数のセンサーデータを収集する
 *
 * 💡 ネストされたオブジェクト型の書き方:
 * config: {
 *   sensor_types: string[];
 *   enabled: boolean;
 * }
 * → config フィールドはオブジェクト型で、中にさらにフィールドがある
 * → 別途 interface を定義せず、インラインで型を書くこともできる
 */
export interface RecordingSession {
  id: string;                       // セッションの一意な識別子
  robot_id: string;                 // 記録対象のロボットID
  user_id: string;                  // 記録を開始したユーザーID
  is_active: boolean;               // 記録中かどうか（true=記録中）
  record_count: number;             // 現在の記録件数
  size_bytes: number;               // 現在のデータサイズ（バイト）
  started_at: string;               // 記録開始日時
  stopped_at: string | null;        // 記録終了日時（記録中はnull）
  config: {                         // 記録設定（ネストされたオブジェクト型）
    sensor_types: string[];         // 記録するセンサーの種類リスト
    enabled: boolean;               // 記録が有効かどうか
  };
}

// ─── RAG（検索拡張生成）関連の型 ───────────────────────────────────────

/**
 * RAGDocument - RAGシステムに登録されたドキュメントを表すインターフェース
 *
 * 💡 RAG（Retrieval-Augmented Generation）とは？
 * - AIが質問に答えるとき、関連するドキュメントを検索して参考にする仕組み
 * - ロボットのマニュアルや技術文書を登録して、AIに質問できる
 * - 例: 「このロボットの最大速度は？」→ マニュアルから回答を生成
 *
 * 💡 チャンク（Chunk）とは？
 * - 長いドキュメントを小さな断片に分割したもの
 * - AIの検索精度を上げるために分割する
 */
export interface RAGDocument {
  id: string;           // ドキュメントの一意な識別子
  title: string;        // ドキュメントのタイトル
  source: string;       // ドキュメントの出典（URL やファイルパス）
  file_type: string;    // ファイルの種類（例: "pdf", "markdown", "txt"）
  file_size: number;    // ファイルサイズ（バイト）
  chunk_count: number;  // ドキュメントが分割されたチャンク数
  created_at: string;   // 登録日時
}

/**
 * RAGQueryResult - RAG検索の結果を表すインターフェース
 *
 * 💡 Array<T> と T[] の違い：
 * - Array<{ chunk_id: string; ... }> と { chunk_id: string; ... }[] は同じ意味
 * - どちらも「T型の配列」を表す
 * - Array<T> の方がネストしたオブジェクト型のときに読みやすい
 */
export interface RAGQueryResult {
  answer: string;       // AIが生成した回答テキスト
  sources: Array<{      // 回答の根拠となったドキュメントのリスト
    chunk_id: string;    // チャンクの識別子
    document_id: string; // 元のドキュメントの識別子
    similarity: number;  // 類似度スコア（0.0〜1.0、1.0が最も類似）
    preview: string;     // チャンクの内容のプレビュー（最初の数行）
  }>;
  context_used: boolean; // コンテキスト（ドキュメント）が使用されたかどうか
}

// ─── Audit（監査ログ）関連の型 ─────────────────────────────────────────

/**
 * AuditLog - 監査ログを表すインターフェース
 *
 * 💡 監査ログ（Audit Log）とは？
 * - 「誰が」「いつ」「何をしたか」を記録するログ
 * - セキュリティ上、重要な操作（ロボットの制御、設定変更など）を追跡する
 * - 問題が発生したときの原因調査に使用する
 */
export interface AuditLog {
  id: string;                          // ログエントリの一意な識別子
  user_id: string;                     // 操作を行ったユーザーのID
  action: string;                      // 実行した操作（例: "robot_control", "login"）
  resource_type: string;               // 操作対象の種類（例: "robot", "dataset"）
  resource_id: string;                 // 操作対象のID
  details: Record<string, unknown>;    // 操作の詳細情報（構造は操作により異なる）
  ip_address: string;                  // 操作元のIPアドレス
  timestamp: string;                   // 操作日時（ISO 8601形式）
}
