// =============================================================================
// Step 11: Redis パブリッシャー — Gateway → Redis Streams
// =============================================================================
//
// 【Step 10 からの変更点（Step 11 で新規追加）】
// Gateway が受信したセンサーデータを Redis Streams に発行（パブリッシュ）する。
// これにより、バックエンド（Python）側でデータを永続化・分析できる。
//
// 【Redis とは？】
// Redis はインメモリ（メモリ上で動作する）のデータストア。
// 通常のデータベース（PostgreSQL）よりも非常に高速で、
// リアルタイムデータの一時保存に最適。
//
// 【Redis Streams とは？】
// Redis Streams は「時系列データを保存するデータ構造」。
// Apache Kafka のような「メッセージキュー」に似た機能を、
// Redis 単体で実現できる。
//
// 特徴：
//   - 時系列順にデータが保存される（ログのような構造）
//   - 複数のコンシューマー（消費者）が同じデータを読める
//   - Consumer Group でデータの分散処理が可能
//   - MaxLen で最大エントリ数を制限できる（古いデータは自動削除）
//   - Approx（概算）モードで削除の効率を向上
//
// 【このファイルの役割】
//
//   ゲートウェイ → Redis Streams → バックエンド（データ分析・ML）
//
// 【設計パターン: パブリッシャー（Publisher）パターン】
// データの「発行者」として、データを Redis に書き込む責任を持つ。
// 誰がデータを読むかは気にしない（疎結合）。
//
// 【学習ポイント】
// - Redis Streams の XADD コマンド
// - Go の Redis クライアントライブラリ（go-redis）の使い方
// - JSON シリアライゼーション
// - エラーハンドリングとリソース管理（Close パターン）
// =============================================================================
package bridge

import (
	// context: ゴルーチンのキャンセルやタイムアウトの伝播を管理。
	// Redis への書き込みがタイムアウトした場合のキャンセルに使用。
	"context"

	// encoding/json: 構造体を JSON 文字列に変換するための標準ライブラリ。
	// Redis Streams の Values にはプリミティブ型しか格納できないため、
	// 複雑なデータ構造（map, slice）は JSON 文字列に変換して格納する。
	"encoding/json"

	// fmt: 文字列のフォーマットとエラーメッセージの生成。
	"fmt"

	// log: Go 標準のログパッケージ。
	// Step 13 で高性能な zap ロガーに置き換える予定。
	"log"

	// go-redis: Go 用の Redis クライアントライブラリ（外部パッケージ）。
	// v9 はバージョン9。context 対応が充実している。
	"github.com/redis/go-redis/v9"

	// adapter: ロボットアダプターパッケージ。
	// SensorData 型と Command 型を使用するためにインポート。
	"github.com/robot-ai-webapp/gateway/internal/adapter"
)

// =============================================================================
// 定数の定義: Redis Streams のストリーム名
// =============================================================================
//
// 【Go言語の知識: const（定数）】
// const で定義された値はコンパイル時に決まり、実行中に変更できない。
// ストリーム名を定数にすることで：
//   - タイプミスを防ぐ
//   - 変更が必要な場合は1箇所で済む
//   - コードの読みやすさが向上する
//
// 【命名規則】
// "robot:sensor_data" のようにコロンで区切るのは Redis の命名慣例。
// 名前空間（namespace）として機能し、キーの整理に役立つ。
const (
	sensorDataStream = "robot:sensor_data" // センサーデータを格納するストリーム名
	commandStream    = "robot:commands"    // コマンドを格納するストリーム名
)

// =============================================================================
// RedisPublisher: Redis にデータを発行する構造体
// =============================================================================
//
// 【Go言語の知識: 構造体のカプセル化】
// client は小文字で始まるため、パッケージ外からアクセスできない。
// 外部からはメソッド（PublishSensorData, PublishCommand, Close）のみ使用可能。
//
// 【Go言語の知識: ポインタ型フィールド *redis.Client】
// *redis.Client はポインタ型。実体は1つだけで、参照を共有する。
type RedisPublisher struct {
	client *redis.Client // Redis クライアント（接続管理やコマンド実行を担当）
}

// =============================================================================
// NewRedisPublisher: Redis パブリッシャーを作成するコンストラクタ関数
// =============================================================================
//
// 処理の流れ：
//  1. Redis URL を解析して接続オプションを取得
//  2. Redis クライアントを作成
//  3. 接続テスト（Ping）を実行
//  4. 成功したら RedisPublisher を返す
//
// 【Go言語の知識: エラーラッピング（Error Wrapping）】
// fmt.Errorf("...: %w", err) の %w はエラーをラップ（包む）する。
// ラップすることで、元のエラーの情報を保持しつつ、
// 追加のコンテキスト（どこで何が失敗したか）を付加できる。
//
// 引数:
//
//	redisURL: Redis 接続URL（例: "redis://localhost:6379/0"）
//
// 戻り値:
//
//	(*RedisPublisher, nil): 成功時 → パブリッシャーとエラーなし
//	(nil, error): 失敗時 → nil とエラー内容
func NewRedisPublisher(redisURL string) (*RedisPublisher, error) {
	// Redis URL を解析して接続オプション（ホスト、ポート、DB番号など）を取得。
	// 例: "redis://localhost:6379/0"
	//   → Host: "localhost:6379", DB: 0
	opts, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, fmt.Errorf("invalid redis URL: %w", err)
	}

	// Redis クライアントを作成。この時点ではまだ接続は確立されていない。
	// Go の Redis クライアントは「遅延接続」で、実際のコマンド実行時に接続する。
	client := redis.NewClient(opts)

	// 接続テスト: PING コマンドを送信して、Redis が応答するか確認する。
	// context.Background() は「キャンセルなし・タイムアウトなし」のコンテキスト。
	if err := client.Ping(context.Background()).Err(); err != nil {
		return nil, fmt.Errorf("redis connection failed: %w", err)
	}

	log.Println("✅ Redis 接続成功")

	return &RedisPublisher{
		client: client,
	}, nil
}

