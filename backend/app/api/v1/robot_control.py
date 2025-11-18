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
from app.services.robot_control.robot_service import get_robot_service
from app.services.robot_control.simulator_service import get_simulator_service

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
    robot_service = get_robot_service(mqtt)
    return await robot_service.send_velocity_command(command)


@router.get("/status", response_model=RobotStatusResponse)
async def get_robot_status(
    db: AsyncSession = Depends(get_db),
    mqtt: MQTTClient = Depends(get_mqtt_client),
):
    """Get latest robot status"""
    robot_service = get_robot_service(mqtt)
    status = await robot_service.get_latest_status(db)
    if not status:
        raise HTTPException(status_code=404, detail="No robot status available")
    return status


@router.post("/navigation/goal", response_model=NavigationGoalResponse)
async def set_navigation_goal(
    goal: NavigationGoalCreate,
    db: AsyncSession = Depends(get_db),
    mqtt: MQTTClient = Depends(get_mqtt_client),
):
    """Set navigation goal for robot"""
    robot_service = get_robot_service(mqtt)
    return await robot_service.create_navigation_goal(db, goal)


@router.delete("/navigation/goal")
async def cancel_navigation(
    db: AsyncSession = Depends(get_db),
    mqtt: MQTTClient = Depends(get_mqtt_client),
):
    """Cancel current navigation goal"""
    robot_service = get_robot_service(mqtt)
    return await robot_service.cancel_navigation(db)


@router.get("/navigation/status")
async def get_navigation_status(
    db: AsyncSession = Depends(get_db),
    mqtt: MQTTClient = Depends(get_mqtt_client),
):
    """Get navigation status"""
    robot_service = get_robot_service(mqtt)
    goal = await robot_service.get_active_navigation_goal(db)
    if not goal:
        return {"status": "no_active_goal"}
    return goal


@router.post("/simulator/start", response_model=SimulatorStatus)
async def start_simulator():
    """Start Unity simulator"""
    simulator_service = get_simulator_service()
    result = await simulator_service.start()
    return SimulatorStatus(**result)


@router.post("/simulator/stop")
async def stop_simulator():
    """Stop Unity simulator"""
    simulator_service = get_simulator_service()
    return await simulator_service.stop()


@router.get("/simulator/status", response_model=SimulatorStatus)
async def get_simulator_status():
    """Get simulator status"""
    simulator_service = get_simulator_service()
    status = simulator_service.get_status()
    return SimulatorStatus(**status)
