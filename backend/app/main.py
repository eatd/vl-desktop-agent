"""
FastAPI application with experimentation endpoints.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .benchmark import Benchmark, DEFAULT_TASKS
from .config import settings
from .models import Event
from .service import AgentService
from .trace import list_sessions, load_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VL Desktop Agent", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_service: AgentService | None = None
_benchmark: Benchmark | None = None


@app.on_event("startup")
async def on_startup() -> None:
    global _service, _benchmark
    _service = AgentService(asyncio.get_running_loop())
    _benchmark = Benchmark()
    logger.info(f"Started (model={settings.model}, dry_run={settings.dry_run})")


def service() -> AgentService:
    assert _service is not None
    return _service


# =============================================================================
# Agent Endpoints
# =============================================================================

@app.get("/api/status")
async def get_status() -> Dict[str, Any]:
    return service().status().model_dump()


@app.post("/api/run")
async def run_goal(payload: Dict[str, Any]) -> Dict[str, Any]:
    goal = str(payload.get("goal", "")).strip()
    if not goal:
        return {"ok": False, "error": "goal required"}
    
    ok = service().start(goal)
    return {"ok": ok, "status": service().status().model_dump()}


@app.post("/api/stop")
async def stop() -> Dict[str, Any]:
    service().stop()
    return {"ok": True, "status": service().status().model_dump()}


# =============================================================================
# Settings Endpoints
# =============================================================================

# Runtime-editable settings (separate from env-based config)
_runtime_settings: Dict[str, Any] = {
    "model": settings.model,
    "base_url": settings.base_url,
    "max_steps": settings.max_steps,
    "loop_delay": settings.loop_delay,
    "dry_run": settings.dry_run,
    "use_dxcam": settings.use_dxcam,
}


@app.get("/api/settings")
async def get_settings() -> Dict[str, Any]:
    """Get current runtime settings."""
    return {"settings": _runtime_settings}


@app.post("/api/settings")
async def update_settings_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update runtime settings."""
    global _runtime_settings
    
    # Update allowed settings
    allowed = {"model", "base_url", "max_steps", "loop_delay", "dry_run", "use_dxcam"}
    for key, value in payload.items():
        if key in allowed:
            _runtime_settings[key] = value
            # Also update the actual settings object
            if hasattr(settings, key):
                setattr(settings, key, value)
    
    return {"ok": True, "settings": _runtime_settings}


# =============================================================================
# Trace Endpoints
# =============================================================================

@app.get("/api/traces")
async def get_traces() -> Dict[str, Any]:
    """List all trace sessions."""
    return {"traces": list_sessions()}


@app.get("/api/traces/{session_id}")
async def get_trace(session_id: str) -> Dict[str, Any]:
    """Get detailed trace with all steps."""
    return load_session(session_id)


# =============================================================================
# Benchmark Endpoints
# =============================================================================

@app.get("/api/benchmark/tasks")
async def get_benchmark_tasks() -> List[Dict[str, Any]]:
    """List available benchmark tasks."""
    return [
        {"id": t.id, "goal": t.goal, "max_steps": t.max_steps}
        for t in DEFAULT_TASKS
    ]


@app.get("/api/benchmark/runs")
async def get_benchmark_runs() -> Dict[str, Any]:
    """List previous benchmark runs."""
    assert _benchmark is not None
    return {"runs": _benchmark.list_runs()}


# =============================================================================
# WebSocket
# =============================================================================

@app.websocket("/api/events")
async def ws_events(ws: WebSocket) -> None:
    await ws.accept()
    queue = await service().broadcaster.subscribe()
    
    await ws.send_json(Event(
        type="status",
        payload=service().status().model_dump()
    ).model_dump())
    
    try:
        while True:
            event = await queue.get()
            await ws.send_json(event.model_dump())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        if not str(type(e).__name__).startswith("ConnectionClosed"):
            logger.debug(f"WebSocket error: {e}")
    finally:
        await service().broadcaster.unsubscribe(queue)
