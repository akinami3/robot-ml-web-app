"""User management endpoints (admin only)."""
# ユーザー管理エンドポイント（管理者専用）
# このファイルでは、ユーザーの一覧取得・作成・更新・削除（CRUD）を行うAPIを定義します
# すべてのエンドポイントは管理者（Admin）のみがアクセスできます

from __future__ import annotations

from uuid import UUID

# FastAPIのルーター機能とエラーハンドリング用のクラスをインポート
from fastapi import APIRouter, HTTPException, status

# パスワードをハッシュ化する関数（平文のまま保存しないためのセキュリティ対策）
from ....core.security import hash_password
# 監査ログに記録するアクションの種類（作成・更新・削除など）
from ....domain.entities.audit_log import AuditAction
# ユーザーエンティティとロール（権限レベル）の定義
from ....domain.entities.user import User, UserRole
# 依存性注入で使う型エイリアス
# AdminUser: 管理者権限を持つユーザーのみ許可する依存性
# AuditSvc: 監査ログサービス（操作履歴を記録する）
# UserRepo: ユーザーリポジトリ（データベースとのやり取りを担当）
from ..dependencies import AdminUser, AuditSvc, UserRepo
# リクエスト・レスポンスのデータ構造（バリデーション付き）
from ..schemas import UserCreate, UserResponse, UserUpdate

# "/users" というURLプレフィックスでルーターを作成
# tags=["users"] はAPIドキュメント（Swagger UI）でのグループ分けに使われます
router = APIRouter(prefix="/users", tags=["users"])


# ── ユーザー一覧取得 ──────────────────────────────────────────
# GET /users → 全ユーザーの一覧を返す（管理者のみ）
# response_model=list[UserResponse] で、レスポンスの型を明示しています
@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user: AdminUser,       # この引数があることで、管理者以外はアクセス拒否されます
    user_repo: UserRepo,           # データベースからユーザーを取得するリポジトリ
    offset: int = 0,               # ページネーション: 何件目から取得するか（デフォルト: 0）
    limit: int = 100,              # ページネーション: 最大何件取得するか（デフォルト: 100）
):
    # データベースからユーザー一覧を取得
    users = await user_repo.get_all(offset=offset, limit=limit)
    # 各ユーザーをレスポンス用の形式（UserResponse）に変換して返す
    # リスト内包表記を使って、全ユーザーを一度に変換しています
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role.value,         # Enum型を文字列に変換（例: UserRole.ADMIN → "admin"）
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


# ── ユーザー新規作成 ──────────────────────────────────────────
# POST /users → 新しいユーザーを作成する（管理者のみ）
# status_code=201 は「リソースが正常に作成された」ことを示すHTTPステータスコード
@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,              # リクエストボディ（ユーザー名、メール、パスワード、ロールなど）
    current_user: AdminUser,       # 管理者のみアクセス可能
    user_repo: UserRepo,           # ユーザーリポジトリ
    audit_svc: AuditSvc,           # 監査ログサービス（誰が何をしたか記録する）
):
    # ── ユーザー名の重複チェック ──
    # 同じユーザー名が既に存在する場合は409 Conflictエラーを返す
    existing = await user_repo.get_by_username(body.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    # ── ロール（権限）のバリデーション ──
    # 無効なロールが指定された場合、エラーにせずデフォルトでVIEWER（閲覧者）にする
    # これにより、不正な値でもアプリがクラッシュしません
    try:
        role = UserRole(body.role)
    except ValueError:
        role = UserRole.VIEWER

    # ── ユーザーエンティティの作成 ──
    # パスワードはhash_password()でハッシュ化してから保存します
    # ハッシュ化 = 元のパスワードに戻せない形式に変換すること（セキュリティの基本）
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=role,
    )
    # データベースに保存
    created = await user_repo.create(user)

    # ── 監査ログへの記録 ──
    # 「誰が」「何を」「どのリソースに対して」行ったかを記録します
    # これはセキュリティ上とても重要で、不正操作の追跡に使われます
    await audit_svc.log_action(
        user_id=current_user.id,              # 操作した管理者のID
        action=AuditAction.USER_CREATE,       # アクション: ユーザー作成
        resource_type="user",                 # リソースの種類
        resource_id=str(created.id),          # 作成されたユーザーのID
    )

    # 作成されたユーザー情報をレスポンスとして返す
    return UserResponse(
        id=created.id,
        username=created.username,
        email=created.email,
        role=created.role.value,
        is_active=created.is_active,
        created_at=created.created_at,
    )


# ── ユーザー部分更新（PATCH） ──────────────────────────────────
# PATCH /users/{user_id} → ユーザー情報を部分的に更新する（管理者のみ）
# PATCHはPUTと違い、変更したいフィールドだけ送ればOKです（部分更新）
# 例: メールだけ変更したい場合 → {"email": "new@example.com"} だけ送る
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,                 # URLパスから取得するユーザーID
    body: UserUpdate,              # 更新内容（変更したいフィールドのみ含む）
    current_user: AdminUser,       # 管理者のみアクセス可能
    user_repo: UserRepo,
    audit_svc: AuditSvc,
):
    # 更新対象のユーザーをデータベースから取得
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # ── 部分更新の処理 ──
    # 各フィールドが None でない場合のみ更新する（PATCHパターン）
    # こうすることで、送られてこなかったフィールドは元の値のまま保持されます
    if body.email is not None:
        user.email = body.email
    if body.role is not None:
        # ロールの値が有効かチェック（無効なら400 Bad Requestエラー）
        try:
            user.role = UserRole(body.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
    if body.is_active is not None:
        user.is_active = body.is_active

    # 更新内容をデータベースに保存
    updated = await user_repo.update(user)

    # 監査ログに更新操作を記録
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.USER_UPDATE,
        resource_type="user",
        resource_id=str(user_id),
    )

    return UserResponse(
        id=updated.id,
        username=updated.username,
        email=updated.email,
        role=updated.role.value,
        is_active=updated.is_active,
        created_at=updated.created_at,
    )


# ── ユーザー削除 ──────────────────────────────────────────────
# DELETE /users/{user_id} → ユーザーを削除する（管理者のみ）
# status_code=204 は「成功したがレスポンスボディなし」を意味します
@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: AdminUser,
    user_repo: UserRepo,
    audit_svc: AuditSvc,
):
    # ── 自分自身の削除を防止する安全チェック ──
    # 管理者が誤って自分を削除してしまうと、システムにログインできなくなる恐れがあります
    # そのため、自分自身の削除は明示的にブロックしています
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Cannot delete yourself"
        )

    # データベースからユーザーを削除（削除できたかどうかをboolで返す）
    deleted = await user_repo.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    # 監査ログに削除操作を記録
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.USER_DELETE,
        resource_type="user",
        resource_id=str(user_id),
    )
