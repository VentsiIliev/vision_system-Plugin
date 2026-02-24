import json
import os
from abc import ABC

from src.VisionSystem.core.settings.CameraSettingKey import CameraSettingKey
from src.VisionSystem.core.logging.custom_logging import log_if_enabled, LoggingLevel
from src.plvision.PLVision.Camera import Camera
from src.VisionSystem.core.service.interfaces.i_service import IService
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config.json') # this is just a default path if not path provided

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
        with open(self.config_file_path, 'w') as f:
            json.dump(settings, f, indent=2)

    def updateSettings(self, vision_system, settings: dict,logging_enabled:bool,logger) -> tuple[bool, str]:
        """
        Updates the camera settings using the CameraSettings object.
        """

        current_index = vision_system.camera_settings.get_camera_index()
        current_width = vision_system.camera_settings.get_camera_width()
        current_height = vision_system.camera_settings.get_camera_height()

        try:
            # Update the camera_settings object
            success, message = vision_system.camera_settings.updateSettings(settings)

            if not success:
                return False, message

            # Update the brightness controller with new PID values
            # Access through brightnessManager, not directly
            vision_system.brightnessManager.brightnessController.Kp = vision_system.camera_settings.get_brightness_kp()
            vision_system.brightnessManager.brightnessController.Ki = vision_system.camera_settings.get_brightness_ki()
            vision_system.brightnessManager.brightnessController.Kd = vision_system.camera_settings.get_brightness_kd()
            vision_system.brightnessManager.brightnessController.target = vision_system.camera_settings.get_target_brightness()

            log_if_enabled(enabled=logging_enabled,
                           logger=logger,
                           level=LoggingLevel.INFO,
                           message=f"Updated brightness controller - Kp: {vision_system.camera_settings.get_brightness_kp()}, "
                                  f"Ki: {vision_system.camera_settings.get_brightness_ki()}, "
                                  f"Kd: {vision_system.camera_settings.get_brightness_kd()}, "
                                  f"Target: {vision_system.camera_settings.get_target_brightness()}",
                           broadcast_to_ui=False)

            # Update camera resolution if changed
            if (CameraSettingKey.WIDTH.value in settings or
                    CameraSettingKey.HEIGHT.value in settings or
                    CameraSettingKey.INDEX.value in settings):
                # Reinitialize camera with new settings

                if (current_index != vision_system.camera_settings.get_camera_index() or
                        current_width != vision_system.camera_settings.get_camera_width() or
                        current_height != vision_system.camera_settings.get_camera_height()):
                    vision_system.camera = Camera(
                        vision_system.camera_settings.get_camera_width(),
                        vision_system.camera_settings.get_camera_height()
                    )

            log_if_enabled(enabled=logging_enabled,
                           logger=logger,
                           level=LoggingLevel.INFO,
                           message=f"Settings updated successfully",
                           broadcast_to_ui=False)
            return True, "Settings updated successfully"

        except Exception as e:
            return False, f"Error updating settings: {str(e)}"