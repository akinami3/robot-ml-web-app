"""API v1 router - aggregates all endpoint routers."""

# =============================================================================
# APIルーター（API Router）- すべてのエンドポイントを集約するモジュール
# =============================================================================
#
# 【このファイルの役割】
# このファイルは、アプリケーション内の全APIエンドポイント（URL）を
# 1つのルーターにまとめる「集約ポイント」です。
# レストランに例えると、このファイルは「総合受付」のような存在です。
# お客さん（リクエスト）が来たら、適切な担当（エンドポイント）に案内します。
#
# 【REST APIのバージョニング（/api/v1）とは？】
# URLに「/api/v1」を含めることで、APIのバージョン管理ができます。
# 例えば、将来的にAPIの仕様を大きく変更したい場合、
# 「/api/v2」として新しいバージョンを作れます。
# これにより、古いバージョンを使っているクライアント（フロントエンドなど）が
# 壊れることなく、新旧のAPIを同時に運用できます。
#
#   /api/v1/robots  ← 現在のバージョン（このファイルで定義）
#   /api/v2/robots  ← 将来の新バージョン（別ファイルで定義可能）
#
# 【URLルーティングとは？】
# 「ルーティング」とは、URLのパス（例: /api/v1/robots）を見て、
# どの処理を実行するかを決定する仕組みです。
# 例えば：
#   GET  /api/v1/robots  → ロボット一覧を取得する処理
#   POST /api/v1/auth    → ログイン認証を行う処理
# =============================================================================

# ---------------------------------------------------------------------------
# FastAPIのAPIRouterクラスをインポートします。
# APIRouterは、関連するエンドポイントをグループ化するための仕組みです。
# FastAPIのメインアプリ（FastAPI()）に直接エンドポイントを書く代わりに、
# 機能ごとにルーターを分けて整理できます。
# これにより、コードが整理され、チーム開発がしやすくなります。
# ---------------------------------------------------------------------------
from fastapi import APIRouter

# ---------------------------------------------------------------------------
# 各エンドポイントモジュールからルーターをインポートします。
#
# 【相対インポート（ドット記法）について】
# 「.endpoints.auth」の「.」は「現在のパッケージ（ディレクトリ）」を意味します。
# つまり、同じ「v1」ディレクトリ内の「endpoints」フォルダにある
# 各モジュールからルーターを読み込んでいます。
#
# 【「as ○○_router」について】
# 各モジュールでは変数名が全て「router」なので、
# そのままインポートすると名前が衝突（重複）してしまいます。
# 「as auth_router」のように別名をつけることで区別しています。
#
# 【各エンドポイントの役割】
#   auth_router       : 認証（ログイン・トークン発行）
#   audit_router      : 監査ログ（誰がいつ何をしたか記録）
#   datasets_router   : データセット管理（ML学習用データ）
#   rag_router        : RAG（検索拡張生成 - AIがドキュメントを参照して回答）
#   recordings_router : センサーデータの記録管理
#   robots_router     : ロボット管理（登録・状態確認）
#   sensors_router    : センサーデータの取得・検索
#   users_router      : ユーザー管理（作成・更新・削除）
# ---------------------------------------------------------------------------
from .endpoints.auth import router as auth_router
from .endpoints.audit import router as audit_router
from .endpoints.datasets import router as datasets_router
from .endpoints.rag import router as rag_router
from .endpoints.recordings import router as recordings_router
from .endpoints.robots import router as robots_router
from .endpoints.sensors import router as sensors_router
from .endpoints.users import router as users_router

# ---------------------------------------------------------------------------
# メインのAPIルーターを作成します。
#
# 【APIRouter(prefix="/api/v1") の意味】
# - APIRouter() : 新しいルーターを作成するクラス
# - prefix="/api/v1" : このルーター配下の全エンドポイントに
#                      「/api/v1」というURLプレフィックス（接頭辞）を自動付与
#
# 例えば、robots_routerに「/robots」というパスがある場合、
# 実際のURLは「/api/v1/robots」になります。
# prefixを使うことで、各エンドポイントで毎回 "/api/v1" と書く必要がなくなります。
# ---------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1")

# ---------------------------------------------------------------------------
# include_router() で各エンドポイントルーターを統合します。
#
# 【include_routerパターンとは？】
# FastAPIでは、機能ごとにルーターを分けて開発し、
# 最後に1つの親ルーターに「include（含める）」するパターンが一般的です。
#
# このパターンのメリット：
#   1. コードの分離 : 各機能を別ファイルで開発できる
#   2. チーム開発 : 複数人が別々のエンドポイントを同時に開発できる
#   3. テスト容易性 : 個別のルーターを独立してテストできる
#   4. 再利用性 : ルーターを別のアプリでも使い回せる
#
# 【最終的なURLの構成】
#   /api/v1/auth/...        ← 認証関連
#   /api/v1/users/...       ← ユーザー管理
#   /api/v1/robots/...      ← ロボット管理
#   /api/v1/sensors/...     ← センサーデータ
#   /api/v1/datasets/...    ← データセット
#   /api/v1/recordings/...  ← 記録管理
#   /api/v1/rag/...         ← RAG（AI検索）
#   /api/v1/audit/...       ← 監査ログ
#
# ※ 各子ルーター（auth_routerなど）にもprefixやtagsが
#    設定されている場合があります（各endpointsファイルを参照）。
# ---------------------------------------------------------------------------
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(robots_router)
api_router.include_router(sensors_router)
api_router.include_router(datasets_router)
api_router.include_router(recordings_router)
api_router.include_router(rag_router)
api_router.include_router(audit_router)
