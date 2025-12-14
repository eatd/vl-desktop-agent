"""
Action trace recording for debugging and experiments.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

TRACE_DIR = Path(os.getenv("AGENT_TRACE_DIR", "./traces"))


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_step(
    session_id: str,
    step: int,
    screenshot: Optional[np.ndarray],
    action: Dict[str, Any],
    raw_response: str = "",
    frame_change: float = 0.0,
    verified: bool = True,
) -> None:
    """Save a single step with full context for analysis."""
    session_dir = TRACE_DIR / session_id
    _ensure_dir(session_dir)
    
    # Save screenshot
    if screenshot is not None:
        img_path = session_dir / f"step_{step:03d}.jpg"
        cv2.imwrite(str(img_path), screenshot, [cv2.IMWRITE_JPEG_QUALITY, 80])
    
    # Enhanced step data
    step_data = {
        "step": step,
        "ts": time.time(),
        "action": action,
        "raw_response": raw_response,  # Full model output
        "frame_change": frame_change,   # % pixels changed
        "verified": verified,           # Did action have effect?
    }
    
    steps_file = session_dir / "steps.jsonl"
    with open(steps_file, "a") as f:
        f.write(json.dumps(step_data) + "\n")


def save_session(
    session_id: str,
    goal: str,
    status: str,
    total_steps: int,
    success_rate: float = 0.0,
) -> Path:
    """Finalize session with summary stats."""
    session_dir = TRACE_DIR / session_id
    _ensure_dir(session_dir)
    
    meta = {
        "session_id": session_id,
        "goal": goal,
        "status": status,
        "total_steps": total_steps,
        "success_rate": success_rate,
        "end_time": time.time(),
    }
    
    meta_path = session_dir / "meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    
    logger.info(f"Saved trace: {session_dir}")
    return session_dir


def list_sessions() -> List[Dict[str, Any]]:
    """List all sessions with stats."""
    if not TRACE_DIR.exists():
        return []
    
    sessions = []
    for entry in sorted(TRACE_DIR.iterdir(), reverse=True):
        if entry.is_dir():
            meta_file = entry / "meta.json"
            if meta_file.exists():
                with open(meta_file) as f:
                    sessions.append(json.load(f))
    return sessions


def load_session(session_id: str) -> Dict[str, Any]:
    """Load full session data for analysis."""
    session_dir = TRACE_DIR / session_id
    
    meta_file = session_dir / "meta.json"
    steps_file = session_dir / "steps.jsonl"
    
    data = {"session_id": session_id, "steps": []}
    
    if meta_file.exists():
        with open(meta_file) as f:
            data.update(json.load(f))
    
    if steps_file.exists():
        with open(steps_file) as f:
            data["steps"] = [json.loads(line) for line in f]
    
    return data
