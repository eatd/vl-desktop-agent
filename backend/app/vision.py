"""
Screen capture using DXCam (Windows) or MSS (cross-platform).
"""
from __future__ import annotations

import threading
from typing import Optional

import mss
import numpy as np

# TODO: Make this configurable
try:
    import DXCam
    HAS_DXCAM = True
except ImportError:
    HAS_DXCAM = False


class ContinuousCapture:
    """Background thread that captures screenshots."""
    
    def __init__(
        self,
        use_dxcam: bool = False,
        monitor_index: int = 1,
        fps: float = 5.0,
    ) -> None:
        self._lock = threading.Lock()
        self._latest: Optional[np.ndarray] = None
        self._stop = threading.Event()
        self._interval = 1.0 / fps if fps > 0 else 0.1
        self._monitor_index = monitor_index
        
        # Initialize backend
        # 
        if use_dxcam and HAS_DXCAM:
            self._cam = DXCam.create(output_idx=0, output_color="BGR") 
            self._use_dxcam = True
        else:
            self._cam = None
            self._use_dxcam = False
        
        # Start thread
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def get_latest(self) -> Optional[np.ndarray]:
        """Get most recent frame."""
        with self._lock:
            return self._latest.copy() if self._latest is not None else None
    
    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
    
    def _run(self) -> None:
        if self._use_dxcam:
            self._dxcam_loop()
        else:
            self._mss_loop()
    
    def _dxcam_loop(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self._cam.grab()
                if frame is not None:
                    with self._lock:
                        self._latest = frame
            except Exception:
                pass
            self._stop.wait(self._interval)
        
        try:
            self._cam.release()
        except Exception:
            pass
    
    def _mss_loop(self) -> None:
        with mss.mss() as sct:
            monitors = sct.monitors
            monitor = monitors[min(self._monitor_index, len(monitors) - 1)]
            
            while not self._stop.is_set():
                try:
                    img = sct.grab(monitor)
                    
                    frame = np.asarray(img)[:, :, :3]  # BGRA → BGR 
                    frame = np.ascontiguousarray(frame)
                    
                    with self._lock:
                        self._latest = frame
                except Exception:
                    pass
                
                self._stop.wait(self._interval)
