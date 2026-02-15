// =============================================================================
// ファイル: config.go（設定管理）
// 概要: ゲートウェイサーバーの全設定を管理するパッケージ
//
// このファイルは、アプリケーションの設定値（ポート番号、タイムアウト、
// Redis接続先など）を一元管理します。
//
// 【設計の考え方】
//   設定値をコード中にハードコーディング（直書き）するのではなく、
//   環境変数やデフォルト値から読み込むことで、以下のメリットがあります：
//   - 環境ごと（開発/本番）に異なる設定を使える
//   - Docker/Kubernetes での設定変更が容易
//   - コードを変更せずに動作を調整できる
//
// 【使用ライブラリ: Viper（バイパー）】
//   Viper は Go で最も人気のある設定管理ライブラリ。
//   環境変数、設定ファイル（YAML, JSON, TOML）、リモート設定など
//   多様なソースから設定を読み込める。
//
// 【Go言語の知識: パッケージ（package）】
//   Go のコードはパッケージ単位で整理される。
//   パッケージ名はディレクトリ名と一致させるのが慣例。
//   他のパッケージから使われる名前（型、関数など）は大文字で始める（エクスポート）。
// =============================================================================
package config

import (
// time: 時間に関する型と操作を提供する標準ライブラリ。
// time.Duration（期間）型を使って、タイムアウト値を表現する。
"time"

// viper: 設定管理ライブラリ。
// 環境変数やデフォルト値から設定を読み込む。
// v.GetInt(), v.GetString() などで型安全に値を取得できる。
"github.com/spf13/viper"
)

// =============================================================================
// Config: ゲートウェイの全設定を保持するルート構造体
//
// 【Go言語の知識: 構造体（struct）】
//   構造体は、関連するデータをグループ化するための型。
//   他の言語のクラスに似ているが、メソッドは外部で定義する。
//
// 【設計パターン: 設定の階層化】
//   設定を Server, Redis, Safety などのカテゴリに分けることで、
//   見通しが良くなり、管理しやすくなる。
// =============================================================================
type Config struct {
Server  ServerConfig  // サーバー関連の設定（ポート番号など）
Redis   RedisConfig   // Redis関連の設定（接続URLなど）
Safety  SafetyConfig  // 安全機構関連の設定（速度制限など）
Auth    AuthConfig    // 認証関連の設定（JWT公開鍵のパスなど）
Logging LoggingConfig // ログ関連の設定（ログレベルなど）
}

// =============================================================================
// ServerConfig: サーバーの接続設定を保持する構造体
//
// 【Go言語の知識: 構造体タグ（Struct Tags）】
//   フィールドの後ろにある ``（バッククォート）で囲まれた部分が「構造体タグ」。
//   例: `mapstructure:"port"` は、設定ファイル中のキー "port" を
//   この Port フィールドにマッピングすることを意味する。
//
//   【mapstructure タグの役割】
//   Viper ライブラリが設定値を構造体にマッピングする際に使用。
//   設定ファイルのキー名と Go のフィールド名を対応付ける。
//   例: YAML の "port: 8080" → ServerConfig.Port = 8080
// =============================================================================
type ServerConfig struct {
Port     int    `mapstructure:"port"`      // WebSocketサーバーのポート番号（例: 8080）
GRPCPort int    `mapstructure:"grpc_port"` // gRPCサーバーのポート番号（例: 50051）
Host     string `mapstructure:"host"`      // リッスンするホストアドレス（例: "0.0.0.0"）
}

// =============================================================================
// RedisConfig: Redisの接続設定を保持する構造体
//
// Redis はインメモリのKey-Valueストア（高速なデータベース）。
// センサーデータやコマンドをストリーム（時系列データ）として保存する。
// =============================================================================
type RedisConfig struct {
URL string `mapstructure:"url"` // Redis接続URL（例: "redis://localhost:6379/0"）
}

