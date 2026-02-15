// =============================================================================
// ファイル: operation_lock.go
// パッケージ: safety（安全機能パッケージ）
//
// 【このファイルの概要】
// ロボットの「操作ロック（Operation Lock）」機能を管理するファイルです。
// 一台のロボットを同時に複数のユーザーが操作すると危険です。
// そのため、「一人のユーザーだけがロボットを操作できる」ようにする
// 排他制御（exclusive access）を実装しています。
//
// 【日常の例え】
// カラオケのリモコンのようなものです。
// リモコンを持っている人だけが曲を選べます。
// 使い終わったらリモコンを返し、一定時間操作しないと自動的に返却されます。
//
// 【主な機能】
// - ロックの取得（Acquire）: ロボットの操作権を取得する
// - ロックの解放（Release）: ロボットの操作権を返す
// - ロックの確認（CheckLock）: 操作権を持っているか確認する
// - ロック情報の取得（GetLockInfo）: 誰がロックしているかを確認する
// - 期限切れロックの自動クリーンアップ（cleanupExpired）
//
// 【設計パターン】
// このファイルでは「リースパターン（Lease Pattern）」を使っています。
// ロックには有効期限があり、期限が切れると自動的に解放されます。
// これにより、ユーザーがブラウザを閉じた場合でもロックが残り続ける問題を防ぎます。
// =============================================================================
package safety

import (
// fmt: フォーマット済み文字列の入出力パッケージ
// fmt.Errorf() でフォーマット済みのエラーメッセージを作成するために使います。
// Printf の「f」は format の略です。
"fmt"

// sync: 同期プリミティブ（ロックなど）を提供するパッケージ
// RWMutex（読み書きロック）を使って、mapへの安全なアクセスを実現します。
"sync"

// time: 時刻と時間に関するパッケージ
// ロックの有効期限の管理や、定期的なクリーンアップ処理に使います。
// time.Duration（期間）、time.Time（時刻）、time.Ticker（定期タイマー）など。
"time"

// zap: 高性能ロガー（Uber社製）
// 構造化ログを出力します。ロックの取得・解放などのイベントを記録します。
"go.uber.org/zap"
)

// =============================================================================
// LockInfo - ロック情報を保持する構造体
// =============================================================================
//
// 【この構造体の役割】
// 「誰が」「いつ」「どのロボットの」ロックを取得したかの情報を保持します。
// ロックの有効期限も含まれており、期限切れの判定に使います。
type LockInfo struct {
// RobotID: ロックされているロボットのID
RobotID string

// UserID: ロックを取得したユーザーのID
UserID string

// AcquiredAt: ロックを取得した時刻
// time.Time型はGoの標準的な時刻表現です。
AcquiredAt time.Time

// ExpiresAt: ロックの有効期限
// この時刻を過ぎると、ロックは自動的に無効になります。
ExpiresAt time.Time
}

// =============================================================================
// OperationLock - 操作ロックマネージャー構造体
// =============================================================================
//
// 【この構造体の役割】
// すべてのロボットの操作ロックを管理する中心的な構造体です。
// ロックの取得・解放・確認・クリーンアップの全機能を提供します。
type OperationLock struct {
// mu: 読み書きロック
// locks mapへの同時アクセスを安全にするためのミューテックスです。
// 詳しくは estop.go のRWMutexの説明を参照してください。
mu sync.RWMutex

// locks: ロボットIDからロック情報へのmap
// キー: ロボットID（string）
// 値: ロック情報へのポインタ（*LockInfo）
//
// 【ポインタを値にする理由】
// *LockInfo（ポインタ）を使うことで：
// 1. ロック情報を更新する時にコピーではなく元のデータを変更できる
// 2. nilで「ロックなし」を表現できる
// 3. メモリ効率が良い（大きな構造体をコピーしない）
locks map[string]*LockInfo // robot_id -> lock info

// timeout: ロックの有効期限（デフォルトの継続時間）
// time.Duration型は「期間」を表します。
// 例: 5 * time.Minute = 5分
timeout time.Duration

// logger: ログ出力用のロガー
logger *zap.Logger
}

