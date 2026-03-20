# =============================================================================
# Step 7: ロボットリポジトリ — ドメイン層インターフェース
# =============================================================================
#
# 【なぜ BaseRepository を直接使わない？】
# BaseRepository は汎用 CRUD のみ。
# Robot 固有の検索（名前検索、ステータス検索など）は
# RobotRepository に追加メソッドとして定義する。
#
# 設計の方針:
#   共通操作 → BaseRepository[T]
#   固有操作 → 各 Repository に追加
#
# =============================================================================

from app.domain.entities.robot import Robot, RobotStatus
from app.domain.repositories.base import BaseRepository


class RobotRepository(BaseRepository[Robot]):
    """
    ロボットリポジトリ — インターフェース

    BaseRepository の CRUD に加えて、
    Robot 固有の検索メソッドを追加する。
    """

    async def find_by_name(self, name: str) -> Robot | None:
        """
        名前でロボットを検索する

        完全一致検索。見つからない場合は None。
        デフォルト実装: list_all を全件取得して線形探索。
        SQLAlchemy 実装では WHERE 句で効率的に検索する。
        """
        robots = await self.list_all()
        for robot in robots:
            if robot.name == name:
                return robot
        return None

    async def find_by_status(self, status: RobotStatus) -> list[Robot]:
        """
        ステータスでロボットを絞り込む

        デフォルト実装: 全件取得 + フィルター。
        """
        robots = await self.list_all()
        return [r for r in robots if r.status == status]
