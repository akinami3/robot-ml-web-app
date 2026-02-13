"""SQLAlchemy implementation of RobotRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.robot import Robot, RobotCapability, RobotState
from ....domain.repositories.robot_repository import RobotRepository
from ..models import RobotModel


class SQLAlchemyRobotRepository(RobotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: RobotModel) -> Robot:
        caps = []
        if model.capabilities:
            for c in model.capabilities:
                try:
                    caps.append(RobotCapability(c))
                except ValueError:
                    pass
        return Robot(
            id=model.id,
            name=model.name,
            adapter_type=model.adapter_type,
            state=RobotState(model.state) if isinstance(model.state, str) else model.state,
            capabilities=caps,
            connection_params=model.connection_params or {},
            battery_level=model.battery_level,
            last_seen=model.last_seen,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Robot) -> RobotModel:
        return RobotModel(
            id=entity.id,
            name=entity.name,
            adapter_type=entity.adapter_type,
            state=entity.state,
            capabilities=[c.value for c in entity.capabilities],
            connection_params=entity.connection_params,
            battery_level=entity.battery_level,
            last_seen=entity.last_seen,
        )

    async def get_by_id(self, id: UUID) -> Robot | None:
        result = await self._session.get(RobotModel, id)
        return self._to_entity(result) if result else None

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[Robot]:
        stmt = select(RobotModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: Robot) -> Robot:
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: Robot) -> Robot:
        model = await self._session.get(RobotModel, entity.id)
        if model is None:
            raise ValueError(f"Robot {entity.id} not found")
        model.name = entity.name
        model.adapter_type = entity.adapter_type
        model.state = entity.state
        model.capabilities = [c.value for c in entity.capabilities]
        model.connection_params = entity.connection_params
        model.battery_level = entity.battery_level
        model.last_seen = entity.last_seen
        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, id: UUID) -> bool:
        model = await self._session.get(RobotModel, id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count(self) -> int:
        stmt = select(func.count()).select_from(RobotModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_by_name(self, name: str) -> Robot | None:
        stmt = select(RobotModel).where(RobotModel.name == name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_state(self, state: RobotState) -> list[Robot]:
        stmt = select(RobotModel).where(RobotModel.state == state)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update_state(self, robot_id: UUID, state: RobotState) -> bool:
        stmt = (
            update(RobotModel)
            .where(RobotModel.id == robot_id)
            .values(state=state)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def update_battery(self, robot_id: UUID, level: float) -> bool:
        stmt = (
            update(RobotModel)
            .where(RobotModel.id == robot_id)
            .values(battery_level=level)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
