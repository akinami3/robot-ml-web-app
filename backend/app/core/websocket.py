"""
WebSocket connection manager
"""
import asyncio
from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect
from structlog import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """WebSocket connection manager"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "robot": [],
            "ml": [],
            "general": [],
        }

    async def connect(self, websocket: WebSocket, channel: str = "general") -> None:
        """
        Accept and register new WebSocket connection

        Args:
            websocket: WebSocket connection
            channel: Channel name (robot, ml, general)
        """
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logger.info("websocket_connected", channel=channel, total=len(self.active_connections[channel]))

    def disconnect(self, websocket: WebSocket, channel: str = "general") -> None:
        """
        Remove WebSocket connection

        Args:
            websocket: WebSocket connection
            channel: Channel name
        """
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
                logger.info(
                    "websocket_disconnected",
                    channel=channel,
                    total=len(self.active_connections[channel]),
                )

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """
        Send message to specific client

        Args:
            message: Message data
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("websocket_send_error", error=str(e))

    async def broadcast(self, message: dict, channel: str = "general") -> None:
        """
        Broadcast message to all clients in channel

        Args:
            message: Message data
            channel: Target channel name
        """
        if channel not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error("websocket_broadcast_error", error=str(e))
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection, channel)

    async def broadcast_to_all(self, message: dict) -> None:
        """
        Broadcast message to all clients in all channels

        Args:
            message: Message data
        """
        for channel in self.active_connections:
            await self.broadcast(message, channel)

    def get_connection_count(self, channel: str = None) -> int:
        """
        Get number of active connections

        Args:
            channel: Specific channel (None for total count)

        Returns:
            Number of connections
        """
        if channel:
            return len(self.active_connections.get(channel, []))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
ws_manager = ConnectionManager()


async def heartbeat_task(manager: ConnectionManager, interval: int = 30) -> None:
    """
    Send periodic heartbeat to all connections

    Args:
        manager: Connection manager instance
        interval: Heartbeat interval in seconds
    """
    while True:
        await asyncio.sleep(interval)
        heartbeat_msg = {"type": "heartbeat", "data": {"status": "alive"}}
        await manager.broadcast_to_all(heartbeat_msg)
