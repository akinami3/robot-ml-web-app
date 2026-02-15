# ============================================================
# 監査ログリポジトリインターフェース
# （Audit Repository Interface）
# ============================================================
# 監査ログ（誰が・いつ・何をしたかの記録）の保存・取得に
# 特化したリポジトリの「設計図」です。
#
# 【監査ログが重要な理由】
# - セキュリティ: 不正アクセスの検知・追跡
# - コンプライアンス: 法令遵守のための記録
# - デバッグ: 問題発生時の原因調査
# - 運用監視: システムの利用状況の把握
#
# 監査ログは「書き込みが多く、読み出しは少ない」という
# 特性があるため、効率的な書き込みが重要です。
# ============================================================
"""Audit log repository interface."""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from uuid import UUID

# 監査アクション（ログイン、ロボット作成 等）の列挙型と監査ログエンティティ
from ..entities.audit_log import AuditAction, AuditLog
from .base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """
    監査ログリポジトリの抽象インターフェース。

    監査ログの検索・フィルタリング・古いデータの削除メソッドを定義。
    """

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        特定ユーザーの操作履歴を取得する。
        オプションで時間範囲を指定可能。

        Args:
            user_id: 対象ユーザーのID
            start_time: 検索開始時刻（省略可）
            end_time: 検索終了時刻（省略可）
            limit: 最大取得件数（デフォルト: 100）
        Returns:
            監査ログのリスト（新しい順）
        """
        ...

    @abstractmethod
    async def get_by_action(
        self,
        action: AuditAction,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        特定のアクション種別でログを検索する。
        例: AuditAction.LOGIN_SUCCESS でログイン成功の履歴を取得。

        Args:
            action: 検索するアクションの種類
            limit: 最大取得件数
        Returns:
            該当するログのリスト
        """
        ...

    @abstractmethod
    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[AuditLog]:
        """
        特定のリソース（ロボット、データセット等）に対する
        操作履歴を取得する。

        例: resource_type="robot", resource_id="abc-123"
        → そのロボットに対する全操作（作成、更新、削除）の履歴

        Args:
            resource_type: リソースの種類（"robot", "dataset" 等）
            resource_id: リソースのID（文字列形式）
        Returns:
            該当するログのリスト
        """
        ...

    @abstractmethod
    async def delete_older_than(self, before: datetime) -> int:
        """
        指定日時より古い監査ログを削除する。
        ストレージ容量の管理のため定期的に実行。

        【注意】
        監査ログの保持期間は法令やポリシーで定められている場合があるため、
        削除する前に保持期間の確認が必要です。

        Args:
            before: この日時より古いログを削除
        Returns:
            削除された件数
        """
        ...