// =============================================================================
// NewOperationLock - OperationLockのコンストラクタ
// =============================================================================
//
// 【引数】
// - timeout: ロックの有効期限（例: 5分）
//   この時間内に操作がなければ、ロックは自動的に期限切れになります。
// - logger: ログ出力用のロガー
//
// 【戻り値】
// - *OperationLock: 初期化されたOperationLockへのポインタ
func NewOperationLock(timeout time.Duration, logger *zap.Logger) *OperationLock {
ol := &OperationLock{
// make(map[...]): mapを初期化する
// mapは使う前に必ず make() で初期化する必要があります。
locks:   make(map[string]*LockInfo),
timeout: timeout,
logger:  logger,
}
return ol
}

// =============================================================================
// StartCleanup - 期限切れロックの定期クリーンアップを開始する
// =============================================================================
//
// 【この関数の役割】
// バックグラウンドで定期的に実行され、期限切れのロックを自動で削除します。
// ユーザーがブラウザを閉じたり、ネットワークが切れた場合に、
// ロックが永遠に残ってしまうのを防ぎます。
//
// 【引数: done チャネル】
// done <-chan struct{} は「停止信号を受け取るためのチャネル」です。
//
// 【チャネル（channel）とは？】
// チャネルはゴルーチン間でデータをやり取りするための「パイプ」です。
// 「<-chan struct{}」は「受信専用チャネル」を意味します。
// struct{} は「空の構造体」で、メモリを消費しません。
// 「データは送らないけど、信号（通知）だけ送りたい」時に使います。
//
// 使い方：
//   done := make(chan struct{})
//   manager.StartCleanup(done)
//   // ... アプリケーション実行中 ...
//   close(done) // ← これでクリーンアップが停止する
func (o *OperationLock) StartCleanup(done <-chan struct{}) {
// go func() { ... }()
//
// 【ゴルーチン（goroutine）とは？】
// 「go」キーワードを付けて関数を呼ぶと、その関数は
// 新しいゴルーチン（軽量スレッド）で並行に実行されます。
// メインの処理は止まらず、すぐに次の行に進みます。
//
// 【無名関数（anonymous function）】
// func() { ... }() は、名前のない関数をその場で定義して実行します。
// JavaScriptのアロー関数 (() => { ... })() に似ています。
go func() {
// time.NewTicker(): 一定間隔で信号を送り続けるタイマーを作成する
// 10秒ごとに ticker.C チャネルに現在時刻が送信されます。
//
// 【Ticker vs Timer の違い】
// - Ticker: 繰り返し発火する（10秒ごと、10秒ごと、...）
// - Timer: 1回だけ発火する
ticker := time.NewTicker(10 * time.Second)

// defer ticker.Stop(): ゴルーチン終了時にTickerを停止する
// Tickerは使い終わったら必ず Stop() する必要があります。
// 停止しないと、リソースリーク（メモリの無駄遣い）になります。
defer ticker.Stop()

// 無限ループでクリーンアップを繰り返す
for {
// select: 複数のチャネルからの受信を待ち受ける
//
// 【select文とは？】
// 複数のチャネルを同時に監視し、どれか一つからデータが来たら、
// そのcase文を実行します。
// switch文のチャネル版と考えてください。
//
// ここでは2つのチャネルを監視しています：
// 1. done: 停止信号（アプリケーション終了時）
// 2. ticker.C: 10秒ごとの定期タイマー
select {
case <-done:
// done チャネルが閉じられた（close(done)された）場合
// ゴルーチンを終了する（return でゴルーチンが終了）
return
case <-ticker.C:
// 10秒経過した場合、期限切れロックをクリーンアップする
o.cleanupExpired()
}
}
}()
}

