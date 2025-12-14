"""
Application settings loaded from environment variables.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(key: str, default: bool) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes")


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


@dataclass
class Settings:
    """Application configuration."""
    
    # Model
    model: str = os.getenv("AGENT_MODEL", "qwen/qwen3-vl-4b")
    base_url: str = os.getenv("AGENT_BASE_URL", "http://localhost:1234/v1")
    api_key: str = os.getenv("AGENT_API_KEY", "EMPTY")
    timeout: float = _env_float("AGENT_TIMEOUT", 30.0)
    
    # Agent behavior
    max_steps: int = _env_int("AGENT_MAX_STEPS", 50)
    loop_delay: float = _env_float("AGENT_LOOP_DELAY", 0.3)
    dry_run: bool = _env_bool("AGENT_DRY_RUN", False)
    
    # Capture
    use_dxcam: bool = _env_bool("AGENT_USE_DXCAM", False)
    monitor_index: int = _env_int("AGENT_MONITOR_INDEX", 1)


settings = Settings()
