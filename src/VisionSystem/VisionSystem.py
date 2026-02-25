import threading


import cv2

from src.VisionSystem.core.camera.frame_grabber import FrameGrabber
from src.VisionSystem.core.path_resolver import get_path_resolver

from src.VisionSystem.core.external_communication.system_state_management import StateManager, \
    ServiceState, MessagePublisher, SubscriptionManager

from src.VisionSystem.core.logging.custom_logging import setup_logger, LoggerContext, log_debug_message, \
    log_info_message
from src.VisionSystem.core.logging.timing_logger import timing_logger
from src.VisionSystem.core.service.internal_service import Service

# Vision System core modules
from src.VisionSystem.features.brigthtness_control.brightness_manager import BrightnessManager
from src.plvision.PLVision.Camera import Camera
from .camera_initialization import CameraInitializer



from src.VisionSystem.features.qr_scanner.QRcodeScanner import detect_and_decode_barcode

# Vision System handlers
from .handlers.aruco_detection_handler import detect_aruco_markers
from .handlers.camera_calibration_handler import (
    calibrate_camera,
    capture_calibration_image
)
from .handlers.contour_detection_handler import handle_contour_detection

# External or domain-specific image processing
from src.plvision.PLVision import ImageProcessing

# Conditional logging import


ENABLE_LOGGING = True  # Enable or disable logging
vision_system_logger = setup_logger("VisionSystem") if ENABLE_LOGGING else None

# Base storage folder - use path resolver for consistent path resolution
DEFAULT_STORAGE_PATH = str(get_path_resolver().vision_system_root / 'storage')


