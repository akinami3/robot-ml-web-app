# Step 12: RAG システム 🤖

> **ブランチ**: `step/12-rag-system`
> **前のステップ**: `step/11-data-recording`
> **次のステップ**: `step/13-production`

---

## このステップで学ぶこと

1. **RAG パイプライン** — Retrieval-Augmented Generation（検索拡張生成）
2. **ベクトル埋め込み** — テキスト → 768 次元の数値ベクトル変換
3. **コサイン類似度** — ベクトル間の角度で意味的類似性を測定
4. **SSE ストリーミング** — Server-Sent Events によるリアルタイム回答配信
5. **Ollama** — ローカル LLM サーバー（プライバシー保護）

---

## 概要

RAG（Retrieval-Augmented Generation: 検索拡張生成）パイプラインを構築するステップ。
ドキュメントをアップロードしてチャンク分割・ベクトル化（Embedding）し、
質問に対して関連文書をコサイン類似度で検索、その文脈を使って LLM が回答を生成する。
回答は **SSE（Server-Sent Events）** でリアルタイムにストリーミング配信される。

---

## RAG パイプライン

```
1. ドキュメント取り込み（Ingest）
   PDF/Text ──► チャンク分割 ──► Embedding ──► PostgreSQL (pgvector)
                (段落認識)      (nomic-embed)   (ベクトル保存)

2. 質問応答（Query）
   質問テキスト ──► Embedding ──► コサイン類似度検索 ──► 上位 K 件取得
                                                         │
   回答 ◄──── LLM 生成 ◄──── プロンプト構築 ◄────────────┘
   (SSE)      (Ollama)        (質問 + 関連文書)
```

---

## 学習ポイント

### チャンク分割（Text Splitting）
- ドキュメントを段落単位で分割
- オーバーラップ（重複）を持たせて文脈の切れ目を防止
- チャンクサイズと検索精度のトレードオフ

### ベクトル埋め込み（Embedding）
```
"ロボットのセンサー" → [0.12, -0.45, 0.78, ..., 0.33]  (768次元)
"robot sensors"      → [0.11, -0.43, 0.76, ..., 0.35]  (意味的に近い！)
"今日の天気"          → [0.89, 0.12, -0.54, ..., 0.01]  (意味的に遠い)
```

### コサイン類似度検索（pgvector）
```sql
SELECT content, 1 - (embedding <=> query_vector) AS similarity
FROM document_chunks
ORDER BY embedding <=> query_vector
LIMIT 5;
```

### SSE ストリーミング
- サーバーからクライアントへの一方向ストリーミング
- `text/event-stream` Content-Type
- Fetch API の `ReadableStream` でトークン単位に受信
- LLM の回答が 1 トークンずつリアルタイムに表示

### Annotated DI パターン（Python 3.9+）
```python
# 従来
async def upload(repo: RAGRepository = Depends(get_rag_repo)):
# Annotated（Step 12）
RagRepo = Annotated[RAGRepository, Depends(get_rag_repo)]
async def upload(repo: RagRepo):
```

---

## ファイル構成

```
backend/
  app/
    config.py                              ← Ollama URL, モデル名, チャンク設定追加
    main.py                                ← v0.5.0
    api/v1/
      schemas.py                           ← RAGDocument, RAGQuery スキーマ追加
      dependencies.py                      ← Annotated エイリアス追加
      rag.py                               ← 🆕 ドキュメント CRUD + クエリ + SSE
    domain/
      entities/
        rag_document.py                    ← 🆕 RAGDocument, DocumentChunk
      repositories/
        rag_repository.py                  ← 🆕 抽象 RAGRepository
      services/
        rag_service.py                     ← TextSplitter, ingest/query/stream
    infrastructure/
      llm/
        ollama_client.py                   ← 🆕 Ollama HTTP クライアント
        embedding.py                       ← 🆕 nomic-embed-text ベクトル化
      database/
        models.py                          ← RAGDocumentModel, DocumentChunkModel 追加
        repositories/
          rag_repo.py                      ← 🆕 pgvector コサイン類似度検索
  pyproject.toml                           ← httpx, pypdf 依存追加

frontend/src/
  pages/
    RAGChatPage.tsx                        ← 🆕 チャット UI（SSE + ドキュメント管理）
  services/
    api.ts                                 ← ragApi 追加
  types/
    index.ts                               ← RAGDocument, RAGSource, RAGQueryResult 型追加
  App.tsx                                  ← /rag ルート追加
  components/layout/Sidebar.tsx            ← RAG Chat ナビ追加

docker-compose.yml                         ← 6 サービス構成（+Ollama）
```

---

## 起動方法

```bash
docker compose up --build
```

| サービス | ポート | 説明 |
|----------|--------|------|
| frontend | 3000 | Vite 開発サーバー |
| backend | 8000 | FastAPI + RAG API |
| gateway | 8080 | WebSocket |
| postgres | 5432 | PostgreSQL + pgvector |
| redis | 6379 | Redis Streams |
| ollama | 11434 | ローカル LLM サーバー |

### 初回セットアップ（LLM モデルのダウンロード）

```bash
# Ollama コンテナにモデルをダウンロード
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama pull nomic-embed-text
```

### 試してみる

1. ログイン後、サイドバー「RAG Chat」を開く
2. サイドバーの「ドキュメント管理」でテキストや PDF をアップロード
3. チャットで質問 → アップロードしたドキュメントに基づいた回答がストリーミング表示
4. 回答には参照元のドキュメントチャンクが表示される

---

## Step 11 からの主な変更

| カテゴリ | 変更内容 |
|----------|----------|
| RAG | ドキュメント取り込み → チャンク → Embedding → 類似度検索 |
| LLM | Ollama ローカル LLM サーバー連携 |
| ストリーミング | SSE でリアルタイム回答配信 |
| DB | pgvector によるベクトル検索 |
| フロント | RAGChatPage（チャット UI + ドキュメント管理） |
| インフラ | Ollama サービス追加（6 サービス構成） |
| ファイル数 | 19 files changed, +2,352 / -84 |

---

## 🏋️ チャレンジ課題

1. **異なるモデルを試そう**: Ollama で `mistral` や `gemma` に切り替えて回答品質を比較
2. **チャンクサイズを変更**: 大きく/小さくして検索精度への影響を観察
3. **類似度スコア表示**: 検索結果の類似度スコアを UI に表示してみよう
4. **会話履歴**: 直前の質疑応答をコンテキストに含めて、文脈を理解した回答を実現

---

## 次のステップへ

Step 13（最終ステップ）では **本番品質** に仕上げます — Docker 最適化、CI/CD、ドキュメント:

```bash
git checkout step/13-production
```
