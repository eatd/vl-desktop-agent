"""
Grid overlay for improved coordinate accuracy.

Adds a labeled 10×10 grid to screenshots so the model can reference
coordinates like "D3" instead of absolute pixels.
"""
from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


# Grid configuration
GRID_ROWS = 10
GRID_COLS = 10
GRID_COLOR = (0, 255, 255)  # Yellow
GRID_ALPHA = 0.3
LABEL_COLOR = (0, 0, 0)  # Black text
BG_COLOR = (0, 255, 255)  # Yellow background


def cell_to_pixels(
    cell: str, 
    image_size: Tuple[int, int]
) -> Tuple[int, int]:
    """
    Convert grid cell like "D3" to pixel coordinates (center of cell).
    
    Columns: A-J (0-9)
    Rows: 1-10 (0-9 internally)
    """
    if len(cell) < 2:
        raise ValueError(f"Invalid cell: {cell}")
    
    col_char = cell[0].upper()
    row_str = cell[1:]
    
    col = ord(col_char) - ord('A')
    row = int(row_str) - 1
    
    if not (0 <= col < GRID_COLS and 0 <= row < GRID_ROWS):
        raise ValueError(f"Cell out of range: {cell}")
    
    width, height = image_size
    cell_w = width // GRID_COLS
    cell_h = height // GRID_ROWS
    
    # Return center of cell
    x = col * cell_w + cell_w // 2
    y = row * cell_h + cell_h // 2
    
    return x, y


def pixels_to_cell(
    x: int, y: int,
    image_size: Tuple[int, int]
) -> str:
    """Convert pixel coordinates to grid cell like "D3"."""
    width, height = image_size
    
    col = min(x * GRID_COLS // width, GRID_COLS - 1)
    row = min(y * GRID_ROWS // height, GRID_ROWS - 1)
    
    col_char = chr(ord('A') + col)
    row_num = row + 1
    
    return f"{col_char}{row_num}"


def overlay_grid(image: np.ndarray) -> np.ndarray:
    """
    Overlay a labeled 10x10 grid on the image.
    
    Returns a new image with grid lines and cell labels.
    """
    result = image.copy()
    h, w = image.shape[:2]
    
    cell_w = w // GRID_COLS
    cell_h = h // GRID_ROWS
    
    # Draw grid lines
    overlay = result.copy()
    
    for i in range(1, GRID_COLS):
        x = i * cell_w
        cv2.line(overlay, (x, 0), (x, h), GRID_COLOR, 1)
    
    for i in range(1, GRID_ROWS):
        y = i * cell_h
        cv2.line(overlay, (0, y), (w, y), GRID_COLOR, 1)
    
    # Blend grid
    cv2.addWeighted(overlay, GRID_ALPHA, result, 1 - GRID_ALPHA, 0, result)
    
    # Add corner labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    thickness = 1
    
    # Column headers (A-J)
    for col in range(GRID_COLS):
        label = chr(ord('A') + col)
        x = col * cell_w + cell_w // 2 - 5
        y = 15
        
        # Background
        cv2.rectangle(result, (x-2, y-12), (x+12, y+2), BG_COLOR, -1)
        cv2.putText(result, label, (x, y), font, font_scale, LABEL_COLOR, thickness)
    
    # Row numbers (1-10)
    for row in range(GRID_ROWS):
        label = str(row + 1)
        x = 3
        y = row * cell_h + cell_h // 2 + 5
        
        # Background
        cv2.rectangle(result, (x-2, y-12), (x+15, y+2), BG_COLOR, -1)
        cv2.putText(result, label, (x, y), font, font_scale, LABEL_COLOR, thickness)
    
    return result