// =============================================================================
// SafetyConfig: ロボットの安全機構に関する設定を保持する構造体
//
// ロボット制御では安全が最も重要。この設定でロボットの動作制限を定義する。
//
// 【Go言語の知識: 複数の型】
//   bool:    真偽値（true/false）
//   int:     整数
//   float64: 64ビット浮動小数点数（小数を扱う）
// =============================================================================
type SafetyConfig struct {
EStopEnabled            bool    `mapstructure:"estop_enabled"`              // 緊急停止機能を有効にするか
CommandTimeoutSec       int     `mapstructure:"cmd_timeout_sec"`            // コマンドのタイムアウト（秒）
MaxLinearVelocity       float64 `mapstructure:"max_linear_vel"`             // 直線速度の上限（m/s）
MaxAngularVelocity      float64 `mapstructure:"max_angular_vel"`            // 回転速度の上限（rad/s）
OperationLockTimeoutSec int     `mapstructure:"operation_lock_timeout_sec"` // 操作ロックのタイムアウト（秒）
}

// =============================================================================
// AuthConfig: 認証関連の設定を保持する構造体
//
// JWT（JSON Web Token）を使った認証の設定。
// 公開鍵でトークンの署名を検証し、ユーザーの身元を確認する。
// =============================================================================
type AuthConfig struct {
JWTPublicKeyPath string `mapstructure:"jwt_public_key_path"` // JWT公開鍵ファイルのパス
}

// =============================================================================
// LoggingConfig: ログ出力に関する設定を保持する構造体
// =============================================================================
type LoggingConfig struct {
Level string `mapstructure:"level"` // ログレベル（"debug", "info", "warn", "error"）
}

// =============================================================================
// CommandTimeout: コマンドタイムアウトを time.Duration 型で返すメソッド
//
// 【Go言語の知識: メソッド（Method）】
//   Go では、関数を特定の型に「紐付ける」ことができる。これがメソッド。
//   func (レシーバ) メソッド名() 戻り値型 { ... }
//
//   (s *SafetyConfig) はレシーバ（receiver）と呼ばれ、
//   このメソッドが SafetyConfig 型に属することを示す。
//   s はメソッド内で SafetyConfig のフィールドにアクセスするための変数名。
//
// 【Go言語の知識: ポインタレシーバ vs 値レシーバ】
//   *SafetyConfig（ポインタレシーバ）: 元の構造体を直接参照する。
//   SafetyConfig（値レシーバ）: 構造体のコピーを作って使う。
//   大きな構造体や変更が必要な場合はポインタレシーバを使う。
//
// 【Go言語の知識: time.Duration】
//   time.Duration は Go の時間の長さを表す型。
//   ナノ秒単位の int64 で内部表現されている。
//   time.Second は 1秒を表す定数。
//   time.Duration(3) * time.Second = 3秒 を表す Duration 値。
// =============================================================================
func (s *SafetyConfig) CommandTimeout() time.Duration {
return time.Duration(s.CommandTimeoutSec) * time.Second
}

// =============================================================================
// OperationLockTimeout: 操作ロックタイムアウトを time.Duration 型で返すメソッド
//
// 操作ロックは、一人のユーザーが一定時間ロボットを独占操作するための仕組み。
// タイムアウト時間が過ぎると、ロックが自動的に解除される。
// =============================================================================
func (s *SafetyConfig) OperationLockTimeout() time.Duration {
return time.Duration(s.OperationLockTimeoutSec) * time.Second
}

