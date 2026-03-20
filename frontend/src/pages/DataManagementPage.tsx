// =============================================================================
// DataManagementPage.tsx — データ管理ページ
// =============================================================================
//
// 【ファイルの概要】
// このファイルは、ロボットのセンサーデータの記録（レコーディング）と
// データセットの管理を行うページです。主な機能は以下の3つ：
//
// 1. レコーディング制御: ロボットのセンサーデータの記録開始/停止
// 2. データセット一覧: 保存されたデータセットの閲覧・ダウンロード・削除
// 3. 記録履歴: 過去のレコーディングセッションの一覧表示
//
// 【なぜデータ管理が必要か？】
// 機械学習（ML）では大量のデータが必要。ロボットが収集したセンサーデータ
// （LiDAR、IMU、オドメトリ等）を記録・保存して、後から学習に使えるようにする。
//
// 【主な技術的ポイント】
// - React Query の useQuery: サーバーからデータを取得（キャッシュ付き）
// - React Query の useMutation: サーバーにデータを送信（作成・削除等）
// - queryClient.invalidateQueries: キャッシュを無効化して再取得
// - toast通知: ユーザーへの成功/失敗メッセージ
// =============================================================================

// ---------------------------------------------------------------------------
// インポート部分
// ---------------------------------------------------------------------------

// 【useState】Reactの状態管理フック。入力フォームの値を管理するために使用。
import { useState } from "react";

// 【React Query（TanStack Query）のインポート】
// React Queryは、サーバーとの通信（データ取得・送信）を簡単にするライブラリ。
//
// useQuery: サーバーからデータを「取得」するためのフック。
//   - 自動的にキャッシュ（一時保存）してくれる
//   - バックグラウンドで再取得してくれる
//   - ローディング状態やエラー状態を自動管理する
//
// useMutation: サーバーにデータを「送信」するためのフック。
//   - POST（作成）、PUT（更新）、DELETE（削除）などの操作に使う
//   - 成功時（onSuccess）やエラー時（onError）のコールバックを設定できる
//
// useQueryClient: キャッシュを直接操作するためのフック。
//   - invalidateQueries でキャッシュを無効化し、データを再取得させる
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// 【UIコンポーネント】プロジェクト内で定義された再利用可能なUI部品。
// Card系: カードレイアウト（枠線付きのコンテナ）
// Button: ボタン
// Badge: タグやラベルを表示する小さなバッジ
// Input: テキスト入力フィールド
// Select: ドロップダウン選択
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, Input, Select } from "@/components/ui/primitives";

// 【APIクライアント】バックエンドサーバーと通信するための関数群。
// datasetApi: データセットのCRUD操作（一覧取得、エクスポート、削除）
// recordingApi: レコーディングの操作（一覧取得、開始、停止）
import { datasetApi, recordingApi } from "@/services/api";

// 【useRobotStore】ロボット関連の状態管理ストア（Zustand）
import { useRobotStore } from "@/stores/robotStore";

// 【formatBytes】バイト数を人間が読みやすい形式に変換するユーティリティ関数。
// 例: 1048576 → "1.00 MB"、2048 → "2.00 KB"
import { formatBytes } from "@/lib/utils";

// 【Lucide React アイコン】
// Database: データベースアイコン（データセットセクション用）
// Play: 再生ボタンアイコン（録画開始用）
// Square: 四角アイコン（録画停止用）
// Download: ダウンロードアイコン（エクスポート用）
// Trash2: ゴミ箱アイコン（削除用）
import { Database, Play, Square, Download, Trash2 } from "lucide-react";

// 【toast】画面の端に一時的な通知メッセージを表示するライブラリ。
// toast.success("成功！") → 成功メッセージ（緑色）を表示
// toast.error("失敗！") → エラーメッセージ（赤色）を表示
import toast from "react-hot-toast";

// 【型定義のインポート】
// type キーワードは「型だけをインポートする」ことを明示する（TypeScript機能）。
// Dataset: データセットの型定義（id, name, record_count, size_bytes, tags 等）
// RecordingSession: レコーディングセッションの型定義（id, is_active, record_count 等）
// これらはビルド時に消える（JavaScriptには型情報は含まれない）。
import type { Dataset, RecordingSession } from "@/types";

