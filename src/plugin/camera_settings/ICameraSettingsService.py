"""
Unified service interface for camera settings.

Combines camera settings persistence and camera actions in a single service.
"""
from typing import Protocol

from src.plugin.camera_settings.camera_settings_data import CameraSettingsData


class ICameraSettingsService(Protocol):
    """
    Unified service interface for camera settings.

    Combines both settings persistence and camera actions.
    """

    # Settings persistence
    def load_settings(self) -> CameraSettingsData: ...
    def save_settings(self, settings: CameraSettingsData) -> None: ...

    # Camera actions
    def set_raw_mode(self, enabled: bool) -> None: ...
    def capture_image(self) -> None: ...
    def calibrate_camera(self) -> None: ...
    def calibrate_robot(self) -> None: ...
