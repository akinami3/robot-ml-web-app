"""Audit log endpoints."""
# 監査ログ（Audit Log）エンドポイント
# 監査ログとは、「誰が・いつ・何をしたか」を記録したものです
# セキュリティの観点から非常に重要で、不正アクセスや操作ミスの調査に使われます
# 例: 「管理者Aが2024年1月1日にユーザーBを削除した」という記録

from __future__ import annotations

from fastapi import APIRouter

# AdminUser: 管理者のみアクセスを許可する依存性注入
# 監査ログは機密情報を含むため、一般ユーザーには見せてはいけません
# AuditRepo: 監査ログのデータベース操作を担当するリポジトリ
from ..dependencies import AdminUser, AuditRepo
# レスポンスのデータ構造（どの項目をクライアントに返すかを定義）
from ..schemas import AuditLogResponse

# "/audit" というURLプレフィックスでルーターを作成
router = APIRouter(prefix="/audit", tags=["audit"])


# ── 監査ログ一覧取得 ──────────────────────────────────────────
# GET /audit/logs → 監査ログの一覧を返す（管理者のみ）
# 監査ログを閲覧できるのは管理者だけです（セキュリティ上の制約）
@router.get("/logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    current_user: AdminUser,       # 管理者認証（AdminUser型で管理者以外は自動的に拒否）
    audit_repo: AuditRepo,        # 監査ログリポジトリ（データベースから取得）
    offset: int = 0,               # ページネーション: 開始位置（デフォルト: 0件目から）
    limit: int = 100,              # ページネーション: 取得件数（デフォルト: 最大100件）
    # ページネーションにより、大量のログを少しずつ取得できます
    # 例: offset=200, limit=100 → 201件目～300件目を取得
):
    # データベースから監査ログを取得
    logs = await audit_repo.get_all(offset=offset, limit=limit)
    # 各ログをレスポンス用の形式に変換して返す
    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            # hasattr()による安全チェック:
            # log.actionがEnum型（.valueプロパティを持つ）の場合は.valueで文字列に変換
            # 文字列がそのまま入っている場合はそのまま使う
            # これにより、データの形式が想定と異なっていてもエラーにならずに対応できます
            action=log.action.value if hasattr(log.action, "value") else log.action,
            resource_type=log.resource_type,   # 操作対象の種類（例: "user", "dataset"）
            resource_id=log.resource_id,       # 操作対象のID
            details=log.details,               # 操作の詳細情報（任意）
            ip_address=log.ip_address,         # 操作元のIPアドレス（不正アクセス調査に有用）
            timestamp=log.timestamp,           # 操作が行われた日時
        )
        for log in logs
    ]