// =============================================================================
// DataManagementPage コンポーネント
// =============================================================================
export function DataManagementPage() {
  // ---------------------------------------------------------------------------
  // React Query のクエリクライアント取得
  // ---------------------------------------------------------------------------
  //
  // 【useQueryClient()】
  // React Queryのキャッシュマネージャーへの参照を取得する。
  // データが変更された後に invalidateQueries() を呼んで最新データを再取得する。
  const queryClient = useQueryClient();

  // ---------------------------------------------------------------------------
  // Zustandストアからの状態取得
  // ---------------------------------------------------------------------------

  // selectedRobotId: 現在選択中のロボットID（未選択ならnull）
  const selectedRobotId = useRobotStore((s) => s.selectedRobotId);

  // robots: 登録されている全ロボットの配列
  const robots = useRobotStore((s) => s.robots);

  // ===========================================================================
  // データセット一覧の取得（useQuery）
  // ===========================================================================
  //
  // 【useQuery の仕組み】
  // useQuery はサーバーからデータを取得し、以下を自動管理する：
  //   - data: 取得したデータ
  //   - isLoading: 読み込み中かどうか
  //   - error: エラー情報
  //   - refetch: 手動で再取得する関数
  //
  // 【queryKey】
  // キャッシュのキー。["datasets"] という配列をキーにして、
  // 同じキーの useQuery が複数あっても一度だけ通信する（共有キャッシュ）。
  //
  // 【queryFn】
  // 実際にデータを取得する非同期関数（async関数）。
  // APIを呼び出してデータを返す。
  //
  // 【= [] のデフォルト値】
  // data が undefined（まだ取得完了していない）場合に空配列を使う。
  // これにより、後続のコードで undefined チェックが不要になる。

  // Datasets
  const { data: datasets = [] } = useQuery<Dataset[]>({
    queryKey: ["datasets"],
    queryFn: async () => {
      // datasetApi.list() でバックエンドの /api/v1/datasets エンドポイントを呼ぶ
      const res = await datasetApi.list();
      // レスポンスの形式に応じてデータを取り出す
      // サーバーが { items: [...] } で返す場合と、直接配列で返す場合に対応
      // 【as unknown as ...】二重アサーション：型を一旦unknownにしてから目的の型に変換
      return (res.data as unknown as { items?: Dataset[] }).items ?? res.data;
    },
  });

  // ===========================================================================
  // レコーディングセッション一覧の取得（useQuery）
  // ===========================================================================
  //
  // 【useQuery<RecordingSession[]>】
  // ジェネリクス<RecordingSession[]>で、取得されるデータの型を指定する。

  // Recordings
  const { data: recordings = [] } = useQuery<RecordingSession[]>({
    queryKey: ["recordings"],
    queryFn: async () => {
      const res = await recordingApi.list();
      return (res.data as unknown as { items?: RecordingSession[] }).items ?? res.data;
    },
  });

  // ===========================================================================
  // レコーディング開始（useMutation）
  // ===========================================================================
  //
  // 【useMutation の仕組み】
  // useMutation はサーバーにデータを送信（POST/PUT/DELETE）するためのフック。
  // useQuery と異なり、自動実行されない。手動で .mutate() を呼んで実行する。
  //
  // 【mutationFn】
  // 実際にAPIを呼び出す非同期関数。
  //
  // 【onSuccess コールバック】
  // APIの呼び出しが成功した後に実行される処理。
  // invalidateQueries でキャッシュを無効化→自動的に最新データを再取得する。
  //
  // 【onError コールバック】
  // APIの呼び出しが失敗した場合に実行される処理。
  // エラーメッセージを表示する。

  // Start recording
  // recRobotId: レコーディング対象のロボットID（フォーム入力値）
  const [recRobotId, setRecRobotId] = useState("");
  // recName: レコーディングセッション名（フォーム入力値）
  const [recName, setRecName] = useState("");

  const startRec = useMutation({
    // mutationFn: レコーディング開始APIを呼ぶ
    // robot_id: 対象ロボットのID（フォームで選択されたID、または現在選択中のID）
    // sensor_types: 記録するセンサーの種類（LiDAR、IMU、オドメトリ）
    mutationFn: () =>
      recordingApi.start({
        robot_id: recRobotId || selectedRobotId || "",
        sensor_types: ["lidar", "imu", "odometry"],
      }),
    onSuccess: () => {
      // レコーディング一覧のキャッシュを無効化（最新データを再取得させる）
      queryClient.invalidateQueries({ queryKey: ["recordings"] });
      toast.success("Recording started");
      // セッション名をクリア
      setRecName("");
    },
    onError: () => toast.error("Failed to start recording"),
  });

  // ===========================================================================
  // レコーディング停止（useMutation）
  // ===========================================================================

  // Stop recording
  const stopRec = useMutation({
    // mutationFn に引数(id)を受け取る例。
    // .mutate(id) で呼び出すと、そのidがここに渡される。
    mutationFn: (id: string) => recordingApi.stop(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recordings"] });
      toast.success("Recording stopped");
    },
  });

  // ===========================================================================
  // データセット削除（useMutation）
  // ===========================================================================

  // Delete dataset
  const deleteDs = useMutation({
    mutationFn: (id: string) => datasetApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      toast.success("Dataset deleted");
    },
  });

  // ===========================================================================
  // JSX（レンダリング部分）
  // ===========================================================================
  //
  // 【ページのレイアウト構成】
  // ┌─────────────────────────────────────────┐
  // │ Data Management（タイトル）               │
  // ├──────────────────┬──────────────────────┤
  // │ Recording        │ Datasets (n)          │
  // │ ・ロボット選択   │ ・データセット一覧     │
  // │ ・開始ボタン     │ ・DL/削除ボタン       │
  // │ ・アクティブ一覧 │                        │
  // ├──────────────────┴──────────────────────┤
  // │ Recording History（過去の記録一覧）       │
  // └─────────────────────────────────────────┘
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Data Management</h1>

      {/* 上段: レコーディング制御とデータセット一覧を横並びで配置 */}
      {/* lg:grid-cols-2: 大画面（1024px以上）で2列レイアウト */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* ================================================================= */}
        {/* レコーディング制御カード                                          */}
        {/* ================================================================= */}
        {/* Recording control */}
        <Card>
          <CardHeader>
            {/* カードのタイトル行にアイコンとテキストを横並びで表示 */}
            <CardTitle className="flex items-center gap-2 text-base">
              <Play className="h-4 w-4" />
              Recording
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* ロボット選択とセッション名の入力フォーム（横並び） */}
            <div className="flex gap-2">
              {/* ロボット選択ドロップダウン */}
              <Select value={recRobotId} onChange={(e) => setRecRobotId(e.target.value)} className="flex-1">
                <option value="">Select robot</option>
                {/* robots配列をmap()で展開し、各ロボットを<option>として表示 */}
                {robots.map((r) => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </Select>
              {/* セッション名の入力欄 */}
              <Input
                placeholder="Session name"
                value={recName}
                onChange={(e) => setRecName(e.target.value)}
                className="flex-1"
              />
            </div>

            {/* レコーディング開始ボタン */}
            {/* disabled: ボタンを無効にする条件 */}
            {/* startRec.isPending: API呼び出し中は二重送信を防ぐ */}
            {/* (!recRobotId && !selectedRobotId): ロボットが未選択なら無効 */}
            <Button
              onClick={() => startRec.mutate()}
              disabled={startRec.isPending || (!recRobotId && !selectedRobotId)}
              className="gap-2"
            >
              <Play className="h-4 w-4" />
              Start Recording
            </Button>

            {/* アクティブなレコーディング一覧 */}
            {/* .filter(): 配列から条件に合う要素だけを抽出する */}
            {/* (r) => r.is_active: アクティブ（録画中）のセッションだけを抽出 */}
            {/* Active recordings */}
            <div className="space-y-2">
              {recordings
                .filter((r) => r.is_active)
                .map((r) => (
                  <div key={r.id} className="flex items-center justify-between rounded-md border p-2">
                    <div>
                      {/* r.id.slice(0, 8): UUIDの先頭8文字だけ表示（表示をコンパクトに） */}
                      <p className="text-sm font-medium">Recording {r.id.slice(0, 8)}</p>
                      <p className="text-xs text-muted-foreground">
                        {/* ?? 0: record_count がnull/undefinedなら0を表示 */}
                        {r.record_count ?? 0} points
                      </p>
                    </div>
                    {/* 停止ボタン: クリックでstopRec.mutate(r.id)を呼ぶ */}
                    {/* variant="destructive": 危険な操作であることを赤色で示す */}
                    <Button size="sm" variant="destructive" onClick={() => stopRec.mutate(r.id)} className="gap-1">
                      <Square className="h-3 w-3" />
                      Stop
                    </Button>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* ================================================================= */}
        {/* データセット一覧カード                                            */}
        {/* ================================================================= */}
        {/* Datasets */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Database className="h-4 w-4" />
              {/* datasets.length: データセットの総数を表示 */}
              Datasets ({datasets.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* 条件付きレンダリング: データセットが0件なら案内メッセージ、あれば一覧表示 */}
            {datasets.length === 0 ? (
              <p className="text-sm text-muted-foreground">No datasets yet. Start a recording first.</p>
            ) : (
              <div className="space-y-2">
                {datasets.map((ds) => (
                  <div key={ds.id} className="flex items-center justify-between rounded-md border p-3">
                    {/* データセット情報（名前、レコード数、サイズ、タグ） */}
                    <div className="min-w-0 flex-1">
                      {/* truncate: テキストが長い場合に「...」で省略表示 */}
                      <p className="truncate font-medium text-sm">{ds.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {/* formatBytesでサイズを読みやすい形式に変換 */}
                        {ds.record_count ?? 0} records · {formatBytes(ds.size_bytes ?? 0)}
                      </p>
                      {/* タグ一覧: tags配列をBadgeコンポーネントで表示 */}
                      {/* ?.map(): tags が undefined でもエラーにならない（Optional Chaining） */}
                      <div className="mt-1 flex gap-1">
                        {ds.tags?.map((t) => (
                          <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>
                        ))}
                      </div>
                    </div>
                    {/* アクションボタン: ダウンロードと削除 */}
                    <div className="flex gap-1">
                      {/* ダウンロードボタン: parquet形式でエクスポート */}
                      <Button size="icon" variant="ghost" onClick={() => datasetApi.export(ds.id, "parquet")}>
                        <Download className="h-4 w-4" />
                      </Button>
                      {/* 削除ボタン: deleteDs.mutate(ds.id) で削除APIを呼ぶ */}
                      <Button size="icon" variant="ghost" onClick={() => deleteDs.mutate(ds.id)}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* =================================================================== */}
      {/* 過去のレコーディング履歴カード                                      */}
      {/* =================================================================== */}
      {/* Past recordings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recording History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {/* is_active が false（終了済み）のレコーディングだけを表示 */}
            {recordings
              .filter((r) => !r.is_active)
              .map((r) => (
                <div key={r.id} className="flex items-center justify-between rounded-md border p-2 text-sm">
                  <span className="font-medium">Recording {r.id.slice(0, 8)}</span>
                  <div className="flex items-center gap-3 text-muted-foreground">
                    {/* 記録されたデータポイント数 */}
                    <span>{r.record_count ?? 0} pts</span>
                    {/* データサイズ */}
                    <span>{formatBytes(r.size_bytes ?? 0)}</span>
                    {/* ステータスバッジ: 完了なら"default"色、アクティブなら"destructive"（赤）色 */}
                    {/* 三項演算子: 条件 ? 真の値 : 偽の値 */}
                    <Badge variant={r.stopped_at ? "default" : "destructive"}>
                      {r.stopped_at ? "completed" : "active"}
                    </Badge>
                  </div>
                </div>
              ))}
            {/* 過去のレコーディングが0件の場合のメッセージ */}
            {/* .filter().length === 0: フィルタ結果が空かどうかをチェック */}
            {recordings.filter((r) => !r.is_active).length === 0 && (
              <p className="text-sm text-muted-foreground">No past recordings.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