// =============================================================================
// Load: 環境変数とデフォルト値から設定を読み込む関数
//
// 【Go言語の知識: 関数の戻り値】
//   (*Config, error) は「Config のポインタ」と「エラー」を返すことを示す。
//   * はポインタを意味し、構造体そのものではなく「構造体の参照」を返す。
//   大きな構造体を効率的に渡すために使用（コピーを避ける）。
//
// 【Viperのワークフロー】
//   1. viper.New() で新しい Viper インスタンスを作成
//   2. AutomaticEnv() で環境変数の自動読み込みを有効化
//   3. SetDefault() でデフォルト値（環境変数が設定されていない場合の値）を設定
//   4. GetInt(), GetString() などで型安全に値を取得
//
// 【環境変数とは？】
//   OSレベルで設定されるキーバリューペア。
//   例: export GATEWAY_PORT=9090 で GATEWAY_PORT の値を 9090 に設定。
//   Docker や Kubernetes でもよく使われる設定方法。
// =============================================================================
func Load() (*Config, error) {
// 新しい Viper インスタンスを作成。
// 【Go言語の知識: 短縮変数宣言 :=】
//   := はGoの短縮変数宣言で、型推論により変数の型を自動で決定する。
//   v := viper.New() は var v *viper.Viper = viper.New() と同じ。
v := viper.New()

// 環境変数の自動バインドを有効にする。
// これにより、v.GetInt("GATEWAY_PORT") が環境変数 GATEWAY_PORT の値を返す。
v.AutomaticEnv()

// --- サーバー設定のデフォルト値 ---
v.SetDefault("GATEWAY_PORT", 8080)        // WebSocketのデフォルトポート
v.SetDefault("GATEWAY_GRPC_PORT", 50051)  // gRPCのデフォルトポート
v.SetDefault("GATEWAY_HOST", "0.0.0.0")   // 全ネットワークインターフェースでリッスン

// --- 安全機構のデフォルト値 ---
v.SetDefault("GATEWAY_ESTOP_ENABLED", true) // 緊急停止はデフォルト有効
v.SetDefault("GATEWAY_CMD_TIMEOUT_SEC", 3)  // 3秒のコマンドタイムアウト
v.SetDefault("GATEWAY_MAX_LINEAR_VEL", 1.0) // 直線速度上限 1.0 m/s
v.SetDefault("GATEWAY_MAX_ANGULAR_VEL", 2.0) // 回転速度上限 2.0 rad/s
v.SetDefault("GATEWAY_OPERATION_LOCK_TIMEOUT_SEC", 300) // ロックは5分（300秒）で自動解除

// --- 認証のデフォルト値 ---
v.SetDefault("JWT_PUBLIC_KEY_PATH", "/app/keys/public.pem") // JWT公開鍵のパス

// --- ログのデフォルト値 ---
v.SetDefault("GATEWAY_LOG_LEVEL", "info") // デフォルトは info レベル

// --- Redis のデフォルト値 ---
v.SetDefault("REDIS_URL", "redis://localhost:6379/0") // ローカルのRedisに接続

// 設定構造体を作成して値を設定する。
// 【Go言語の知識: 複合リテラル（Composite Literal）】
//   &Config{...} で Config 構造体を作成し、そのポインタを返す。
//   入れ子の構造体（ServerConfig など）も同時に初期化できる。
cfg := &Config{
Server: ServerConfig{
Port:     v.GetInt("GATEWAY_PORT"),       // 環境変数 or デフォルト値からポートを取得
GRPCPort: v.GetInt("GATEWAY_GRPC_PORT"),  // gRPCポートを取得
Host:     v.GetString("GATEWAY_HOST"),    // ホストアドレスを取得
},
Redis: RedisConfig{
URL: v.GetString("REDIS_URL"), // Redis接続URLを取得
},
Safety: SafetyConfig{
EStopEnabled:            v.GetBool("GATEWAY_ESTOP_ENABLED"),            // bool型で取得
CommandTimeoutSec:       v.GetInt("GATEWAY_CMD_TIMEOUT_SEC"),            // int型で取得
MaxLinearVelocity:       v.GetFloat64("GATEWAY_MAX_LINEAR_VEL"),         // float64型で取得
MaxAngularVelocity:      v.GetFloat64("GATEWAY_MAX_ANGULAR_VEL"),        // float64型で取得
OperationLockTimeoutSec: v.GetInt("GATEWAY_OPERATION_LOCK_TIMEOUT_SEC"), // int型で取得
},
Auth: AuthConfig{
JWTPublicKeyPath: v.GetString("JWT_PUBLIC_KEY_PATH"), // 文字列で取得
},
Logging: LoggingConfig{
Level: v.GetString("GATEWAY_LOG_LEVEL"), // ログレベルを取得
},
}

// 設定とnil（エラーなし）を呼び出し元に返す。
// 【Go言語の知識: 多値返却】
//   Go の関数は複数の値を返せる。ここでは (設定, エラー) を返す。
//   エラーがない場合は nil を返すのが Go の慣例。
return cfg, nil
}