class VisionSystem:
    def __init__(self,
                 storage_path=None,
                 message_broker=None,
                 service=None):

        self.optimal_camera_matrix = None
        self.logger_context = LoggerContext(ENABLE_LOGGING, vision_system_logger)

        if storage_path is None:
            self.storage_path = DEFAULT_STORAGE_PATH
        else:
            self.storage_path = storage_path
        log_debug_message(self.logger_context,
                          message=f"VisionSystem initialized with storage path: {self.storage_path}")

        if service is None:
            self.service = Service(ENABLE_LOGGING, vision_system_logger, data_storage_path=self.storage_path)
        else:
            self.service = service

        self.message_broker = message_broker



        self.service_id = "vision_system"

        # only initialize the publisher if the message broker provided
        self.camera_settings = self.service.loadSettings()
        self.setup_camera()
        self.load_calibration_data()

        self.brightnessManager = BrightnessManager(self)

        if self.message_broker is not None:
            self.setup_external_communication()

        self.threshold_by_area = "spray"
        self.calibrationImages = []

        # Extract camera matrix and distortion coefficients
        if self.service.isCalibrated:
            self.cameraMatrix = self.service.get_camera_matrix()
            self.cameraDist = self.service.get_distortion_coefficients()

        # Initialize image variables
        self.image = None
        self.rawImage = None
        self.correctedImage = None
        self.rawMode = False

        # Initialize skip frames counter
        self.current_skip_frames = 0
        self.frame_grabber = FrameGrabber(self.camera, maxlen=5)
        self.frame_grabber.start()

    def setup_external_communication(self):
        self.message_publisher = MessagePublisher()

        self.state_manager = StateManager(
            service_id=self.service_id,
            initial_state=ServiceState.INITIALIZING,
            message_publisher=self.message_publisher
        )

        self.subscription_manager = SubscriptionManager(self, self.message_broker).subscribe_all()

    def setup_camera(self):
        # print the type of camera_settings
        print(type(self.camera_settings))
        camera_index = self.camera_settings.get_camera_index()
        camera_initializer = CameraInitializer(log_enabled=ENABLE_LOGGING,
                                               logger=vision_system_logger,
                                               width=self.camera_settings.get_camera_width(),
                                               height=self.camera_settings.get_camera_height())

        self.camera, camera_index = camera_initializer.initializeCameraWithRetry(camera_index)
        # VIDEO_URL = 'http://192.168.222.178:5000/video_feed'  # replace with server IP if remote
        # self.camera = Camera(device=VIDEO_URL, width=1280, height=720, fps=30,backend="ANY") # Use RemoteCamera for MJPEG stream
        self.camera.set_auto_exposure(True)
        self.camera_settings.set_camera_index(camera_index)

    def load_calibration_data(self):
        self.service.loadPerspectiveMatrix()
        self.service.loadCameraCalibrationData()
        self.service.loadCameraToRobotMatrix()
        self.service.loadWorkAreaPoints()

    @property
    def camera_to_robot_matrix_path(self):
        return self.service.camera_to_robot_matrix_path

    @property
    def cameraToRobotMatrix(self):
        return self.service.cameraToRobotMatrix



    # Setter
    @cameraToRobotMatrix.setter
    def cameraToRobotMatrix(self, value):
        self.service.cameraToRobotMatrix = value
        # Update system calibration state locally


    @property
    def perspectiveMatrix(self):
        return self.service.perspectiveMatrix

    @property
    def stateTopic(self):
        return self.message_publisher.stateTopic

    def captureCalibrationImage(self):
        return capture_calibration_image(vision_system=self,
                                         log_enabled=ENABLE_LOGGING,
                                         logger=vision_system_logger)

    # @timing_logger(log_memory_cpu=False)
    def run(self):
        def log_func(msg):
            log_info_message(self.logger_context, message=msg)

        self.image = self.frame_grabber.get_latest()

        # Handle frame skipping
        if self.current_skip_frames < self.camera_settings.get_skip_frames():
            self.current_skip_frames += 1
            return None, None, None

        if self.image is None:
            return None, None, None

        if self.message_broker is not None:
            self.state_manager.update_state(ServiceState.IDLE)

        self.rawImage = self.image.copy()

        if self.camera_settings.get_brightness_auto():
            self.brightnessManager.adjust_brightness()

        if self.rawMode:
            return None, self.rawImage, None

        if self.camera_settings.get_contour_detection():
            result = handle_contour_detection(self)
            return result

        if not self.service.isCalibrated:
            self.message_publisher.publish_latest_image(self.image)
            return None, self.image, None

        self.correctedImage = self.correctImage(self.image)

        return None, self.correctedImage, None

    def correctImage(self, imageParam):
        """
        Undistorts and applies perspective correction to the given image.
        """
        # First, undistort the image using camera calibration parameters
        if self.optimal_camera_matrix is None:
            self.optimal_camera_matrix, self.roi = cv2.getOptimalNewCameraMatrix(self.cameraMatrix, self.cameraDist,
                                                                                 (self.camera_settings.get_camera_width(),
                                                                                  self.camera_settings.get_camera_height(),),
                                                                                 0.5,
                                                                                 (self.camera_settings.get_camera_width(),
                                                                                  self.camera_settings.get_camera_height(),))
        imageParam = ImageProcessing.undistortImage(
            imageParam,
            self.cameraMatrix,
            self.cameraDist,
            self.camera_settings.get_camera_width(),
            self.camera_settings.get_camera_height(),
            crop=False,
            optimal_camera_matrix=self.optimal_camera_matrix,
            roi=self.roi
        )

        # Apply perspective transformation if available (only for single-image calibrations with ArUco markers)
        if self.perspectiveMatrix is not None:
            imageParam = cv2.warpPerspective(
                imageParam,
                self.perspectiveMatrix,
                (self.camera_settings.get_camera_width(), self.camera_settings.get_camera_height())
            )

        return imageParam

    def on_threshold_update(self, message):
        # message format {"region": "pickup"})
        area = message.get("region", "")
        self.threshold_by_area = area

    def get_thresh_by_area(self, area):
        if area == "pickup":
            return self.camera_settings.get_threshold_pickup_area()
        elif area == "spray":
            return self.camera_settings.get_threshold()
        else:
            raise ValueError("Invalid region for threshold update")

    def calibrateCamera(self):
        return calibrate_camera(vision_system=self,
                                log_enabled=ENABLE_LOGGING,
                                logger=vision_system_logger,
                                storage_path=self.storage_path)

    def captureImage(self):
        """
        Capture and return the corrected image.
        """
        return self.correctedImage

    def updateSettings(self, settings: dict):
        def reinit_camera(width: int, height: int) -> None:
            self.camera = Camera(width, height)

        return self.service.updateSettings(
            camera_settings=self.camera_settings,
            settings=settings,
            logging_enabled=ENABLE_LOGGING,
            logger=vision_system_logger,
            brightness_controller=self.brightnessManager.brightnessController,
            reinit_camera=reinit_camera,
        )

    def saveWorkAreaPoints(self, data):
        return self.service.saveWorkAreaPoints(data)

    def getWorkAreaPoints(self, area_type):
        """Get work area points for the specified area type"""
        if not area_type:
            return False, "Area type is required", None

        if area_type not in ['pickup', 'spray', 'work']:
            return False, f"Invalid area_type: {area_type}. Must be 'pickup', 'spray', or 'work'", None

        try:
            if area_type == 'pickup':
                points = self.service.pickupAreaPoints
                print(f"[VisionSystem.getWorkAreaPoints] pickup points type: {type(points)}, value: {points}")
            elif area_type == 'spray':
                points = self.service.sprayAreaPoints
                print(f"[VisionSystem.getWorkAreaPoints] spray points type: {type(points)}, value: {points}")
            else:  # work (legacy)
                points = self.service.workAreaPoints
                print(f"[VisionSystem.getWorkAreaPoints] work points type: {type(points)}, value: {points}")

            if points is not None:
                # Convert a numpy array to a list for JSON serialization
                points_list = points.tolist() if hasattr(points, 'tolist') else points
                print(f"[VisionSystem.getWorkAreaPoints] Returning points for {area_type}: {points_list}")
                return True, f"Work area points retrieved successfully for {area_type} area", points_list
            else:
                print(f"[VisionSystem.getWorkAreaPoints] No points found for {area_type} area")
                return True, f"No saved points found for {area_type} area", None

        except Exception as e:
            print(f"[VisionSystem.getWorkAreaPoints] Error loading {area_type} area points: {str(e)}")
            return False, f"Error loading {area_type} area points: {str(e)}", None


    def detectArucoMarkers(self, flip=False, image=None):
        return detect_aruco_markers(vision_system=self,
                                    log_enabled=ENABLE_LOGGING,
                                    logger=vision_system_logger,
                                    flip=flip,
                                    image=image)

    def detectQrCode(self):
        """
        Detect and decode QR codes in the raw image.
        """
        data = detect_and_decode_barcode(self.rawImage)
        return data

    def get_camera_settings(self):
        """
        Get the current camera settings object.
        """
        return self.camera_settings


    """PRIVATE METHODS SECTION"""

    @perspectiveMatrix.setter
    def perspectiveMatrix(self, value):
        self._perspectiveMatrix = value

    def start_system(self):
        self.stop_signal = False
        def _loop():
            while not self.stop_signal:
                self.run()

        self.cameraThread = threading.Thread(target=_loop, daemon=True)
        self.cameraThread.start()


    def stop_system(self):
        print(f"Stopping Vision System...")
        self.stop_signal = True
        self.camera.stop_stream()
        self.camera.stopCapture()
        self.cameraThread.join()

if __name__ == "__main__":
    vs = VisionSystem()
    while True:
        _, img, _ = vs.run()
        if img is not None:
            cv2.imshow("Vision System", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()