// =============================================================================
// Acquire - ロボットの操作ロックを取得する
// =============================================================================
//
// 【この関数の動作フロー】
// 1. 既存のロックがあるか確認する
//    a. あり＋有効期限内＋同じユーザー → ロックを延長する
//    b. あり＋有効期限内＋別のユーザー → エラーを返す（他の人が使用中）
//    c. あり＋期限切れ → 古いロックを削除して新規取得
// 2. 既存のロックがない → 新規ロックを取得する
//
// 【戻り値】
// - *LockInfo: 取得（または延長）されたロック情報
// - error: ロック取得に失敗した場合のエラー
func (o *OperationLock) Acquire(robotID, userID string) (*LockInfo, error) {
// 書き込みロックを取得（mapの読み書きを行うため）
o.mu.Lock()

// defer o.mu.Unlock(): 関数終了時に必ずロックを解放する
// この関数は複数のreturn文があるため、deferを使うと安全です。
// どのreturn文を通っても、Unlock()が必ず実行されます。
defer o.mu.Unlock()

// 現在時刻を取得する
// time.Now(): 現在の時刻をtime.Time型で返す
now := time.Now()

// --- 既存のロックがあるか確認する ---

// map からの値取得（カンマOKイディオム）
// existing: ロック情報（*LockInfo型）
// ok: キーが存在するか（bool型）
if existing, ok := o.locks[robotID]; ok {
// 有効期限がまだ残っているか確認する
// After(now): ExpiresAt が now より後かどうか → まだ有効
if existing.ExpiresAt.After(now) {
if existing.UserID == userID {
// 同じユーザーがロックを持っている場合 → ロックを延長する
// これにより、操作を続けている間はロックが期限切れにならない
existing.ExpiresAt = now.Add(o.timeout)

o.logger.Debug("Operation lock extended",
zap.String("robot_id", robotID),
zap.String("user_id", userID),
)
return existing, nil
}

// 別のユーザーがロックを持っている場合 → エラーを返す
// fmt.Errorf(): フォーマット文字列からエラーを生成する
// %s: 文字列のプレースホルダー
return existing, fmt.Errorf("robot %s is locked by user %s until %s",
robotID, existing.UserID, existing.ExpiresAt.Format(time.RFC3339))
// time.RFC3339: 国際標準の時刻フォーマット
// 例: "2026-02-15T14:30:00+09:00"
}
// ロックが期限切れの場合 → 削除して新規取得に進む
delete(o.locks, robotID)
}

// --- 新規ロックを取得する ---

// &LockInfo{...}: LockInfo構造体を作成してそのポインタを取得する
// 「&」はアドレス演算子で、「この値のメモリアドレスをください」という意味です。
lock := &LockInfo{
RobotID:    robotID,
UserID:     userID,
AcquiredAt: now,
// now.Add(o.timeout): 現在時刻にタイムアウト期間を加算する
// 例: 現在14:00 + 5分 → 14:05に期限切れ
ExpiresAt: now.Add(o.timeout),
}

// mapにロック情報を保存する
o.locks[robotID] = lock

o.logger.Info("Operation lock acquired",
zap.String("robot_id", robotID),
zap.String("user_id", userID),
// zap.Time(): time.Time型の値をログに含める
zap.Time("expires_at", lock.ExpiresAt),
)

return lock, nil
}

// =============================================================================
// Release - ロボットの操作ロックを解放する
// =============================================================================
//
// 【この関数の安全性】
// ロックの所有者だけがロックを解放できます。
// 他のユーザーが勝手に解放することはできません。
//
// 【戻り値】
// - error: 自分のロックでない場合のエラー、またはnil
func (o *OperationLock) Release(robotID, userID string) error {
o.mu.Lock()
defer o.mu.Unlock()

// ロックが存在するか確認する
lock, ok := o.locks[robotID]
if !ok {
// ロックが存在しない場合 → エラーなし（べき等：何度呼んでも安全）
// 【べき等（idempotent）とは？】
// 同じ操作を何度実行しても結果が変わらない性質です。
// REST APIの設計で重要な概念です。
return nil // No lock to release
}

// ロックの所有者を確認する
if lock.UserID != userID {
// 別のユーザーのロックは解放できない → エラーを返す
return fmt.Errorf("cannot release lock: owned by %s, requested by %s", lock.UserID, userID)
}

// ロックを削除する（mapから除去）
delete(o.locks, robotID)

o.logger.Info("Operation lock released",
zap.String("robot_id", robotID),
zap.String("user_id", userID),
)
return nil
}

