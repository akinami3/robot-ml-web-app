"""FastAPI dependencies for dependency injection."""

# =============================================================================
# 依存性注入（Dependency Injection = DI）- FastAPIの心臓部
# =============================================================================
#
# 【依存性注入（DI）とは？】
# 「依存性注入」とは、あるクラスや関数が必要とする「部品（依存物）」を、
# 外部から「注入（渡す）」するデザインパターンです。
#
# 身近な例で説明すると：
#   ❌ DIなし: レストランのシェフが自分で食材を買いに行く
#   ✅ DIあり: 食材は配達業者が届けてくれる（シェフは料理に集中できる）
#
# プログラミングでは：
#   ❌ DIなし: 関数内でデータベース接続を直接作成する
#   ✅ DIあり: データベース接続は外部から渡してもらう
#
# 【DIのメリット】
#   1. テスト容易性 : テスト時にモック（偽物）の部品を注入できる
#      例: 本物のDBの代わりにメモリ上の偽DBを使ってテスト
#   2. 疎結合     : 部品の実装を簡単に差し替えられる
#      例: PostgreSQL → MySQL への変更が容易
#   3. 再利用性   : 同じ部品を複数の場所で共有できる
#   4. 可読性     : 各関数が何に依存しているか明確にわかる
#
# 【FastAPIのDIチェーン（連鎖）】
# このファイルでは、以下の順番でDIの連鎖が構成されています：
#
#   データベースセッション（Session）
#     ↓ 注入
#   リポジトリ（Repository）- データベース操作を担当
#     ↓ 注入
#   サービス（Service）- ビジネスロジックを担当
#     ↓ 注入
#   認証・認可（Auth）- ユーザー確認・権限チェック
#     ↓ 注入
#   エンドポイント関数 - 最終的なAPI処理
#
# 各レイヤーは自分が必要な部品だけを受け取り、
# 自分の仕事に集中します。
# =============================================================================

from __future__ import annotations

# ---------------------------------------------------------------------------
# 標準ライブラリとサードパーティのインポート
#
# - Annotated : Python 3.9+の型ヒント機能。型に追加情報（メタデータ）を付与できる
#               FastAPIではDepends()と組み合わせてDIを宣言するのに使います
# - UUID      : ユーザーIDなどの一意識別子
# ---------------------------------------------------------------------------
from typing import Annotated
from uuid import UUID

# ---------------------------------------------------------------------------
# FastAPIフレームワークからのインポート
#
# - Depends   : DIの核心。「この関数/クラスに依存しています」と宣言する
# - HTTPException : HTTPエラーレスポンスを返すための例外クラス
# - Request   : HTTPリクエストオブジェクト
# - status    : HTTPステータスコード定数（401, 403など）
# ---------------------------------------------------------------------------
from fastapi import Depends, HTTPException, Request, status

