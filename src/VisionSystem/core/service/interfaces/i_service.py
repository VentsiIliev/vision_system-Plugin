from abc import ABC, abstractmethod
from typing import Tuple, Any


class IService(ABC):
    """
    Interface for settings backend.
    Allows VisionSystem to use local or remote storage interchangeably.
    Also abstracts camera calibration and work area data.
    """

    # ---------------- Settings methods ----------------
    @abstractmethod
    def loadSettings(self) -> dict:
        """Load camera/settings from backend"""
        pass

    @abstractmethod
    def updateSettings(self,
                       vision_system,
                       settings: dict,
                       logging_enabled: bool,
                       logger) -> Tuple[bool, str]:
        """Update camera/settings and apply to vision_system"""
        pass

    # ---------------- Calibration / DataManager methods ----------------
    @abstractmethod
    def loadPerspectiveMatrix(self):
        """Load perspective matrix from storage"""
        pass

    @abstractmethod
    def loadCameraCalibrationData(self):
        """Load camera calibration data"""
        pass

    @abstractmethod
    def loadCameraToRobotMatrix(self):
        """Load camera-to-robot homography"""
        pass

    @abstractmethod
    def loadWorkAreaPoints(self):
        """Load pickup, spray, and work area points"""
        pass

    @abstractmethod
    def saveWorkAreaPoints(self, data: Any) -> Tuple[bool, str]:
        """Save work area points"""
        pass

    # ---------------- Convenience properties ----------------
    @property
    @abstractmethod
    def cameraData(self):
        pass

    @property
    @abstractmethod
    def cameraToRobotMatrix(self):
        pass

    @cameraToRobotMatrix.setter
    @abstractmethod
    def cameraToRobotMatrix(self, value):
        pass

    @property
    @abstractmethod
    def perspectiveMatrix(self):
        pass

    @property
    @abstractmethod
    def camera_to_robot_matrix_path(self):
        pass

    @property
    @abstractmethod
    def sprayAreaPoints(self):
        pass

    @abstractmethod
    def get_camera_matrix(self):
        pass

    @abstractmethod
    def get_distortion_coefficients(self):
        pass

    @property
    @abstractmethod
    def isCalibrated(self) -> bool:
        """True if the system has both camera calibration data and camera-to-robot matrix."""
        pass