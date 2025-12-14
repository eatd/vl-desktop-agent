"""
Action models for the desktop agent.
"""
from __future__ import annotations

import time
from typing import Literal, Optional, Tuple

from pydantic import BaseModel, Field


# Qwen VL uses normalized coordinates in [0, 1000) range
COORD_MAX = 1000


class Action(BaseModel):
    """A single action from the VLM."""
    
    action: Literal["click", "type", "press", "scroll", "done"]
    coordinate: Optional[Tuple[int, int]] = Field(
        default=None, 
        description="(x, y) normalized coordinates [0-1000) for click"
    )
    text: Optional[str] = Field(
        default=None,
        description="Text to type"
    )
    key: Optional[str] = Field(
        default=None,
        description="Key to press (enter, escape, tab, etc.)"
    )
    direction: Optional[Literal["up", "down"]] = Field(
        default=None,
        description="Scroll direction"
    )
    reason: str = Field(
        default="",
        description="Why this action was chosen"
    )


class AgentStatus(BaseModel):
    """Current state of the agent."""
    running: bool = False
    goal: Optional[str] = None
    step: int = 0
    last_action: Optional[str] = None
    dry_run: bool = False


class Event(BaseModel):
    """Event sent to frontend via WebSocket."""
    type: str
    ts: float = Field(default_factory=lambda: time.time())
    payload: dict = Field(default_factory=dict)
