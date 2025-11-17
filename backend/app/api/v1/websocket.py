"""
WebSocket endpoints for real-time communication
"""
import json
from typing import Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from structlog import get_logger

from app.api.deps import get_mqtt_client, get_ws_manager
from app.config import settings
from app.core.mqtt import MQTTClient
from app.core.websocket import ConnectionManager

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/robot")
async def websocket_robot_endpoint(
    websocket: WebSocket,
    ws_manager: ConnectionManager = Depends(get_ws_manager),
    mqtt: MQTTClient = Depends(get_mqtt_client),
):
    """
    WebSocket endpoint for robot control
    
    Handles:
    - Velocity commands from frontend
    - Robot status updates to frontend
    - Camera feed to frontend
    """
    await ws_manager.connect(websocket, channel="robot")
    
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            payload = message.get("data", {})
            
            if message_type == "velocity_command":
                # Forward velocity command to robot via MQTT
                await mqtt.publish(settings.MQTT_TOPIC_CMD_VEL, payload)
                logger.debug("velocity_command_sent", payload=payload)
                
            elif message_type == "subscribe_status":
                # Client wants to subscribe to robot status updates
                # Status updates are handled by MQTT message handlers
                pass
                
            else:
                logger.warning("unknown_message_type", type=message_type)
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel="robot")
        logger.info("websocket_robot_disconnected")
    except Exception as e:
        logger.error("websocket_robot_error", error=str(e))
        ws_manager.disconnect(websocket, channel="robot")


@router.websocket("/ml/training")
async def websocket_ml_training_endpoint(
    websocket: WebSocket,
    ws_manager: ConnectionManager = Depends(get_ws_manager),
):
    """
    WebSocket endpoint for ML training
    
    Provides real-time training metrics updates
    """
    await ws_manager.connect(websocket, channel="ml")
    
    try:
        while True:
            # Keep connection alive and receive any control messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Training metrics are pushed from training service via ws_manager.broadcast()
            logger.debug("ml_websocket_message", message=message)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel="ml")
        logger.info("websocket_ml_disconnected")
    except Exception as e:
        logger.error("websocket_ml_error", error=str(e))
        ws_manager.disconnect(websocket, channel="ml")


@router.websocket("/connection")
async def websocket_connection_monitor(
    websocket: WebSocket,
    ws_manager: ConnectionManager = Depends(get_ws_manager),
    mqtt: MQTTClient = Depends(get_mqtt_client),
):
    """
    WebSocket endpoint for connection status monitoring
    
    Provides:
    - MQTT connection status
    - WebSocket connection status
    """
    await ws_manager.connect(websocket, channel="general")
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connection_status",
            "data": {
                "mqtt": mqtt.connected,
                "websocket": True,
            }
        })
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Send status update if requested
            message = json.loads(data)
            if message.get("type") == "status_request":
                await websocket.send_json({
                    "type": "connection_status",
                    "data": {
                        "mqtt": mqtt.connected,
                        "websocket": True,
                    }
                })
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel="general")
        logger.info("websocket_connection_monitor_disconnected")
    except Exception as e:
        logger.error("websocket_connection_monitor_error", error=str(e))
        ws_manager.disconnect(websocket, channel="general")
