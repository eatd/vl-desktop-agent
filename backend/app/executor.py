"""
Execute actions using pyautogui.

IMPORTANT: Qwen3-VL outputs normalized coordinates in [0, 1000) range.
This module scales them to actual screen pixels.
"""
from __future__ import annotations

import logging
from typing import Optional, Tuple

import pyautogui

from .models import Action, COORD_MAX
from .safety import is_safe_hotkey, is_safe_text

logger = logging.getLogger(__name__)

# Safety settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


def scale_coords(
    normalized: Tuple[int, int],
) -> Tuple[int, int]:
    """
    Scale normalized [0, 1000) coordinates to screen pixels.
    
    Qwen VL outputs coordinates where:
    - (0, 0) = top-left
    - (1000, 1000) = bottom-right
    """
    norm_x, norm_y = normalized
    screen_w, screen_h = pyautogui.size()
    
    # Scale from 0-1000 to screen dimensions
    pixel_x = int((norm_x / COORD_MAX) * screen_w)
    pixel_y = int((norm_y / COORD_MAX) * screen_h)
    
    # Clamp to screen bounds
    pixel_x = max(0, min(pixel_x, screen_w - 1))
    pixel_y = max(0, min(pixel_y, screen_h - 1))
    
    return pixel_x, pixel_y


def execute(action: Action, dry_run: bool = False) -> Tuple[str, Optional[Tuple[int, int]]]:
    """
    Execute an action and return (description, screen_coordinates).
    """
    coords = None
    
    if action.action == "click":
        if action.coordinate is None:
            return "Click failed: no coordinates", None
        
        coords = scale_coords(action.coordinate)
        desc = f"Click at {coords} (norm: {action.coordinate})"
        
        if not dry_run:
            pyautogui.click(coords[0], coords[1])
    
    elif action.action == "type":
        if not action.text:
            return "Type failed: no text", None
        
        safe, reason = is_safe_text(action.text)
        if not safe:
            return f"Type blocked: {reason}", None
        
        desc = f"Type: {action.text[:30]}..."
        
        if not dry_run:
            pyautogui.write(action.text, interval=0.02)
    
    elif action.action == "press":
        if not action.key:
            return "Press failed: no key", None
        
        # Check if it's a combo like "ctrl+c"
        if "+" in action.key:
            safe, reason = is_safe_hotkey(action.key)
            if not safe:
                return f"Hotkey blocked: {reason}", None
            
            keys = action.key.lower().split("+")
            desc = f"Hotkey: {action.key}"
            
            if not dry_run:
                pyautogui.hotkey(*keys)
        else:
            desc = f"Press: {action.key}"
            if not dry_run:
                pyautogui.press(action.key)
    
    elif action.action == "scroll":
        direction = action.direction or "down"
        amount = -3 if direction == "down" else 3
        desc = f"Scroll {direction}"
        
        if not dry_run:
            pyautogui.scroll(amount)
    
    elif action.action == "done":
        desc = f"Done: {action.reason}"
    
    else:
        desc = f"Unknown action: {action.action}"
    
    logger.debug(f"Executed: {desc}")
    return desc, coords
