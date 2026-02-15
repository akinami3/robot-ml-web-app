# ============================================================
# 監査サービス（Audit Service）
# ============================================================
# 監査ログ（誰が・いつ・何をしたかの記録）に関する
# ビジネスロジックを担当するサービスクラスです。
#
# 【サービス層の役割】
# - リポジトリ（データ保存）を呼び出す
# - ロギング（構造化ログの出力）を行う
# - ビジネスルールを適用する
#
# 【なぜエンドポイントから直接リポジトリを呼ばないのか？】
# サービス層を挟むことで：
# 1. ビジネスロジックを一箇所にまとめられる
# 2. 複数のエンドポイントから同じロジックを再利用できる
# 3. テスト時にサービスだけを独立してテストできる
# ============================================================
"""Audit service - domain logic for audit logging."""

from __future__ import annotations

# structlog: 構造化ログライブラリ（JSONでログを出力）
import structlog
from uuid import UUID

# 監査アクション列挙型と監査ログエンティティ
from ..entities.audit_log import AuditAction, AuditLog
# 監査ログリポジトリのインターフェース（抽象クラス）
from ..repositories.audit_repository import AuditRepository

# ロガーの取得（このモジュール用のロガーインスタンス）
logger = structlog.get_logger()


class AuditService:
    """
    監査ログに関するビジネスロジックを提供するサービスクラス。

    主な機能：
    - 操作ログの記録（log_action）
    - ユーザーの操作履歴の取得
    - リソースの操作履歴の取得
    """

    def __init__(self, audit_repo: AuditRepository) -> None:
        """
        コンストラクタ（初期化メソッド）。

        【依存性注入（DI）パターン】
        リポジトリをコンストラクタの引数として受け取ることで、
        テスト時にモック（偽の実装）を渡すことができます。
        self._repo の先頭の「_」は「外部から直接アクセスしないで」という慣例。

        Args:
            audit_repo: 監査ログリポジトリの実装インスタンス
        """
        self._repo = audit_repo

    async def log_action(
        self,
        user_id: UUID,
        action: AuditAction,
        resource_type: str = "",
        resource_id: str = "",
        details: dict | None = None,
        ip_address: str = "",
        user_agent: str = "",
    ) -> AuditLog:
        """
        操作を監査ログとして記録する。

        全てのエンドポイントから呼び出される中心的なメソッド。
        ユーザーの操作（ログイン、ロボット作成、データ削除等）を
        データベースに保存し、構造化ログにも出力する。

        Args:
            user_id: 操作を行ったユーザーのID
            action: 操作の種類（LOGIN_SUCCESS, ROBOT_CREATE等）
            resource_type: 操作対象のリソース種別（"robot", "dataset"等）
            resource_id: 操作対象のリソースID
            details: 追加情報（辞書形式、省略可）
            ip_address: 操作元のIPアドレス
            user_agent: ブラウザ/クライアントの情報
        Returns:
            作成された監査ログエントリ
        """
        # AuditLog エンティティを作成
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},  # None の場合は空辞書 {} を使用
            ip_address=ip_address,
            user_agent=user_agent,
        )
        # リポジトリを使ってデータベースに保存
        created = await self._repo.create(entry)

        # 構造化ログにも記録（運用監視・デバッグ用）
        # structlog は key=value 形式でログを整理して出力する
        logger.info(
            "audit_log_created",         # ログのイベント名
            action=action.value,         # 操作の種類（文字列）
            user_id=str(user_id),        # ユーザーID
            resource_type=resource_type, # リソースの種類
            resource_id=resource_id,     # リソースのID
        )
        return created

    async def get_user_history(
        self, user_id: UUID, limit: int = 100
    ) -> list[AuditLog]:
        """
        特定ユーザーの操作履歴を取得する。
        管理者がユーザーの操作を確認する際に使用。

        Args:
            user_id: 対象ユーザーのID
            limit: 取得する最大件数
        Returns:
            監査ログのリスト
        """
        return await self._repo.get_by_user(user_id, limit=limit)

    async def get_resource_history(
        self, resource_type: str, resource_id: str
    ) -> list[AuditLog]:
        """
        特定リソースの操作履歴を取得する。
        例: あるロボットに対する全操作の履歴。

        Args:
            resource_type: リソースの種類（"robot", "dataset"等）
            resource_id: リソースのID
        Returns:
            監査ログのリスト
        """
        return await self._repo.get_by_resource(resource_type, resource_id)
