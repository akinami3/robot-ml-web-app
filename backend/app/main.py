from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import chatbot, ml, robot_control, simulation, telemetry
from app.api.ws import router as ws_router
from app.core.config import get_settings
from app.core.events import lifespan

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.backend_cors_origins] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(robot_control.router, prefix=settings.api_v1_prefix)
app.include_router(telemetry.router, prefix=settings.api_v1_prefix)
app.include_router(ml.router, prefix=settings.api_v1_prefix)
app.include_router(chatbot.router, prefix=settings.api_v1_prefix)
app.include_router(simulation.router, prefix=settings.api_v1_prefix)
app.include_router(ws_router.router, prefix=settings.ws_prefix)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
