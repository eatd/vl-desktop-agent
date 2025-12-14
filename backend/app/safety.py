"""
Safety guardrails for desktop agent actions.
"""
from __future__ import annotations

import re
from typing import Optional, Set

# Hotkeys that could cause data loss or system issues
BLOCKED_HOTKEYS: Set[str] = {
    "alt+f4",
    "ctrl+alt+delete",
    "win+r",
    "win+l",
    "ctrl+shift+escape",
}

# Patterns in text that suggest dangerous commands
DANGEROUS_PATTERNS = [
    re.compile(r"rm\s+-rf", re.IGNORECASE),
    re.compile(r"format\s+[a-z]:", re.IGNORECASE),
    re.compile(r"del\s+/[sfq]", re.IGNORECASE),
]


def is_safe_hotkey(key_combo: str) -> tuple[bool, Optional[str]]:
    """Check if a hotkey is safe to execute."""
    normalized = key_combo.lower().replace(" ", "")
    if normalized in BLOCKED_HOTKEYS:
        return False, f"Blocked hotkey: {key_combo}"
    return True, None


def is_safe_text(text: str) -> tuple[bool, Optional[str]]:
    """Check if text content is safe to type."""
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(text):
            return False, f"Dangerous command pattern detected"
    return True, None
