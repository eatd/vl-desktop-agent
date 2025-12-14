"""
Agent service layer - manages lifecycle and events.
"""
from __future__ import annotations

import asyncio
import logging
import threading
from typing import Callable

from .agent import Agent
from .broadcast import Broadcaster
from .models import AgentStatus, Event
from .vision import ContinuousCapture
from .config import settings

logger = logging.getLogger(__name__)


class AgentService:
    """Manages agent lifecycle and event broadcasting."""
    
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self.broadcaster = Broadcaster()
        
        # Create capture and agent
        self._capture = ContinuousCapture(
            use_dxcam=settings.use_dxcam,
            monitor_index=settings.monitor_index,
        )
        self._agent = Agent(self._capture)
        
        # Start agent thread
        self._thread = threading.Thread(
            target=self._agent.run_loop,
            args=(self._publish,),
            daemon=True,
        )
        self._thread.start()
        logger.info("Agent service started")
    
    def _publish(self, event: Event) -> None:
        """Thread-safe event publishing."""
        asyncio.run_coroutine_threadsafe(
            self.broadcaster.broadcast(event),
            self._loop,
        )
    
    def status(self) -> AgentStatus:
        return self._agent.status()
    
    def start(self, goal: str) -> bool:
        return self._agent.start(goal)
    
    def stop(self) -> None:
        self._agent.stop()