// =============================================================================
// CheckLock - ユーザーがロボットのロックを持っているか確認する
// =============================================================================
//
// 【この関数の用途】
// コマンドを送信する前に、送信者がロックを持っているか確認します。
// ロックを持っていないユーザーからのコマンドは拒否されるべきです。
//
// 【読み取りロック（RLock）を使う理由】
// この関数はmapを読み取るだけなので、RLock()を使います。
// 複数のゴルーチンが同時にCheckLockを呼び出せるため、パフォーマンスが向上します。
func (o *OperationLock) CheckLock(robotID, userID string) bool {
o.mu.RLock()
defer o.mu.RUnlock()

lock, ok := o.locks[robotID]
if !ok {
// ロックが存在しない → false
return false
}

// ロックの所有者が一致し、かつ有効期限内であることを確認する
// &&: 論理AND演算子（両方trueの場合にtrueを返す）
return lock.UserID == userID && lock.ExpiresAt.After(time.Now())
}

// =============================================================================
// GetLockInfo - ロボットのロック情報を取得する
// =============================================================================
//
// 【この関数の用途】
// ロボットが誰にロックされているかを表示するために使います。
// 例えば、UIで「このロボットはユーザーAが操作中です」と表示するため。
//
// 【戻り値】
// - *LockInfo: ロック情報（ロックがないか期限切れの場合は nil）
//
// 【nil とは？】
// nil は「何も指していないポインタ」です。
// Python の None、JavaScript の null に相当します。
// ポインタ型、スライス型、map型、チャネル型、インターフェース型で使えます。
func (o *OperationLock) GetLockInfo(robotID string) *LockInfo {
o.mu.RLock()
defer o.mu.RUnlock()

lock, ok := o.locks[robotID]

// ロックが存在しない、または期限切れの場合は nil を返す
// ||: 論理OR演算子（どちらか一方がtrueならtrueを返す）
// Before(now): ExpiresAt が now より前 → 期限切れ
if !ok || lock.ExpiresAt.Before(time.Now()) {
return nil
}
return lock
}

// =============================================================================
// cleanupExpired - 期限切れのロックをクリーンアップする（内部関数）
// =============================================================================
//
// 【この関数の役割】
// StartCleanup()から定期的に呼び出され、期限切れのロックを自動削除します。
//
// 【小文字で始まる関数名について】
// Goでは、名前が小文字で始まる関数はパッケージ外からアクセスできません。
// これは「プライベート関数」と同じ意味です。
// cleanupExpired は外部から直接呼ぶ必要がないため、小文字で始めています。
//
// 【大文字 vs 小文字のルール（エクスポート）】
// - 大文字で始まる名前（例: Acquire, Release）→ パッケージ外からアクセス可能（public）
// - 小文字で始まる名前（例: cleanupExpired, mu）→ パッケージ内からのみアクセス可能（private）
func (o *OperationLock) cleanupExpired() {
// 書き込みロック（mapからの削除があるため）
o.mu.Lock()
defer o.mu.Unlock()

now := time.Now()

// map をイテレーションしながら期限切れのロックを削除する
//
// 【Goのmap削除の安全性】
// Goでは、rangeでmapをイテレーション中にdelete()を呼んでも安全です。
// これは言語仕様で保証されています。
// （注意：他の言語では安全でないことがあります）
for robotID, lock := range o.locks {
// Before(now): ロックの期限が現在時刻より前 → 期限切れ
if lock.ExpiresAt.Before(now) {
// 期限切れのロックを削除する
delete(o.locks, robotID)
o.logger.Info("Expired operation lock cleaned up",
zap.String("robot_id", robotID),
zap.String("user_id", lock.UserID),
)
}
}
}
