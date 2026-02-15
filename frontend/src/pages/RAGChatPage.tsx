// =============================================================================
// RAGChatPage.tsx — RAGチャットページ
// =============================================================================
//
// 【ファイルの概要】
// このファイルは RAG（Retrieval-Augmented Generation）チャット機能のページです。
//
// 【RAGとは？】
// RAG = Retrieval-Augmented Generation（検索拡張生成）
// ユーザーがアップロードしたドキュメント（PDF、テキスト等）の内容をAIが理解し、
// そのドキュメントの内容に基づいて質問に回答する仕組み。
// 一般的なチャットAIと違い、ユーザー独自のドキュメントの情報を基に回答できる。
//
// 【このページの3つの機能】
// 1. チャット: ユーザーが質問を入力し、AIが回答する（SSEストリーミング対応）
// 2. ドキュメント管理: PDF/TXT/MDファイルのアップロード・削除
// 3. リアルタイム応答: SSE（Server-Sent Events）でAIの回答を少しずつ表示
//
// 【主な技術的ポイント】
// - SSE（Server-Sent Events）ストリーミング: AIの回答をリアルタイムで受信
// - ReadableStream: fetch APIのレスポンスをストリームとして読み取る
// - useRef: DOMへの直接参照（自動スクロール用）
// - useEffect: 副作用の管理（メッセージ変更時の自動スクロール）
// - useMutation: ファイルアップロード・削除のAPI通信
// - フォールバック処理: ストリーミング失敗時の代替処理
// =============================================================================

// ---------------------------------------------------------------------------
// インポート部分
// ---------------------------------------------------------------------------

// 【useState】状態管理フック。チャットメッセージ、入力テキスト、ストリーミング状態を管理。
// 【useRef】DOMへの参照を保持するフック。スクロール位置の制御に使用。
// 【useEffect】副作用（side effect）を処理するフック。
//   コンポーネントの描画後に実行したい処理（スクロール等）を定義する。
import { useState, useRef, useEffect } from "react";

// 【React Query】サーバー通信のためのライブラリ。
// useMutation: ファイルアップロードや削除などの「変更」操作に使用。
// useQuery: ドキュメント一覧の「取得」に使用。
// useQueryClient: キャッシュの操作（無効化→再取得）に使用。
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// 【UIコンポーネント】再利用可能なUI部品。
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from "@/components/ui/primitives";

// 【ragApi】RAG関連のAPIクライアント。
// - ragApi.listDocuments(): ドキュメント一覧を取得
// - ragApi.uploadDocument(file): ドキュメントをアップロード
// - ragApi.deleteDocument(id): ドキュメントを削除
// - ragApi.query(query, topK): 質問を送信して回答を取得（非ストリーミング版）
import { ragApi } from "@/services/api";

// 【Lucide React アイコン】
// Send: 送信アイコン（メッセージ送信ボタン）
// Upload: アップロードアイコン（ファイルアップロード）
// FileText: ファイルアイコン（ドキュメント表示）
// Trash2: ゴミ箱アイコン（削除）
// Bot: ロボットアイコン（AIの回答に表示）
// User (UserIconとしてリネーム): ユーザーアイコン
// Loader2: スピナー（読み込み中のアニメーション）
import { Send, Upload, FileText, Trash2, Bot, User as UserIcon, Loader2 } from "lucide-react";

// 【toast】ポップアップ通知。成功/失敗メッセージを画面端に表示する。
import toast from "react-hot-toast";

// 【RAGDocument型】ドキュメントのデータ構造を定義した型。
// id: ドキュメントID、title: タイトル、chunk_count: 分割チャンク数など。
import type { RAGDocument } from "@/types";

// =============================================================================
// ChatMessage インターフェース
// =============================================================================
//
// 【interfaceとは？】
// TypeScriptでオブジェクトの「形」を定義する仕組み。
// このインターフェースは「チャットメッセージはroleとcontentを持つ」と宣言している。
//
// 【role: "user" | "assistant"】
// ユニオンリテラル型。roleは"user"か"assistant"のどちらかしか取れない。
// "user" = ユーザーが送信したメッセージ
// "assistant" = AIが生成した回答
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

