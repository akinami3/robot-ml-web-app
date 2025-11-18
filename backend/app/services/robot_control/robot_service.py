"""
Robot control service
"""
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.config import settings
from app.core.exceptions import RobotControlException
from app.core.mqtt import MQTTClient
from app.models.robot import NavigationGoal, RobotStatus
from app.repositories.robot import NavigationGoalRepository, RobotStatusRepository
from app.schemas.robot import (
    NavigationGoalCreate,
    NavigationGoalResponse,
    RobotStatusResponse,
    VelocityCommand,
)

logger = get_logger(__name__)


class RobotService:
    """Robot control service"""

    def __init__(self, mqtt_client: MQTTClient):
        self.mqtt = mqtt_client

    async def send_velocity_command(self, command: VelocityCommand) -> Dict:
        """
        Send velocity command to robot via MQTT
        
        Args:
            command: Velocity command
            
        Returns:
            Status dictionary
        """
        try:
            payload = {
                "vx": command.vx,
                "vy": command.vy,
                "vz": command.vz,
                "angular": command.angular,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self.mqtt.publish(settings.MQTT_TOPIC_CMD_VEL, payload)
            logger.info("velocity_command_sent", payload=payload)

            return {"status": "sent", "command": payload}

        except Exception as e:
            logger.error("velocity_command_error", error=str(e))
            raise RobotControlException(f"Failed to send velocity command: {str(e)}")

    async def get_latest_status(
        self, db: AsyncSession
    ) -> Optional[RobotStatusResponse]:
        """
        Get latest robot status
        
        Args:
            db: Database session
            
        Returns:
            Latest robot status or None
        """
        repo = RobotStatusRepository(db)
        status = await repo.get_latest()
        
        if not status:
            return None
        
        return RobotStatusResponse(
            id=status.id,
            position_x=status.position_x,
            position_y=status.position_y,
            orientation=status.orientation,
            battery_level=status.battery_level,
            is_moving=status.is_moving,
            timestamp=status.timestamp
        )

    async def create_navigation_goal(
        self, db: AsyncSession, goal: NavigationGoalCreate
    ) -> NavigationGoalResponse:
        """
        Create navigation goal and send to robot
        
        Args:
            db: Database session
            goal: Navigation goal data
            
        Returns:
            Created navigation goal
        """
        try:
            # Cancel any existing active goals
            goal_repo = NavigationGoalRepository(db)
            await goal_repo.cancel_active()
            
            # Create new goal in database
            goal_data = {
                "target_x": goal.target_x,
                "target_y": goal.target_y,
                "target_orientation": goal.target_orientation,
                "status": "active"
            }
            
            db_goal = await goal_repo.create(goal_data)
            
            # Send to MQTT
            payload = {
                "goal_id": str(db_goal.id),
                "x": goal.target_x,
                "y": goal.target_y,
                "orientation": goal.target_orientation,
            }
            
            await self.mqtt.publish(settings.MQTT_TOPIC_NAV_GOAL, payload)
            
            logger.info(f"Created navigation goal {db_goal.id}")
            
            return NavigationGoalResponse(
                id=db_goal.id,
                target_x=db_goal.target_x,
                target_y=db_goal.target_y,
                target_orientation=db_goal.target_orientation,
                status=db_goal.status,
                created_at=db_goal.created_at,
                completed_at=db_goal.completed_at
            )
        except Exception as e:
            logger.error(f"Failed to create navigation goal: {e}")
            raise RobotControlException(f"Failed to create navigation goal: {e}")

    async def cancel_navigation(self, db: AsyncSession) -> Dict:
        """
        Cancel current navigation goal
        
        Args:
            db: Database session
            
        Returns:
            Status dictionary
        """
        try:
            # Publish cancel command to MQTT
            await self.mqtt.publish(settings.MQTT_TOPIC_NAV_CANCEL, {})
            
            # Update active navigation goal in database
            goal_repo = NavigationGoalRepository(db)
            active_goal = await goal_repo.get_active()
            
            if active_goal:
                await goal_repo.update(
                    active_goal.id,
                    {"status": "cancelled"}
                )
                logger.info(f"Cancelled navigation goal {active_goal.id}")
            
            return {"status": "cancelled"}
        except Exception as e:
            logger.error("navigation_cancel_error", error=str(e))
            raise RobotControlException(f"Failed to cancel navigation: {str(e)}")

    async def get_active_navigation_goal(
        self,
        db: AsyncSession
    ) -> NavigationGoalResponse | None:
        """
        Get active navigation goal
        
        Args:
            db: Database session
            
        Returns:
            Active navigation goal or None
        """
        goal_repo = NavigationGoalRepository(db)
        goal = await goal_repo.get_active()
        
        if not goal:
            return None
        
        return NavigationGoalResponse(
            id=goal.id,
            target_x=goal.target_x,
            target_y=goal.target_y,
            target_orientation=goal.target_orientation,
            status=goal.status,
            created_at=goal.created_at,
            completed_at=goal.completed_at
        )


# Global instance
_robot_service: RobotService | None = None


def get_robot_service(mqtt_client: MQTTClient) -> RobotService:
    """Get robot service instance"""
    global _robot_service
    if _robot_service is None:
        _robot_service = RobotService(mqtt_client)
    return _robot_service
