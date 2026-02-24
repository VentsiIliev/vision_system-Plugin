import sys
import threading
import time

import cv2
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow

from external_dependencies.MessageBroker import MessageBroker
from src.VisionSystem.VisionSystem import VisionSystem
from src.VisionSystem.core.external_communication.system_state_management import VisionTopics
from src.gui.camera_settings import ICameraSettingsService, CameraSettingsPlugin
from src.gui.camera_settings.camera_settings_data import CameraSettingsData


class FrameBridge:
    """
    Vision thread writes latest frame to _slot (old frames discarded).
    QTimer on main thread polls _slot at fixed fps and updates the label.
    Supports switching between 'live' and 'threshold' topics.
    """

    def __init__(self, preview_label, fps: int = 60):
        self._label = preview_label
        self._live_slot: np.ndarray | None = None
        self._thresh_slot: np.ndarray | None = None
        self._mode: str = "live"
        self._lock = threading.Lock()

        self._timer = QTimer()
        self._timer.timeout.connect(self._display)
        self._timer.start(1000 // fps)

    def set_mode(self, mode: str) -> None:
        """Switch between 'live' and 'threshold'. Called from main thread."""
        self._mode = mode

    def on_live_frame(self, message: dict) -> None:
        image = message.get("image") if isinstance(message, dict) else message
        if image is None:
            return
        frame = np.ascontiguousarray(image)
        with self._lock:
            self._live_slot = frame

    def on_threshold_frame(self, message) -> None:
        # threshold image is published as a raw numpy array (grayscale)
        image = message.get("image") if isinstance(message, dict) else message
        if image is None:
            return
        frame = np.ascontiguousarray(image)
        # convert grayscale to BGR so QImage format stays consistent
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        with self._lock:
            self._thresh_slot = frame

    def _display(self) -> None:
        with self._lock:
            frame = self._thresh_slot if self._mode == "threshold" else self._live_slot
            if self._mode == "threshold":
                self._thresh_slot = None
            else:
                self._live_slot = None
        if frame is None or self._label is None:
            return
        h, w, ch = frame.shape
        qt_image = QImage(frame.tobytes(), w, h, ch * w, QImage.Format.Format_BGR888)
        self._label.set_frame(QPixmap.fromImage(qt_image))


class FakeCameraSettingsService(ICameraSettingsService):
    """THIS WILL ADAPT THE VISON SYSTEM SERVICE TO THE PLUGINS EXPECTED INTERFACE FOR NOW"""

    def __init__(self, v_system: VisionSystem):
        self.v_system = v_system

    def load_settings(self) -> CameraSettingsData:
        settings = self.v_system.service.loadSettings()
        # print type of settings
        print(type(settings))
        return settings

    def save_settings(self, settings) -> None:
        settings_dict = settings.to_dict()
        self.v_system.service.saveSettings(settings_dict)
        self.v_system.service.updateSettings(self.v_system, settings_dict, logging_enabled=False, logger=None)

    # Camera actions
    def set_raw_mode(self, enabled: bool) -> None:
        print(f"[service] Raw mode: {'ON' if enabled else 'OFF'}")

    def capture_image(self) -> None:
        print(f"[service] Capturing image...")
        return self.v_system.captureImage()

    def calibrate_camera(self) -> None:
        print(f"[service] Starting camera calibration...")

    def calibrate_robot(self) -> None:
        print(f"[service] Starting robot calibration...")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    broker = MessageBroker()
    vs = VisionSystem(message_broker=broker)
    vs.start_system()


    plugin = CameraSettingsPlugin(service=FakeCameraSettingsService(v_system=vs))
    plugin.load()

    # Wire camera feed: vision thread → FrameBridge → main thread → preview label
    bridge = FrameBridge(preview_label=plugin.preview_label)
    broker.subscribe(VisionTopics.LATEST_IMAGE, bridge.on_live_frame)
    broker.subscribe(VisionTopics.THRESHOLD_IMAGE, bridge.on_threshold_frame)

    # Wire the threshold view toggle from the controls widget
    plugin.widget.controls.view_mode_changed.connect(bridge.set_mode)

    win = QMainWindow()
    win.setWindowTitle("Camera Settings")
    win.resize(1280, 1024)
    win.setCentralWidget(plugin.widget)
    win.show()

    app.aboutToQuit.connect(vs.stop_system)
    sys.exit(app.exec())
