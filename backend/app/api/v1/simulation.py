from __future__ import annotations

from fastapi import APIRouter

from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["simulation"])

_service = SimulationService()


@router.post("/start")
def start_simulation() -> dict[str, str]:
    _service.start()
    return {"status": "started"}


@router.post("/stop")
def stop_simulation() -> dict[str, str]:
    _service.stop()
    return {"status": "stopped"}