# ---------------------------------------------------------------------------
# HTTPBearer : Bearer認証スキームを処理するセキュリティクラス
# リクエストヘッダーの「Authorization: Bearer <token>」からトークンを抽出する
# ---------------------------------------------------------------------------
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# ---------------------------------------------------------------------------
# SQLAlchemy（データベースORM）の非同期セッション
# AsyncSession : 非同期（async/await）でデータベースを操作するためのセッション
# ---------------------------------------------------------------------------
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# 内部モジュールのインポート
#
# 「...config」の「...」は3階層上のディレクトリを意味する相対インポートです。
# 現在地: backend/app/api/v1/dependencies.py
#   .    → backend/app/api/v1/
#   ..   → backend/app/api/
#   ...  → backend/app/
#
# 以下の順番で依存関係が構成されています：
#   config（設定）→ security（セキュリティ）→ entities（エンティティ）
#   → repositories（リポジトリ）→ services（サービス）
#   → infrastructure（インフラ実装）
# ---------------------------------------------------------------------------
from ...config import Settings, get_settings
from ...core.security import decode_token
from ...domain.entities.user import User, UserRole
from ...domain.repositories.audit_repository import AuditRepository
from ...domain.repositories.dataset_repository import DatasetRepository
from ...domain.repositories.rag_repository import RAGRepository
from ...domain.repositories.recording_repository import RecordingRepository
from ...domain.repositories.robot_repository import RobotRepository
from ...domain.repositories.sensor_data_repository import SensorDataRepository
from ...domain.repositories.user_repository import UserRepository
from ...domain.services.audit_service import AuditService
from ...domain.services.dataset_service import DatasetService
from ...domain.services.rag_service import RAGService
from ...domain.services.recording_service import RecordingService
from ...infrastructure.database.connection import get_session
from ...infrastructure.database.repositories.audit_repo import SQLAlchemyAuditRepository
from ...infrastructure.database.repositories.dataset_repo import SQLAlchemyDatasetRepository
from ...infrastructure.database.repositories.rag_repo import SQLAlchemyRAGRepository
from ...infrastructure.database.repositories.recording_repo import SQLAlchemyRecordingRepository
from ...infrastructure.database.repositories.robot_repo import SQLAlchemyRobotRepository
from ...infrastructure.database.repositories.sensor_data_repo import SQLAlchemySensorDataRepository
from ...infrastructure.database.repositories.user_repo import SQLAlchemyUserRepository

# ---------------------------------------------------------------------------
# HTTPBearerセキュリティスキームの作成
#
# HTTPBearer(auto_error=False) の意味：
# - HTTPBearer() : Authorizationヘッダーから「Bearer <token>」を自動解析する
# - auto_error=False : トークンがない場合でもエラーを自動発生させない
#   → 代わりに None を返す（エラー処理は自分でカスタマイズできる）
#   → auto_error=True（デフォルト）だと、トークンがない場合に
#     FastAPIが自動で403エラーを返してしまう
# ---------------------------------------------------------------------------
security = HTTPBearer(auto_error=False)


# ─── Database Session ────────────────────────────────────────────────────────
# データベースセッション管理
#
# 【DIチェーンの第1層】セッション
# データベースとの「会話の窓口」を提供します。
# 全てのデータベース操作は、このセッションを通じて行われます。


# ---------------------------------------------------------------------------
# get_db() - データベースセッションを提供するジェネレーター関数
#
# 【async for ... yield パターン】
# この関数は「非同期ジェネレーター」と呼ばれる特殊な関数です。
# 「yield」でセッションを一時的に「貸し出し」、
# 使い終わったら自動的にセッションをクリーンアップ（閉じる）します。
#
# 流れ：
#   1. get_session()からセッションを取得
#   2. yieldでセッションを呼び出し元に渡す（一時停止）
#   3. 呼び出し元の処理が完了したら、自動的にセッションを片付ける
#
# これにより、セッションの開放忘れ（リソースリーク）を防ぎます。
# ---------------------------------------------------------------------------
async def get_db() -> AsyncSession:
    async for session in get_session():
        yield session


# ---------------------------------------------------------------------------
# DbSession型エイリアス
#
# 【Annotated[型, Depends(依存関数)] パターン】
# これはFastAPIのDIの「宣言的記法」です。
#
# Annotated[AsyncSession, Depends(get_db)] は以下を意味します：
# 「AsyncSession型の値を、get_db関数から取得して注入してください」
#
# こう書くことで、エンドポイント関数の引数に「DbSession」と書くだけで、
# 自動的にデータベースセッションが注入されます。
#
# 使用例：
#   async def my_endpoint(session: DbSession):  ← 自動注入！
#       users = await session.execute(...)
# ---------------------------------------------------------------------------
DbSession = Annotated[AsyncSession, Depends(get_db)]


