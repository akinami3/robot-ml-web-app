from .auth import router as auth_router
from .robots import router as robots_router
from .missions import router as missions_router
from .sensor_data import router as sensor_data_router
from .command_data import router as command_data_router

__all__ = ["auth_router", "robots_router", "missions_router", "sensor_data_router", "command_data_router"]
