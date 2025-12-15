"""
On-Demand Screen Capture.

Refactored from threaded/polling model to request-response model
to save resources and ensure frame freshness.
"""
from __future__ import annotations

import logging
from typing import Optional, Tuple
import numpy as np
import mss

# DXCam is Windows only
try:
    import DXCam
    HAS_DXCAM = True
except ImportError:
    HAS_DXCAM = False

logger = logging.getLogger(__name__)

class OnDemandCapture:
    """Captures screen frames only when requested."""
    
    def __init__(self, use_dxcam: bool = False, monitor_index: int = 1) -> None:
        self.use_dxcam = use_dxcam and HAS_DXCAM
        self.monitor_index = monitor_index
        self._cam = None
        
        if self.use_dxcam:
            try:
                # Initialize DXCam once
                self._cam = DXCam.create(output_idx=monitor_index-1, output_color="BGR")
                logger.info(f"Initialized DXCam on monitor {monitor_index}")
            except Exception as e:
                logger.error(f"DXCam failed to init, falling back to MSS: {e}")
                self.use_dxcam = False
    
    def capture(self) -> Optional[np.ndarray]:
        """
        Capture a single frame immediately.
        
        Returns:
            np.ndarray: BGR image or None if capture failed.
        """
        if self.use_dxcam and self._cam is not None:
            return self._capture_dxcam()
        return self._capture_mss()
    
    def _capture_dxcam(self) -> Optional[np.ndarray]:
        # DXCam needs a 'grab' call. If the screen hasn't changed, 
        # it might return None depending on settings, but usually it blocks.
        # We use .grab() which is efficient.
        try:
            frame = self._cam.grab()
            if frame is None:
                # If None, it means no change or timeout. 
                # For an agent, we force a frame if possible, but DXCam is quirky.
                # Often it's better to restart or just return None.
                pass
            return frame
        except Exception as e:
            logger.error(f"DXCam capture error: {e}")
            return None

    def _capture_mss(self) -> Optional[np.ndarray]:
        with mss.mss() as sct:
            try:
                monitors = sct.monitors
                if self.monitor_index >= len(monitors):
                    logger.warning(f"Monitor index {self.monitor_index} out of range, using 1")
                    target = monitors[1]
                else:
                    target = monitors[self.monitor_index]
                
                # grab() returns BGRA
                screenshot = sct.grab(target)
                img = np.array(screenshot)
                
                # Convert BGRA to BGR
                return img[:, :, :3]
            except Exception as e:
                logger.error(f"MSS capture error: {e}")
                return None

    def get_resolution(self) -> Tuple[int, int]:
        """Return (width, height) of the capture target."""
        if self.use_dxcam and self._cam:
             # DXCam doesn't easily expose size without capturing, 
             # but we can try capturing one frame.
             frame = self.capture()
             if frame is not None:
                 return frame.shape[1], frame.shape[0]
             return (1920, 1080) # Fallback

        with mss.mss() as sct:
            try:
                monitors = sct.monitors
                target = monitors[min(self.monitor_index, len(monitors)-1)]
                return target["width"], target["height"]
            except:
                return (1920, 1080)

    def release(self):
        if self.use_dxcam and self._cam:
            try:
                self._cam.release()
            except:
                pass