# ─── Repositories ────────────────────────────────────────────────────────────
# リポジトリの依存性定義
#
# 【DIチェーンの第2層】リポジトリ
# リポジトリは「データベース操作を隠蔽する層」です。
# エンドポイントやサービスは、SQLを直接書く代わりに、
# リポジトリのメソッド（find_by_id, saveなど）を使います。
#
# 【抽象と具象の分離】
# - UserRepository（抽象）: 「こんな操作ができるはず」というインターフェース
# - SQLAlchemyUserRepository（具象）: 「PostgreSQLでこう実装する」という実装
#
# なぜ分けるのか？
#   → テスト時にはインメモリ実装に差し替えられる
#   → データベースをPostgreSQLからMongoDBに変更しても、上位層に影響しない


# ---------------------------------------------------------------------------
# 各リポジトリのファクトリ関数
# 「ファクトリ関数」= オブジェクトを生成して返す関数
#
# 引数の「session: DbSession」に注目してください。
# この引数をFastAPIのDIシステムが見て、
# 「DbSessionが必要だな → get_db()を先に呼ぼう」と判断します。
#
# つまり、DIの連鎖が自動的に発生します：
#   get_db() → セッション取得
#     ↓ 注入
#   get_user_repo(session) → リポジトリ生成
#     ↓ 注入
#   エンドポイント関数
# ---------------------------------------------------------------------------
def get_user_repo(session: DbSession) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_robot_repo(session: DbSession) -> RobotRepository:
    return SQLAlchemyRobotRepository(session)


def get_sensor_data_repo(session: DbSession) -> SensorDataRepository:
    return SQLAlchemySensorDataRepository(session)


def get_dataset_repo(session: DbSession) -> DatasetRepository:
    return SQLAlchemyDatasetRepository(session)


def get_rag_repo(session: DbSession) -> RAGRepository:
    return SQLAlchemyRAGRepository(session)


def get_audit_repo(session: DbSession) -> AuditRepository:
    return SQLAlchemyAuditRepository(session)


def get_recording_repo(session: DbSession) -> RecordingRepository:
    return SQLAlchemyRecordingRepository(session)


# ---------------------------------------------------------------------------
# リポジトリの型エイリアス
#
# 上で定義したファクトリ関数をAnnotated + Dependsで型エイリアスにします。
# これにより、エンドポイント関数で簡潔にリポジトリを受け取れます。
#
# 使用例：
#   async def list_users(repo: UserRepo):  ← この1行でDI完了！
#       users = await repo.find_all()
#
# 実際の動作：
#   1. FastAPIが「UserRepo」の型を解析
#   2. Depends(get_user_repo)を発見
#   3. get_user_repoの引数「session: DbSession」を解析
#   4. Depends(get_db)を発見
#   5. get_db()を実行してセッションを取得
#   6. セッションをget_user_repoに渡してリポジトリを生成
#   7. リポジトリをエンドポイント関数に注入
# ---------------------------------------------------------------------------
UserRepo = Annotated[UserRepository, Depends(get_user_repo)]
RobotRepo = Annotated[RobotRepository, Depends(get_robot_repo)]
SensorDataRepo = Annotated[SensorDataRepository, Depends(get_sensor_data_repo)]
DatasetRepo = Annotated[DatasetRepository, Depends(get_dataset_repo)]
RagRepo = Annotated[RAGRepository, Depends(get_rag_repo)]
AuditRepo = Annotated[AuditRepository, Depends(get_audit_repo)]
RecordingRepo = Annotated[RecordingRepository, Depends(get_recording_repo)]


# ─── Services ────────────────────────────────────────────────────────────────
# サービス層の依存性定義
#
# 【DIチェーンの第3層】サービス
# サービスはビジネスロジック（業務ルール）を担当する層です。
# 例: 「データセットを作成する際は、指定されたロボットが存在するか確認する」
#
# サービスは1つ以上のリポジトリに依存します。
# 例: DatasetServiceはDatasetRepoとSensorDataRepoの両方が必要


