"""
Gateway Client - HTTP client for communicating with Fleet Gateway
"""
import httpx
from typing import Optional
from app.config import get_settings
from app.schemas import CommandResponse

settings = get_settings()


class GatewayClient:
    """Client for communicating with Fleet Gateway"""
    
    def __init__(self):
        self.base_url = settings.GATEWAY_URL
        self.timeout = 10.0
    
    async def send_move_command(
        self,
        robot_id: str,
        goal_x: float,
        goal_y: float,
        goal_theta: float = 0.0
    ) -> CommandResponse:
        """Send move command to robot via gateway"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/commands/move",
                    json={
                        "robot_id": robot_id,
                        "goal": {
                            "x": goal_x,
                            "y": goal_y,
                            "theta": goal_theta
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                return CommandResponse(
                    success=data.get("success", True),
                    message=data.get("message", "Command sent"),
                    command_id=data.get("command_id")
                )
        except httpx.HTTPError as e:
            return CommandResponse(
                success=False,
                message=f"Failed to send command: {str(e)}"
            )
    
    async def send_stop_command(self, robot_id: str) -> CommandResponse:
        """Send stop command to robot via gateway"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/commands/stop",
                    json={"robot_id": robot_id}
                )
                response.raise_for_status()
                data = response.json()
                return CommandResponse(
                    success=data.get("success", True),
                    message=data.get("message", "Command sent"),
                    command_id=data.get("command_id")
                )
        except httpx.HTTPError as e:
            return CommandResponse(
                success=False,
                message=f"Failed to send command: {str(e)}"
            )
    
    async def get_robot_status(self, robot_id: str) -> Optional[dict]:
        """Get robot status from gateway"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/robots/{robot_id}/status"
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError:
            return None
    
    async def health_check(self) -> bool:
        """Check gateway health"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