// =============================================================================
// PublishSensorData: センサーデータを Redis Stream に発行するメソッド
// =============================================================================
//
// ロボットから受信したセンサーデータ（LiDAR、カメラ、IMU など）を
// Redis Streams に書き込む。バックエンドはこのデータを読み取って処理する。
//
// 【Redis XADD コマンド】
// XADD はストリームにエントリを追加するコマンド。
// 各エントリは自動生成されるID（タイムスタンプベース）とフィールド群で構成。
//
//   XADD robot:sensor_data * robot_id "robot-01" topic "/lidar" ...
//         ^ストリーム名      ^自動ID   ^フィールド群
//
// 【Go言語の知識: メソッドレシーバ (r *RedisPublisher)】
// func (r *RedisPublisher) PublishSensorData(...) は、
// RedisPublisher 型に紐づくメソッド。
// r はこのメソッド内で RedisPublisher のフィールドにアクセスするための変数。
//
// 引数:
//
//	ctx: コンテキスト（キャンセルやタイムアウトの制御に使用）
//	robotID: ロボットの識別子
//	data: センサーデータ（adapter.SensorData 型）
//
// 戻り値:
//
//	error: 書き込みに失敗した場合のエラー（成功時は nil）
func (r *RedisPublisher) PublishSensorData(ctx context.Context, robotID string, data adapter.SensorData) error {
	// data.Data（map型）を JSON 文字列に変換する。
	// Redis Streams の Values にはプリミティブ型（文字列、数値）しか
	// 直接格納できないため、複雑なデータは JSON に変換する必要がある。
	//
	// 【Go言語の知識: json.Marshal】
	// 構造体やマップを JSON バイト列に変換する。
	// 例: map[string]any{"speed": 1.5} → []byte(`{"speed":1.5}`)
	payload, err := json.Marshal(data.Data)
	if err != nil {
		return err
	}

	// Redis XADD コマンドでセンサーデータをストリームに追加。
	//
	// 【XAddArgs の各フィールドの説明】
	// Stream: 書き込み先のストリーム名
	// MaxLen: ストリームの最大エントリ数（これを超えると古いエントリが削除される）
	// Approx: true にすると、正確な MaxLen ではなく概算で削除する
	//         （厳密な削除よりも高速 — パフォーマンスとのトレードオフ）
	// Values: 書き込むフィールドの key-value ペア
	return r.client.XAdd(ctx, &redis.XAddArgs{
		Stream: sensorDataStream,
		MaxLen: 100000, // 最大10万エントリを保持（古いものは自動削除）
		Approx: true,   // 概算モードで効率的に削除
		Values: map[string]interface{}{
			"robot_id":  robotID,         // どのロボットのデータか
			"topic":     data.Topic,      // データのトピック（例: "/scan", "/imu"）
			"data_type": data.DataType,   // データの種類（例: "lidar_scan", "imu"）
			"timestamp": data.Timestamp,  // データ取得時のタイムスタンプ
			"payload":   string(payload), // JSON文字列化したセンサーデータ本体
		},
	}).Err()
}

// =============================================================================
// PublishCommand: コマンドを Redis Stream に発行するメソッド
// =============================================================================
//
// ユーザーがロボットに送ったコマンド（速度指令、ナビゲーション目標など）を
// Redis Streams に記録する。これにより：
//   - コマンド履歴の監査（誰がいつ何をしたか）
//   - バックエンドでのコマンドの再生・分析
//   - 異常なコマンドパターンの検出
//
// 引数:
//
//	ctx: コンテキスト
//	robotID: ロボットの識別子
//	cmd: コマンドデータ（adapter.Command 型）
func (r *RedisPublisher) PublishCommand(ctx context.Context, robotID string, cmd adapter.Command) error {
	// コマンドのペイロード（データ本体）を JSON 文字列に変換。
	payload, err := json.Marshal(cmd.Payload)
	if err != nil {
		return err
	}

	// Redis XADD でコマンドストリームにエントリを追加。
	return r.client.XAdd(ctx, &redis.XAddArgs{
		Stream: commandStream,
		MaxLen: 50000, // 最大5万エントリを保持
		Approx: true,  // 概算モードで効率的に削除
		Values: map[string]interface{}{
			"robot_id":  robotID,         // どのロボットへのコマンドか
			"type":      cmd.Type,        // コマンドの種類（例: "velocity_cmd"）
			"timestamp": cmd.Timestamp,   // コマンド発行時のタイムスタンプ
			"payload":   string(payload), // JSON文字列化したコマンドデータ
		},
	}).Err()
}

// =============================================================================
// Close: Redis 接続を閉じるメソッド
// =============================================================================
//
// アプリケーション終了時に呼び出す。
// 開いたリソース（接続）は必ず閉じるのがプログラミングの鉄則。
// 閉じ忘れると「リソースリーク」（資源の無駄遣い）が発生する。
func (r *RedisPublisher) Close() error {
	return r.client.Close()
}
