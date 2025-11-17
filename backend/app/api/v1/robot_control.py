"""
Robot Control API endpoints
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_mqtt_client
from app.config import settings
from app.core.mqtt import MQTTClient
from app.dependencies import get_db
from app.schemas.robot import (
    NavigationGoalCreate,
    NavigationGoalResponse,
    RobotStatusResponse,
    SimulatorStatus,
    VelocityCommand,
)

router = APIRouter()


@router.post("/velocity", status_code=200)
async def send_velocity_command(
    command: VelocityCommand,
    mqtt: MQTTClient = Depends(get_mqtt_client),
):
    """
    Send velocity command to robot via MQTT
    
    Note: This is typically handled via WebSocket for real-time control,
    but this endpoint provides a REST alternative
    """
    payload = {
        "vx": command.vx,
        "vy": command.vy,
        "vz": command.vz,
        "angular": command.angular,
    }
    
    await mqtt.publish(settings.MQTT_TOPIC_CMD_VEL, payload)
    
    return {"status": "sent", "command": payload}


@router.get("/status", response_model=RobotStatusResponse)
async def get_robot_status(db: AsyncSession = Depends(get_db)):
    """Get latest robot status"""
    # TODO: Implement - fetch latest status from database
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/navigation/goal", response_model=NavigationGoalResponse)
async def set_navigation_goal(
    goal: NavigationGoalCreate,
    db: AsyncSession = Depends(get_db),
    mqtt: MQTTClient = Depends(get_mqtt_client),
):
    """Set navigation goal for robot"""
    # TODO: Implement - save to DB and send via MQTT
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/navigation/goal")
async def cancel_navigation(mqtt: MQTTClient = Depends(get_mqtt_client)):
    """Cancel current navigation goal"""
    await mqtt.publish(settings.MQTT_TOPIC_NAV_CANCEL, {})
    return {"status": "cancelled"}


@router.get("/navigation/status")
async def get_navigation_status(db: AsyncSession = Depends(get_db)):
    """Get navigation status"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/simulator/start", response_model=SimulatorStatus)
async def start_simulator():
    """Start Unity simulator"""
    # TODO: Implement simulator process management
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/simulator/stop")
async def stop_simulator():
    """Stop Unity simulator"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/simulator/status", response_model=SimulatorStatus)
async def get_simulator_status():
    """Get simulator status"""
    # TODO: Implement
    return SimulatorStatus(is_running=False, process_id=None, started_at=None)
