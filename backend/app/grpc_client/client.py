"""
Fleet Gateway gRPC Client

Backend → Gateway間のgRPC通信を担当するクライアント。
HealthCheck / GetAllRobots / SendCommand 等のRPCをGatewayに送信する。

NOTE: 現在は簡易実装（stub）。Docker build時に生成される fleet_pb2/fleet_pb2_grpc を
      利用した本番実装はコメントで記載。
"""

import grpc
from typing import Optional, List, Dict, Any, AsyncIterator
import logging
from contextlib import asynccontextmanager

from app.config import settings

logger = logging.getLogger(__name__)

# Auto-generated proto stubs (available after Docker build)
try:
    from app.grpc_client import fleet_pb2, fleet_pb2_grpc
    _PROTO_AVAILABLE = True
except ImportError:
    fleet_pb2 = None
    fleet_pb2_grpc = None
    _PROTO_AVAILABLE = False


class FleetGatewayClient:
    """Fleet Gateway gRPCクライアント"""
    
    def __init__(self, gateway_address: str = None):
        self.address = gateway_address or settings.GATEWAY_GRPC_ADDRESS
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub = None
    
    async def connect(self) -> None:
        """gRPCチャネルを確立"""
        if self._channel is None:
            self._channel = grpc.aio.insecure_channel(self.address)
            if _PROTO_AVAILABLE:
                self._stub = fleet_pb2_grpc.FleetGatewayStub(self._channel)
            logger.info(f"Connected to Fleet Gateway at {self.address}")
    
    async def disconnect(self) -> None:
        """gRPCチャネルを切断"""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info("Disconnected from Fleet Gateway")
    
    async def health_check(self) -> Dict[str, Any]:
        """Gateway のヘルスチェック"""
        try:
            if self._stub and _PROTO_AVAILABLE:
                response = await self._stub.HealthCheck(fleet_pb2.Empty())
                return {
                    "healthy": response.healthy,
                    "version": response.version,
                    "connected_robots": response.connected_robots,
                    "uptime_seconds": response.uptime_seconds,
                }
            # Fallback: proto未生成時
            return {
                "healthy": True,
                "version": "1.0.0",
                "connected_robots": 0,
                "uptime_seconds": 0,
            }
        except grpc.RpcError as e:
            logger.error(f"Health check failed: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def get_all_robots(self) -> List[Dict[str, Any]]:
        """全ロボットの状態を取得"""
        try:
            if self._stub and _PROTO_AVAILABLE:
                response = await self._stub.GetAllRobots(fleet_pb2.Empty())
                return [_robot_status_to_dict(r) for r in response.robots]
            return []
        except grpc.RpcError as e:
            logger.error(f"GetAllRobots failed: {e}")
            raise
    
    async def get_robot(self, robot_id: str) -> Optional[Dict[str, Any]]:
        """特定ロボットの状態を取得"""
        try:
            if self._stub and _PROTO_AVAILABLE:
                request = fleet_pb2.RobotId(id=robot_id)
                response = await self._stub.GetRobot(request)
                return _robot_status_to_dict(response)
            return None
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            logger.error(f"GetRobot failed: {e}")
            raise
    
    async def send_command(
        self,
        robot_id: str,
        command_type: str,
        parameters: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """ロボットにコマンドを送信"""
        command_type_map = {
            "move": 1,
            "stop": 2,
            "pause": 3,
            "resume": 4,
            "dock": 5,
            "undock": 6,
            "localize": 7,
        }
        
        try:
            if self._stub and _PROTO_AVAILABLE:
                request = fleet_pb2.Command(
                    robot_id=robot_id,
                    type=command_type_map.get(command_type, 0),
                    parameters=parameters or {},
                )
                response = await self._stub.SendCommand(request)
                return {
                    "success": response.success,
                    "message": response.message,
                    "command_id": response.command_id,
                }
            # Fallback: proto未生成時
            return {
                "success": True,
                "message": "command sent (stub)",
                "command_id": "stub-cmd",
            }
        except grpc.RpcError as e:
            logger.error(f"SendCommand failed: {e}")
            return {"success": False, "message": str(e), "command_id": ""}
    
    async def start_mission(
        self,
        mission_id: str,
        robot_id: str,
        mission_type: str,
        waypoints: List[Dict[str, Any]],
        priority: int = 0,
        parameters: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """ミッションを開始"""
        mission_type_map = {
            "transport": 1,
            "patrol": 2,
            "charge": 3,
            "custom": 4,
        }
        
        try:
            if self._stub and _PROTO_AVAILABLE:
                wp_list = []
                for wp in waypoints:
                    pos = fleet_pb2.Position(
                        x=wp.get("x", 0.0),
                        y=wp.get("y", 0.0),
                        theta=wp.get("theta", 0.0),
                    )
                    wp_list.append(fleet_pb2.Waypoint(
                        id=wp.get("id", ""),
                        position=pos,
                        action=wp.get("action", 0),
                        wait_time_sec=wp.get("wait_time_sec", 0),
                    ))
                request = fleet_pb2.MissionRequest(
                    mission_id=mission_id,
                    robot_id=robot_id,
                    type=mission_type_map.get(mission_type, 0),
                    waypoints=wp_list,
                    priority=priority,
                    parameters=parameters or {},
                )
                response = await self._stub.StartMission(request)
                return {
                    "success": response.success,
                    "message": response.message,
                    "status": response.status,
                }
            # Fallback
            return {
                "success": True,
                "message": "mission started (stub)",
                "status": 2,
            }
        except grpc.RpcError as e:
            logger.error(f"StartMission failed: {e}")
            return {"success": False, "message": str(e), "status": 0}
    
    async def cancel_mission(self, mission_id: str) -> Dict[str, Any]:
        """ミッションをキャンセル"""
        try:
            if self._stub and _PROTO_AVAILABLE:
                request = fleet_pb2.MissionId(id=mission_id)
                response = await self._stub.CancelMission(request)
                return {
                    "success": response.success,
                    "message": response.message,
                    "status": response.status,
                }
            # Fallback
            return {
                "success": True,
                "message": "mission cancelled (stub)",
                "status": 4,
            }
        except grpc.RpcError as e:
            logger.error(f"CancelMission failed: {e}")
            return {"success": False, "message": str(e), "status": 0}
    
    async def stream_robot_status(
        self,
        robot_ids: List[str] = None,
        interval_ms: int = 1000
    ) -> AsyncIterator[Dict[str, Any]]:
        """ロボット状態のストリーミングを受信"""
        try:
            if self._stub and _PROTO_AVAILABLE:
                request = fleet_pb2.StreamRequest(
                    robot_ids=robot_ids or [],
                    interval_ms=interval_ms,
                )
                async for status in self._stub.StreamRobotStatus(request):
                    yield _robot_status_to_dict(status)
            else:
                return
        except grpc.RpcError as e:
            logger.error(f"StreamRobotStatus failed: {e}")
            raise


# シングルトンインスタンス
_gateway_client: Optional[FleetGatewayClient] = None


def get_gateway_client() -> FleetGatewayClient:
    """Gateway クライアントのシングルトンを取得"""
    global _gateway_client
    if _gateway_client is None:
        _gateway_client = FleetGatewayClient()
    return _gateway_client


@asynccontextmanager
async def gateway_client_context():
    """Gateway クライアントのコンテキストマネージャー"""
    client = get_gateway_client()
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()


def _robot_status_to_dict(status) -> Dict[str, Any]:
    """Protobuf RobotStatus メッセージを辞書に変換"""
    pos = status.position if status.position else None
    return {
        "id": status.id,
        "name": status.name,
        "vendor": status.vendor,
        "model": status.model,
        "state": status.state,
        "position": {
            "x": pos.x if pos else 0.0,
            "y": pos.y if pos else 0.0,
            "theta": pos.theta if pos else 0.0,
        },
        "battery_level": status.battery_level,
        "current_mission_id": status.current_mission_id,
        "last_seen": status.last_seen,
        "metadata": dict(status.metadata) if status.metadata else {},
    }
