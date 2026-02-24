"""
FrameBridge: routes frames from the vision thread to a Qt preview label.

Vision thread writes latest frame into a slot (old frames are silently
discarded).  A QTimer on the main thread polls the slot at a fixed fps
and updates the label — keeping OpenCV and Qt on the correct threads.

Supports switching between 'live' and 'threshold' topics at runtime.
"""
import threading

import cv2
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap


class FrameBridge:
    """Thread-safe bridge between vision worker frames and a Qt preview label."""

    def __init__(self, preview_label, fps: int = 60):
        self._label = preview_label
        self._live_slot: np.ndarray | None = None
        self._thresh_slot: np.ndarray | None = None
        self._mode: str = "live"
        self._lock = threading.Lock()

        self._timer = QTimer()
        self._timer.timeout.connect(self._display)
        self._timer.start(1000 // fps)

    # ── Public API ───────────────────────────────────────────────────────────

    def set_mode(self, mode: str) -> None:
        """Switch between 'live' and 'threshold'. Safe to call from main thread."""
        self._mode = mode

    def on_live_frame(self, message) -> None:
        """Subscriber callback for VisionTopics.LATEST_IMAGE."""
        image = message.get("image") if isinstance(message, dict) else message
        if image is None:
            return
        with self._lock:
            self._live_slot = np.ascontiguousarray(image)

    def on_threshold_frame(self, message) -> None:
        """Subscriber callback for VisionTopics.THRESHOLD_IMAGE."""
        image = message.get("image") if isinstance(message, dict) else message
        if image is None:
            return
        frame = np.ascontiguousarray(image)
        if frame.ndim == 2:                              # grayscale → BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        with self._lock:
            self._thresh_slot = frame

    # ── Private ──────────────────────────────────────────────────────────────

    def _display(self) -> None:
        with self._lock:
            if self._mode == "threshold":
                frame, self._thresh_slot = self._thresh_slot, None
            else:
                frame, self._live_slot = self._live_slot, None

        if frame is None or self._label is None:
            return

        h, w, ch = frame.shape
        qt_image = QImage(frame.tobytes(), w, h, ch * w, QImage.Format.Format_BGR888)
        self._label.set_frame(QPixmap.fromImage(qt_image))

