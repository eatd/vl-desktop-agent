"""
Action Executor.

Handles coordinate mapping and PyAutoGUI interaction.
Refactored to handle resolution mismatches correctly.
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
pyautogui.PAUSE = 0.1 # Small pause between actions

def scale_coords(
    normalized: Tuple[int, int],
    capture_size: Tuple[int, int],
    screen_size: Tuple[int, int]
) -> Tuple[int, int]:
    """
    Map coordinates from the VLM's normalized space -> Capture Space -> Screen Space.
    
    Args:
        normalized: (x, y) from model in [0, 1000)
        capture_size: (width, height) of the image sent to model
        screen_size: (width, height) of the actual monitor
    """
    norm_x, norm_y = normalized
    cap_w, cap_h = capture_size
    scr_w, scr_h = screen_size

    # 1. Normalized -> Capture Image Pixels
    img_x = (norm_x / COORD_MAX) * cap_w
    img_y = (norm_y / COORD_MAX) * cap_h
    
    # 2. Capture Pixels -> Screen Pixels
    # If we are capturing the whole screen, this ratio is 1.0.
    # If capturing a region, we need to add offsets (omitted for now as we assume full monitor capture).
    scale_x = scr_w / cap_w
    scale_y = scr_h / cap_h
    
    final_x = int(img_x * scale_x)
    final_y = int(img_y * scale_y)
    
    # Clamp
    final_x = max(0, min(final_x, scr_w - 1))
    final_y = max(0, min(final_y, scr_h - 1))
    
    return final_x, final_y


def execute(
    action: Action, 
    capture_size: Tuple[int, int],
    dry_run: bool = False
) -> Tuple[str, Optional[Tuple[int, int]]]:
    """
    Execute the action.
    """
    screen_size = pyautogui.size()
    coords = None
    desc = f"Unknown action: {action.action}"

    try:
        if action.action == "click":
            if action.coordinate:
                coords = scale_coords(action.coordinate, capture_size, screen_size)
                desc = f"Click at {coords} (screen)"
                if not dry_run:
                    pyautogui.click(coords[0], coords[1])
            else:
                desc = "Click failed (no coords)"

        elif action.action == "type":
            if action.text:
                safe, reason = is_safe_text(action.text)
                if safe:
                    desc = f"Type '{action.text}'"
                    if not dry_run:
                        pyautogui.write(action.text)
                else:
                    desc = f"Type blocked: {reason}"

        elif action.action == "press":
            if action.key:
                desc = f"Press '{action.key}'"
                # Handle hotkeys
                if "+" in action.key:
                    safe, reason = is_safe_hotkey(action.key)
                    if safe:
                        if not dry_run:
                            parts = action.key.lower().split("+")
                            pyautogui.hotkey(*parts)
                    else:
                        desc = f"Hotkey blocked: {reason}"
                else:
                    if not dry_run:
                        pyautogui.press(action.key)

        elif action.action == "scroll":
            desc = f"Scroll {action.direction}"
            amount = -300 if action.direction == "down" else 300
            if not dry_run:
                pyautogui.scroll(amount)

        elif action.action == "done":
            desc = f"Goal Completed: {action.reason}"

        return desc, coords

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return f"Error: {str(e)}", None