# ---------------------------------------------------------------------------
# 各サービスのファクトリ関数
#
# 引数にリポジトリの型エイリアス（AuditRepo等）を使っているので、
# FastAPIのDIが自動的にリポジトリを先に生成して渡してくれます。
#
# DIチェーンの例（DatasetService）：
#   get_db() → セッション
#     ↓
#   get_dataset_repo(session) → DatasetRepository
#   get_sensor_data_repo(session) → SensorDataRepository
#     ↓
#   get_dataset_service(dataset_repo, sensor_repo) → DatasetService
#     ↓
#   エンドポイント関数
# ---------------------------------------------------------------------------
def get_audit_service(repo: AuditRepo) -> AuditService:
    return AuditService(repo)


def get_dataset_service(
    dataset_repo: DatasetRepo,
    sensor_repo: SensorDataRepo,
) -> DatasetService:
    return DatasetService(dataset_repo, sensor_repo)


def get_recording_service(
    recording_repo: RecordingRepo,
    sensor_repo: SensorDataRepo,
) -> RecordingService:
    return RecordingService(recording_repo, sensor_repo)


# ---------------------------------------------------------------------------
# サービスの型エイリアス
# リポジトリと同じパターンで、サービスも型エイリアスを定義します。
# ---------------------------------------------------------------------------
AuditSvc = Annotated[AuditService, Depends(get_audit_service)]
DatasetSvc = Annotated[DatasetService, Depends(get_dataset_service)]
RecordingSvc = Annotated[RecordingService, Depends(get_recording_service)]


# ─── Authentication ──────────────────────────────────────────────────────────
# 認証（Authentication）の依存性定義
#
# 【認証（Authentication）とは？】
# 「あなたは誰ですか？」を確認するプロセスです。
# このアプリではJWT（JSON Web Token）ベースの認証を使っています。
#
# 【認証フロー（流れ）】
#   1. クライアントがリクエストヘッダーにトークンを付けて送信
#      → Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
#   2. HTTPBearerがヘッダーからトークンを抽出
#   3. decode_token()でトークンを検証・解読
#   4. トークン内のユーザーID（sub）を取得
#   5. データベースからユーザー情報を取得
#   6. ユーザーが有効（is_active）か確認
#   7. 認証成功！ → Userオブジェクトを返す


