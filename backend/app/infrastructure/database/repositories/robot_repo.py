# =============================================================================
# Step 7: SQLAlchemy ロボットリポジトリ実装
# =============================================================================
#
# 【このファイルの位置づけ】
#
#   ドメイン層:      RobotRepository (インターフェース)
#                      ↑ 依存の方向（内側を参照）
#   インフラ層:      SQLAlchemyRobotRepository ★ (このファイル)
#
# ドメイン層の RobotRepository インターフェースを「実装」する。
# SQLAlchemy 固有のコード（select, Session, commit）はここだけに閉じ込める。
#
# もし将来 MongoDB に変えたくなったら、
# MongoRobotRepository を作って差し替えるだけ。
# API 層もドメイン層も影響を受けない = Clean Architecture の効果。
#
# 【SQLAlchemy 2.0 のクエリ構文】
# 旧 (1.x): session.query(Robot).filter(Robot.name == "foo").all()
# 新 (2.0): session.execute(select(Robot).where(Robot.name == "foo"))
#
# 新しい構文は:
#   - 型安全（IDE の補完が効く）
#   - 非同期対応
#   - SQL に近い（SELECT, WHERE がそのまま）
#
# =============================================================================

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.robot import Robot, RobotStatus, RobotType
from app.domain.repositories.robot_repo import RobotRepository
from app.infrastructure.database.models import RobotModel


class SQLAlchemyRobotRepository(RobotRepository):
    """
    SQLAlchemy によるロボットリポジトリの実装

    【コンストラクタに Session を注入する理由】
    Repository 自身は Session を作らず、外部から受け取る。
    → 1リクエスト = 1セッション を API 層で管理できる。
    → トランザクションのスコープを上位層が制御できる。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # =========================================================================
    # エンティティ ↔ ORM モデルの変換
    # =========================================================================
    #
    # 【なぜ変換が必要？】
    # ドメイン層の Robot（dataclass）と
    # インフラ層の RobotModel（ORM）は別のクラス。
    # リポジトリが変換の責務を持つ。
    #
    # 小規模プロジェクトでは ORM モデルをそのまま使うこともあるが、
    # 学習のため Clean Architecture に従う。

    @staticmethod
    def _to_entity(model: RobotModel) -> Robot:
        """ORM モデル → ドメインエンティティ"""
        return Robot(
            id=model.id,
            name=model.name,
            robot_type=RobotType(model.robot_type),
            description=model.description,
            status=RobotStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Robot) -> RobotModel:
        """ドメインエンティティ → ORM モデル"""
        return RobotModel(
            id=entity.id,
            name=entity.name,
            robot_type=entity.robot_type.value,
            description=entity.description,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    # =========================================================================
    # CRUD 実装
    # =========================================================================

    async def get_by_id(self, entity_id: UUID) -> Robot | None:
        """
        ID で1件取得

        【session.get() とは？】
        主キーで直接取得する最も効率的な方法。
        内部的には `SELECT * FROM robots WHERE id = :id` と同等。
        キャッシュ（Identity Map）が効くため、同一セッション内では高速。
        """
        model = await self._session.get(RobotModel, entity_id)
        if model is None:
            return None
        return self._to_entity(model)

    async def list_all(self) -> list[Robot]:
        """
        全件取得

        【select() とは？】
        SQLAlchemy 2.0 のクエリビルダー。
        select(RobotModel) → SELECT * FROM robots

        .order_by(RobotModel.created_at.desc())
        → ORDER BY created_at DESC（新しい順）

        【scalars() とは？】
        execute() の結果は Row オブジェクト（タプルのようなもの）。
        scalars() で ORM モデルオブジェクトに変換する。
        .all() でリストとして取得。
        """
        stmt = select(RobotModel).order_by(RobotModel.created_at.desc())
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def create(self, entity: Robot) -> Robot:
        """
        新規作成

        【session.add() とは？】
        セッションの「変更リスト」にオブジェクトを追加する。
        この時点ではまだ SQL は実行されない。

        【session.flush() とは？】
        変更リストの内容を DB に反映する（INSERT 文を実行）。
        ただしトランザクションはまだコミットされていない。
        flush 後は DB が採番した値（server_default など）が反映される。

        【session.commit() とは？】
        トランザクションを確定する。
        commit しないと、セッション終了時にロールバックされる。

        refresh は commit 後にオブジェクトを最新の DB 状態で更新する。
        """
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: Robot) -> Robot:
        """
        更新

        【merge() とは？】
        指定されたオブジェクトを現在のセッションにマージする。
        - セッションに同じ ID のオブジェクトがあれば → フィールドを上書き
        - なければ → DB から取得して上書き
        """
        model = await self._session.get(RobotModel, entity.id)
        if model is None:
            msg = f"Robot not found: {entity.id}"
            raise ValueError(msg)

        # フィールドを更新
        model.name = entity.name
        model.robot_type = entity.robot_type.value
        model.description = entity.description
        model.status = entity.status.value
        model.updated_at = datetime.now(timezone.utc)

        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, entity_id: UUID) -> bool:
        """
        削除

        【session.delete() とは？】
        オブジェクトを削除対象としてマークする。
        commit 時に DELETE 文が実行される。
        """
        model = await self._session.get(RobotModel, entity_id)
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True

    async def count(self) -> int:
        """
        総数取得

        【func.count() とは？】
        SQL の COUNT() 関数。
        SELECT COUNT(*) FROM robots と同等。
        全件取得して len() するより効率的。
        """
        stmt = select(func.count()).select_from(RobotModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # =========================================================================
    # Robot 固有のメソッド（効率的に実装）
    # =========================================================================

    async def find_by_name(self, name: str) -> Robot | None:
        """
        名前で検索（WHERE 句を使って効率的に）

        BaseRepository のデフォルト実装（全件取得 + フィルター）を
        SQLAlchemy の WHERE 句で上書きする。
        """
        stmt = select(RobotModel).where(RobotModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if model is None:
            return None
        return self._to_entity(model)

    async def find_by_status(self, status: RobotStatus) -> list[Robot]:
        """ステータスで検索"""
        stmt = (
            select(RobotModel)
            .where(RobotModel.status == status.value)
            .order_by(RobotModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
