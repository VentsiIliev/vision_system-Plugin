import json
import os
import tempfile
from typing import Callable

from src.VisionSystem.core.settings.CameraSettingKey import CameraSettingKey
from src.VisionSystem.core.logging.custom_logging import log_if_enabled, LoggingLevel

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

class SettingsManager:

    def __init__(self, config_file_path: str | None = None):
        self.config_file_path = config_file_path or CONFIG_FILE_PATH

    def loadSettings(self):
        if not os.path.exists(self.config_file_path):
            print(f"Settings file not found at {self.config_file_path} returning empty dict")
            # If file doesn't exist → return empty dict
            return {}
        print(f"[SettingsManager] Loading settings from {self.config_file_path}")
        with open(self.config_file_path) as f:
            return json.load(f)

    def saveSettings(self, settings: dict) -> None:
        dir_name = os.path.dirname(self.config_file_path)
        os.makedirs(dir_name, exist_ok=True)
        # Write to a temp file in the same directory, then atomically replace.
        # This prevents a crash mid-write from corrupting the JSON file.
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(settings, f, indent=2)
            os.replace(tmp_path, self.config_file_path)
        except Exception:
            os.unlink(tmp_path)
            raise

    def updateSettings(
        self,
        camera_settings,
        settings: dict,
        logging_enabled: bool,
        logger,
        brightness_controller=None,
        reinit_camera: Callable[[int, int], None] | None = None,
    ) -> tuple[bool, str]:
        """
        Apply *settings* dict to *camera_settings* and propagate side-effects.

        Parameters
        ----------
        camera_settings : CameraSettings
            The live settings object to update.
        settings : dict
            Nested dict in the camera_settings.json format.
        logging_enabled : bool
        logger :
            Logger instance (or None).
        brightness_controller :
            The PID controller whose Kp/Ki/Kd/target must stay in sync.
            Optional — pass None to skip brightness sync.
        reinit_camera : Callable[[width, height], None] | None
            Called when index/width/height change so the caller can
            swap the Camera instance.  Optional — pass None to skip.
        """
        current_index  = camera_settings.get_camera_index()
        current_width  = camera_settings.get_camera_width()
        current_height = camera_settings.get_camera_height()

        try:
            success, message = camera_settings.updateSettings(settings)
            if not success:
                return False, message

            # ── Brightness controller sync ──────────────────────────────
            if brightness_controller is not None:
                brightness_controller.Kp     = camera_settings.get_brightness_kp()
                brightness_controller.Ki     = camera_settings.get_brightness_ki()
                brightness_controller.Kd     = camera_settings.get_brightness_kd()
                brightness_controller.target = camera_settings.get_target_brightness()

                log_if_enabled(
                    enabled=logging_enabled, logger=logger, level=LoggingLevel.INFO,
                    message=(
                        f"Updated brightness controller — "
                        f"Kp: {camera_settings.get_brightness_kp()}, "
                        f"Ki: {camera_settings.get_brightness_ki()}, "
                        f"Kd: {camera_settings.get_brightness_kd()}, "
                        f"Target: {camera_settings.get_target_brightness()}"
                    ),
                    broadcast_to_ui=False,
                )

            # ── Camera reinitialization ─────────────────────────────────
            resolution_keys = {
                CameraSettingKey.WIDTH.value,
                CameraSettingKey.HEIGHT.value,
                CameraSettingKey.INDEX.value,
            }
            if reinit_camera is not None and resolution_keys & settings.keys():
                new_index  = camera_settings.get_camera_index()
                new_width  = camera_settings.get_camera_width()
                new_height = camera_settings.get_camera_height()
                if (new_index != current_index or
                        new_width != current_width or
                        new_height != current_height):
                    reinit_camera(new_width, new_height)

            log_if_enabled(
                enabled=logging_enabled, logger=logger, level=LoggingLevel.INFO,
                message="Settings updated successfully",
                broadcast_to_ui=False,
            )
            return True, "Settings updated successfully"

        except Exception as e:
            return False, f"Error updating settings: {str(e)}"