# ---------------------------------------------------------------------------
# get_current_user() - 現在のログインユーザーを取得する認証関数
#
# 【引数の解説】
# - credentials : HTTPBearerが抽出したトークン情報（なければNone）
# - user_repo   : ユーザーリポジトリ（DBからユーザーを検索する）
# - settings    : アプリ設定（JWT公開鍵が含まれている）
#
# 各引数にAnnotated + Dependsが使われているので、
# FastAPIが自動的に値を解決して注入してくれます。
#
# 【HTTPExceptionによるエラーレスポンス】
# 認証に失敗すると、HTTPException（HTTP例外）を発生させます。
# - status_code=401 : 「認証されていない」（Unauthorized）
# - headers={"WWW-Authenticate": "Bearer"} :
#   → クライアントに「Bearerトークンが必要です」と通知するHTTPヘッダー
#   → これはHTTPの標準仕様（RFC 7235）に準拠しています
# ---------------------------------------------------------------------------
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    user_repo: UserRepo,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    # トークンが提供されていない場合（未ログイン状態）
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # トークンをデコード（解読）して検証する
    # JWT公開鍵を使って、トークンが正規のサーバーが発行したものか確認する
    # 改ざんされたトークンや期限切れのトークンはNoneが返る
    payload = decode_token(credentials.credentials, settings.jwt_public_key)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # トークンの「sub」（subject = 主体）クレームからユーザーIDを取得
    # JWTの標準クレームで、「このトークンは誰のものか」を示す
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # データベースからユーザーを取得し、存在確認とアクティブ状態を検証
    user = await user_repo.get_by_id(UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # 認証成功！ユーザーオブジェクトを返す
    return user


# ---------------------------------------------------------------------------
# CurrentUser型エイリアス
#
# エンドポイント関数で「user: CurrentUser」と書くだけで、
# 自動的にトークン検証 → ユーザー取得が行われます。
#
# 使用例：
#   @router.get("/me")
#   async def get_me(user: CurrentUser):  ← 認証済みユーザーが自動注入！
#       return {"username": user.username}
#
# 認証に失敗すると、エンドポイント関数は実行されず、
# 401エラーがクライアントに返されます。
# ---------------------------------------------------------------------------
CurrentUser = Annotated[User, Depends(get_current_user)]


# ─── Authorization ───────────────────────────────────────────────────────────
# 認可（Authorization）の依存性定義
#
# 【認証（Authentication）と認可（Authorization）の違い】
# - 認証（AuthN）: 「あなたは誰？」 → ログインの確認
# - 認可（AuthZ）: 「あなたに権限はある？」 → 操作の許可確認
#
# 例えば：
#   - 認証: 社員証を見せてビルに入る（あなたが社員であることを確認）
#   - 認可: サーバールームに入れるかチェック（管理者だけ入室可能）
#
# 【ロール（Role）ベースアクセス制御（RBAC）】
# ユーザーに「役割（ロール）」を割り当て、
# ロールに応じてアクセスできる機能を制限する方式です。
#
#   - ADMIN     : 全機能にアクセス可能（管理者）
#   - OPERATOR  : ロボット操作・データ管理が可能（操作者）
#   - VIEWER    : 閲覧のみ可能（閲覧者）


# ---------------------------------------------------------------------------
# require_role() - ロールベースの認可チェックを行うDI関数
#
# 【高階関数（Higher-Order Function）パターン】
# この関数は「関数を返す関数」です。
# require_role(UserRole.ADMIN) を呼ぶと、
# 「ADMINロールかチェックする関数」が返されます。
#
# このパターンにより、必要なロールを柔軟に指定できます：
#   require_role(UserRole.ADMIN)                    → 管理者のみ
#   require_role(UserRole.ADMIN, UserRole.OPERATOR) → 管理者または操作者
#
# 【内部の仕組み】
#   1. require_role()が呼ばれると、checker関数が生成される
#   2. checker関数はCurrentUserに依存している
#   3. FastAPIがcheckerを実行する際、まずget_current_userが実行される
#   4. 認証が成功したら、checkerがユーザーのロールを確認
#   5. 必要なロールを持っていなければ403 Forbiddenエラー
#
# 使用例（エンドポイントでの使い方）：
#   @router.delete("/users/{user_id}")
#   async def delete_user(user: AdminUser):  ← ADMINのみ実行可能！
#       ...
# ---------------------------------------------------------------------------
def require_role(*roles: UserRole):
    """Dependency that checks the user has one of the required roles."""

    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(r.value for r in roles)}",
            )
        return user

    return checker


# ---------------------------------------------------------------------------
# ロール別ユーザー型エイリアス
#
# - AdminUser    : 管理者（ADMIN）ロールが必須
# - OperatorUser : 管理者（ADMIN）または操作者（OPERATOR）ロールが必須
#
# エンドポイントの引数の型をこれにするだけで、
# 認証＋認可が自動的に行われます。
#
# DIチェーンの完全な流れ（AdminUserの場合）：
#   1. get_db()            → データベースセッション取得
#   2. get_user_repo()     → ユーザーリポジトリ生成
#   3. get_settings()      → アプリ設定取得
#   4. security()          → Authorizationヘッダーからトークン抽出
#   5. get_current_user()  → トークン検証 → ユーザー取得（認証）
#   6. require_role()      → ロールチェック（認可）
#   7. エンドポイント関数実行
#
# この全ての処理が「user: AdminUser」の1行で自動実行されます！
# これがFastAPIのDIの強力さです。
# ---------------------------------------------------------------------------
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
OperatorUser = Annotated[
    User, Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR))
]
