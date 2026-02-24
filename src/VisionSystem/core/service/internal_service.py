from typing import Tuple

from src.VisionSystem.core.data_loading import DataManager
from src.VisionSystem.core.logging.custom_logging import log_info_message, LoggerContext
from src.VisionSystem.core.service.interfaces.i_service import IService
from src.VisionSystem.core.settings.CameraSettings import CameraSettings
from src.VisionSystem.core.settings.settings_manager import SettingsManager
from src.VisionSystem.core.path_resolver import get_user_config_path

class Service(IService):

    def __init__(self, logging_enabled, logger, data_storage_path):
        self.data_manager = DataManager(logging_enabled, logger, data_storage_path)
        self.settings_manager = SettingsManager(config_file_path=str(get_user_config_path()))

    # ---------------- Settings interface ----------------
    def loadSettings(self):
        settings = self.settings_manager.loadSettings()
        print(f"[SettingsManager] settings type in loadSettings")
        print(type(settings))
        default_settings = CameraSettings()
        CameraSettings.from_dict(default_settings,settings)
        settings = default_settings
        print(f"[SettingsManager] after from dict {type(settings)} {settings}")
        return settings

    def updateSettings(self, vision_system, settings: dict, logging_enabled: bool, logger) -> Tuple[bool, str]:
        return self.settings_manager.updateSettings(vision_system, settings, logging_enabled, logger)

    def saveSettings(self, settings: dict) -> None:
        self.settings_manager.saveSettings(settings)

    # ---------------- DataManager interface ----------------
    def loadPerspectiveMatrix(self):
        self.data_manager.loadPerspectiveMatrix()

    def loadCameraCalibrationData(self):
        self.data_manager.loadCameraCalibrationData()

    def loadCameraToRobotMatrix(self):
        self.data_manager.loadCameraToRobotMatrix()

    def loadWorkAreaPoints(self):
        self.data_manager.loadWorkAreaPoints()

    def saveWorkAreaPoints(self, data):
        return self.data_manager.saveWorkAreaPoints(data)

    # ---------------- Convenience properties ----------------
    @property
    def cameraData(self):
        return self.data_manager.cameraData

    @property
    def camera_to_robot_matrix_path(self):
        return self.data_manager.camera_to_robot_matrix_path

    @property
    def cameraToRobotMatrix(self):
        return self.data_manager.cameraToRobotMatrix

    @cameraToRobotMatrix.setter
    def cameraToRobotMatrix(self, value):
        """
        Setter for cameraToRobotMatrix.
        Updates DataManager internally and marks system as calibrated if valid.
        """
        self.data_manager.cameraToRobotMatrix = value
        log_info_message(
            LoggerContext(self.data_manager.ENABLE_LOGGING, self.data_manager.logger),
            message="cameraToRobotMatrix updated in Service"
        )

    @property
    def perspectiveMatrix(self):
        return self.data_manager.perspectiveMatrix

    @property
    def sprayAreaPoints(self):
        return self.data_manager.sprayAreaPoints

    def get_camera_matrix(self):
        return self.data_manager.get_camera_matrix()

    def get_distortion_coefficients(self):
        return self.data_manager.get_distortion_coefficients()

    @property
    def isCalibrated(self) -> bool:
        return (
            self.data_manager.cameraData is not None and
            self.data_manager.cameraToRobotMatrix is not None
        )