// =============================================================================
// RAGChatPage コンポーネント
// =============================================================================
export function RAGChatPage() {
  // ---------------------------------------------------------------------------
  // フックの初期化
  // ---------------------------------------------------------------------------

  // React Queryのキャッシュマネージャー
  const queryClient = useQueryClient();

  // 【チャットメッセージの状態】
  // messages: 会話履歴の配列（ユーザーとAIのメッセージが交互に入る）
  // setMessages: messagesを更新する関数
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // 【入力テキストの状態】
  // input: テキスト入力フィールドの現在のテキスト
  const [input, setInput] = useState("");

  // 【ストリーミング状態】
  // isStreaming: AIが回答を生成中かどうか（trueなら入力を無効化する）
  const [isStreaming, setIsStreaming] = useState(false);

  // 【useRef — DOM参照】
  // chatEndRef: チャット領域の末端にある空のdiv要素への参照。
  // スクロール位置をこの要素に合わせることで、最新メッセージが見えるようにする。
  // 初期値はnull（まだDOM要素が描画されていないため）。
  // HTMLDivElement: TypeScriptのDOM型で、<div>要素を表す。
  const chatEndRef = useRef<HTMLDivElement>(null);

  // ===========================================================================
  // ドキュメント一覧の取得（useQuery）
  // ===========================================================================

  // Documents
  const { data: documents = [] } = useQuery<RAGDocument[]>({
    queryKey: ["rag-documents"],
    queryFn: async () => {
      const res = await ragApi.listDocuments();
      return (res.data as unknown as { items?: RAGDocument[] }).items ?? res.data;
    },
  });

  // ===========================================================================
  // ドキュメントアップロード（useMutation）
  // ===========================================================================
  //
  // 【File型】
  // ブラウザのFile APIで定義された型。<input type="file">で選択されたファイルを表す。
  // name（ファイル名）、size（サイズ）、type（MIMEタイプ）などのプロパティを持つ。

  // Upload
  const uploadMut = useMutation({
    mutationFn: (file: File) => ragApi.uploadDocument(file),
    onSuccess: () => {
      // アップロード成功後、ドキュメント一覧のキャッシュを無効化して再取得
      queryClient.invalidateQueries({ queryKey: ["rag-documents"] });
      toast.success("Document uploaded & processed");
    },
    onError: () => toast.error("Upload failed"),
  });

  // ===========================================================================
  // ドキュメント削除（useMutation）
  // ===========================================================================

  // Delete document
  const deleteMut = useMutation({
    mutationFn: (id: string) => ragApi.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rag-documents"] });
      toast.success("Document deleted");
    },
  });

  // ===========================================================================
  // 自動スクロール（useEffect）
  // ===========================================================================
  //
  // 【useEffect(callback, dependencies)】
  // 副作用フック。依存配列（第2引数）の値が変わるたびにコールバックが実行される。
  // ここでは messages が変わるたびに（= 新しいメッセージが追加されるたびに）
  // チャット領域を最下部までスクロールする。
  //
  // 【.scrollIntoView()】
  // DOM APIのメソッド。指定した要素が画面内に見えるようにスクロールする。
  // { behavior: "smooth" } でなめらかにスクロールする。
  //
  // 【chatEndRef.current?.scrollIntoView(...)】
  // chatEndRef.current: refに紐づいたDOM要素（<div ref={chatEndRef} />）
  // ?. (Optional Chaining): currentがnullの場合は何もしない（エラーを防ぐ）

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ===========================================================================
  // メッセージ送信処理（SSEストリーミング対応）
  // ===========================================================================
  //
  // 【SSE（Server-Sent Events）とは？】
  // サーバーからクライアントへ一方向にデータをリアルタイム送信する仕組み。
  // WebSocketと異なり、HTTPの標準的な仕組みで実現できる。
  // AIの回答を「少しずつ」受信して表示するのに適している。
  //
  // 【async関数とは？】
  // 非同期関数。awaitキーワードを使って、非同期処理の完了を待てる。
  // API通信など時間がかかる処理で使う。

  // Send query with SSE streaming
  const handleSend = async () => {
    // .trim(): 文字列の前後の空白を除去する
    const query = input.trim();
    // 空の質問やストリーミング中は何もしない（ガード節）
    if (!query || isStreaming) return;

    // 入力フィールドをクリアする
    setInput("");
    // ユーザーのメッセージを会話履歴に追加する
    // 【関数型更新 (prev) => [...]】
    // setMessages に関数を渡すと、現在の状態(prev)を引数として受け取れる。
    // これにより「現在のメッセージ配列 + 新しいメッセージ」の配列を安全に作成できる。
    // [...prev, newItem] はスプレッド演算子で、prevの全要素を展開して新しい配列を作る。
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setIsStreaming(true);

    // Add empty assistant message
    // AIの回答用に空のメッセージを先に追加する（ストリーミングで少しずつ内容が埋まる）
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    // -----------------------------------------------------------------------
    // fetch API でSSEストリーミングリクエストを送信
    // -----------------------------------------------------------------------
    try {
      // 【fetch API】
      // ブラウザ標準のHTTP通信関数。サーバーにリクエストを送りレスポンスを受け取る。
      // 第1引数: URL（APIエンドポイント）
      // 第2引数: オプション（HTTPメソッド、ヘッダー、ボディ等）
      const response = await fetch("/api/v1/rag/query/stream", {
        method: "POST",  // POSTメソッド（データを送信する）
        headers: {
          "Content-Type": "application/json",  // JSONデータを送ることを宣言
          // 【Authorization ヘッダー】認証トークンをサーバーに送る
          // localStorage: ブラウザにデータを永続保存するAPI
          // Bearer: トークン認証の種類（Bearer Token方式）
          Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}`,
        },
        // 【JSON.stringify()】JavaScriptオブジェクトをJSON文字列に変換する
        // query: ユーザーの質問テキスト
        // top_k: 検索で上位何件のドキュメントチャンクを参照するか
        body: JSON.stringify({ query, top_k: 5 }),
      });

      // レスポンスが正常でなければエラーをスローする
      // response.ok: HTTPステータスコードが200-299ならtrue
      if (!response.ok) throw new Error("Query failed");

      // -------------------------------------------------------------------
      // ReadableStream でレスポンスを少しずつ読み取る
      // -------------------------------------------------------------------
      //
      // 【ReadableStream とは？】
      // データを少しずつ（チャンクごとに）読み取れるストリームオブジェクト。
      // 全データの到着を待たずに、届いた分から処理を開始できる。
      // AIの長い回答を「少しずつ受信→少しずつ画面に表示」するのに最適。
      //
      // 【response.body】
      // fetchのレスポンスのボディ部分をReadableStreamとして取得する。
      //
      // 【.getReader()】
      // ReadableStreamから ReadableStreamDefaultReader を取得する。
      // このreaderを使ってデータを読み取る（read()メソッド）。
      const reader = response.body?.getReader();

      // 【TextDecoder】
      // バイトデータ（Uint8Array）をテキスト（文字列）に変換するAPI。
      // ネットワークから届くデータはバイナリなので、文字列に変換が必要。
      const decoder = new TextDecoder();

      if (reader) {
        // buffer: 不完全な行を一時保管するバッファ
        // SSEのデータは改行区切りだが、チャンクの境界が行の途中に来ることがある
        let buffer = "";

        // 【while (true) + break パターン】
        // 無限ループで読み取りを続け、done が true（ストリーム終了）になったら break
        while (true) {
          // 【reader.read()】
          // ストリームから次のチャンクを読み取る。
          // 返り値: { done: boolean, value: Uint8Array | undefined }
          // done: ストリームの終端に達したらtrue
          // value: 読み取ったバイトデータ
          const { done, value } = await reader.read();
          if (done) break;

          // 【decoder.decode(value, { stream: true })】
          // バイトデータを文字列にデコード。
          // stream: true はマルチバイト文字が途中で切れている場合に対応する。
          buffer += decoder.decode(value, { stream: true });

          // バッファを改行で分割して行ごとに処理する
          const lines = buffer.split("\n");
          // 最後の要素は不完全な可能性があるので、次回のバッファに残す
          // pop(): 配列の最後の要素を取り出す（元の配列からは削除される）
          buffer = lines.pop() ?? "";

          // 各行を処理する（SSE形式のデータをパースする）
          for (const line of lines) {
            // 【SSE形式】
            // SSEでは各メッセージが "data: " で始まる行として送られる。
            // 例: "data: {"token": "こんにちは"}"
            // 例: "data: [DONE]" → ストリーム終了の合図
            if (line.startsWith("data: ")) {
              // "data: " の6文字を除去してデータ本体を取得
              const data = line.slice(6);
              // ストリーミング完了の合図
              if (data === "[DONE]") break;
              try {
                // JSONとしてパースを試みる
                const parsed = JSON.parse(data);
                if (parsed.token) {
                  // 【setMessages の関数型更新で最後のメッセージを更新】
                  // AIの回答メッセージ（配列の最後の要素）に新しいトークンを追記する
                  setMessages((prev) => {
                    const updated = [...prev];  // 配列のコピーを作成
                    const last = updated[updated.length - 1];  // 最後のメッセージ
                    if (last.role === "assistant") {
                      last.content += parsed.token;  // トークンを追記
                    }
                    return updated;
                  });
                }
              } catch {
                // JSONパースに失敗した場合は、生のテキストとして追記する
                // Not JSON, append as raw token
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last.role === "assistant") {
                    last.content += data;
                  }
                  return updated;
                });
              }
            }
          }
        }
      }
    } catch {
      // -------------------------------------------------------------------
      // フォールバック処理: ストリーミングが失敗した場合の代替処理
      // -------------------------------------------------------------------
      //
      // 【フォールバックとは？】
      // メインの方法（ストリーミング）が失敗した場合に、
      // 別の方法（通常のAPI呼び出し）で同じ結果を得ようとすること。
      // ユーザーにとっては、どちらの方法でも回答が得られるようにする。

      // Fallback to non-streaming query
      try {
        // ストリーミングではなく、通常のAPI呼び出しで回答を取得
        const res = await ragApi.query(input || query, 5);
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            last.content = res.data.answer;  // 回答全体を一括設定
          }
          return updated;
        });
      } catch {
        // 通常のAPIも失敗した場合のエラーメッセージ
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            last.content = "Sorry, I couldn't process your query.";
          }
          return updated;
        });
      }
    } finally {
      // 【finally ブロック】
      // try/catch の結果に関わらず、必ず実行される処理。
      // 成功しても失敗してもストリーミング状態をリセットする。
      setIsStreaming(false);
    }
  };

  // ===========================================================================
  // ファイルアップロード処理
  // ===========================================================================
  //
  // 【React.ChangeEvent<HTMLInputElement>】
  // <input>要素の値が変わった時に発生するイベントの型。
  // e.target.files: 選択されたファイルの配列（FileList型）。
  // ?.[0]: Optional Chainingで最初のファイルを安全に取得。

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMut.mutate(file);
    // ファイル入力をリセット（同じファイルを再選択できるように）
    e.target.value = "";
  };

  // ===========================================================================
  // JSX（レンダリング部分）
  // ===========================================================================
  //
  // 【ページのレイアウト構成】
  // ┌──────────────────────────────────┬──────────┐
  // │ RAG Chat                         │Documents │
  // │ ┌──────────────────────────────┐ │ Upload↑  │
  // │ │ AIの回答                     │ │ file.pdf │
  // │ │ ユーザーの質問                │ │ doc.txt  │
  // │ │ AIの回答                     │ │          │
  // │ └──────────────────────────────┘ │          │
  // │ [質問を入力...         ] [送信]  │          │
  // └──────────────────────────────────┴──────────┘
  //
  // 【flex h-full gap-6】
  // flex: 横並びレイアウト（チャット領域 + サイドバー）
  // h-full: 親要素の高さいっぱいに広がる
  // gap-6: 子要素間の隙間（1.5rem）

  return (
    <div className="flex h-full gap-6">
      {/* ================================================================= */}
      {/* チャット領域（左側・メイン）                                      */}
      {/* ================================================================= */}
      {/* Chat */}
      <div className="flex flex-1 flex-col">
        <h1 className="mb-4 text-2xl font-bold">RAG Chat</h1>

        {/* チャットカード全体: flex-col で縦方向にメッセージ表示→入力欄の順 */}
        <Card className="flex flex-1 flex-col overflow-hidden">
          {/* メッセージ表示エリア */}
          {/* overflow-auto: 内容がはみ出したらスクロールバーを表示 */}
          {/* Messages */}
          <CardContent className="flex-1 space-y-4 overflow-auto p-4">
            {/* メッセージが0件の場合の案内テキスト */}
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                <p>Ask questions about your uploaded documents.</p>
              </div>
            )}

            {/* 【messages.map() でメッセージ一覧を表示】 */}
            {/* (msg, i): msg = 各メッセージ、i = インデックス（0から始まる番号） */}
            {messages.map((msg, i) => (
              // ユーザーメッセージは右寄せ（justify-end）
              <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                {/* AIの回答の場合: 左側にBotアイコンを表示 */}
                {/* 【条件付きレンダリング: && 演算子】 */}
                {/* 左側が true の場合のみ、右側の要素をレンダリングする */}
                {msg.role === "assistant" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                )}

                {/* メッセージ本文のバブル */}
                {/* テンプレートリテラルで条件に応じたクラス名を切り替え */}
                {/* ユーザー: bg-primary (主要色の背景) */}
                {/* AI: bg-muted (控えめな背景色) */}
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  {/* whitespace-pre-wrap: 改行やスペースをそのまま表示する */}
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {/* AIが回答生成中（ストリーミング中）で内容がまだ空の場合、スピナーを表示 */}
                  {/* animate-spin: CSSアニメーションでアイコンを回転させる */}
                  {msg.role === "assistant" && msg.content === "" && isStreaming && (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  )}
                </div>

                {/* ユーザーメッセージの場合: 右側にUserアイコンを表示 */}
                {msg.role === "user" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <UserIcon className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {/* 【自動スクロール用の空div】 */}
            {/* ref={chatEndRef}: このdivへの参照を保持。useEffectでここにスクロールする */}
            <div ref={chatEndRef} />
          </CardContent>

          {/* ─────────────────────────────────────────────────────────── */}
          {/* メッセージ入力エリア                                        */}
          {/* ─────────────────────────────────────────────────────────── */}
          {/* Input */}
          <div className="border-t p-4">
            {/* 【form の onSubmit】 */}
            {/* フォーム送信時（Enterキー押下時）に handleSend を呼ぶ */}
            {/* e.preventDefault(): ブラウザのデフォルト動作（ページリロード）を防ぐ */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex gap-2"
            >
              {/* テキスト入力フィールド */}
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your documents..."
                disabled={isStreaming}
                className="flex-1"
              />
              {/* 送信ボタン */}
              {/* disabled: ストリーミング中または入力が空の場合は無効化 */}
              {/* !input.trim(): 空白のみの入力もブロックする */}
              <Button type="submit" disabled={isStreaming || !input.trim()} size="icon">
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </Card>
      </div>

      {/* ================================================================= */}
      {/* ドキュメントサイドバー（右側）                                    */}
      {/* ================================================================= */}
      {/* w-72: 幅288px固定 */}
      {/* shrink-0: フレックスボックスで縮小させない */}
      {/* Documents sidebar */}
      <div className="w-72 shrink-0">
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-base">
              <span>Documents</span>
              {/* ファイルアップロードボタン */}
              {/* 【隠しinput + label のパターン】 */}
              {/* <input type="file">は見た目が制御しにくいため、 */}
              {/* className="hidden"で非表示にし、<label>をクリックトリガーにする。 */}
              {/* labelをクリックすると、紐づいたinputのファイル選択ダイアログが開く。 */}
              <label className="cursor-pointer">
                <input type="file" className="hidden" accept=".pdf,.txt,.md" onChange={handleFileUpload} />
                <div className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent">
                  <Upload className="h-4 w-4" />
                </div>
              </label>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {/* アップロード処理中のローディング表示 */}
            {uploadMut.isPending && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                Processing...
              </div>
            )}

            {/* ドキュメント一覧 */}
            {documents.length === 0 ? (
              <p className="text-xs text-muted-foreground">Upload PDF, TXT, or MD files.</p>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between rounded-md border p-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {/* shrink-0: アイコンがテキストに押されて縮小しないようにする */}
                    <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0">
                      {/* truncate: 長いファイル名を「...」で省略 */}
                      <p className="truncate text-xs font-medium">{doc.title}</p>
                      {/* chunk_count: ドキュメントがいくつのチャンク（断片）に分割されたか */}
                      {/* RAGではドキュメントを小さなチャンクに分割して検索・参照する */}
                      <p className="text-[10px] text-muted-foreground">{doc.chunk_count ?? 0} chunks</p>
                    </div>
                  </div>
                  {/* 削除ボタン */}
                  <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => deleteMut.mutate(doc.id)}>
                    <Trash2 className="h-3 w-3 text-destructive" />
                  </Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
