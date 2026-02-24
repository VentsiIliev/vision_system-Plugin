import threading
from dataclasses import dataclass
from enum import Enum

from external_dependencies.MessageBroker import MessageBroker




class VisionTopics:
    """Vision system and camera topics"""

    # Vision service state
    SERVICE_STATE = "vision-service/state"
    LATEST_IMAGE = "vision-system/latest-image"
    FPS = "vision-system/fps"
    CALIBRATION_IMAGE_CAPTURED = "vision-system/calibration-image-captured"
    # Camera and image processing
    BRIGHTNESS_REGION = "vision-system/brightness-region"
    THRESHOLD_REGION = "vision-system/threshold"
    CALIBRATION_FEEDBACK = "vision-system/calibration-feedback"
    THRESHOLD_IMAGE = "vision-system/threshold-image"
    AUTO_BRIGHTNESS = "vision-system/auto-brightness"
    AUTO_BRIGHTNESS_START = "vison-auto-brightness"
    AUTO_BRIGHTNESS_STOP = "vison-auto-brightness"
    TRANSFORM_TO_CAMERA_POINT = "vision-system/transform-to-camera-point"

class SubscriptionManager:

    def __init__(self, vision_system,broker):
        self.vision_system = vision_system
        self.broker = broker
        self.subscriptions = {}

    def subscribe_to_threshold_update(self):
        self.broker.subscribe(VisionTopics.THRESHOLD_REGION, self.vision_system.on_threshold_update)
        self.subscriptions[VisionTopics.THRESHOLD_REGION] = self.vision_system.on_threshold_update

    def subscribe_to_auto_brightness_toggle(self):
        # self.broker.subscribe(VisionTopics.BRIGHTNESS_REGION, self.vision_system.brightnessManager.on_brightness_toggle)
        self.subscriptions[VisionTopics.AUTO_BRIGHTNESS] = self.vision_system.brightnessManager.on_brighteness_toggle

    def subscribe_all(self):
        self.subscribe_to_threshold_update()
        self.subscribe_to_auto_brightness_toggle()


class MessagePublisher:
    def __init__(self):
        self.broker= MessageBroker()
        self.latest_image_topic = VisionTopics.LATEST_IMAGE
        self.calibration_image_captured_topic = VisionTopics.CALIBRATION_IMAGE_CAPTURED
        self.thresh_image_topic = VisionTopics.THRESHOLD_IMAGE
        self.stateTopic = VisionTopics.SERVICE_STATE
        self.topic = VisionTopics.CALIBRATION_FEEDBACK

    def publish_latest_image(self,image):
        self.broker.publish(self.latest_image_topic, {"image": image})

    def publish_calibration_image_captured(self,calibration_images):
        self.broker.publish(self.calibration_image_captured_topic, calibration_images)

    def publish_thresh_image(self,thresh_image):
        self.broker.publish(self.thresh_image_topic, thresh_image)

    def publish_state(self,state):
        print(f"[VisionMessagePublisher] Publishing vision service state on topic {self.stateTopic}:", state)
        self.broker.publish(self.stateTopic, state)

    def publish_calibration_feedback(self,feedback):
        self.broker.publish(self.topic, feedback)
# ==========================================================
# Service State (also used as System State)
# Higher numeric value = higher priority
# ==========================================================

class ServiceState(Enum):
    UNKNOWN = 0
    INITIALIZING = 1
    IDLE = 2
    STARTED = 3
    PAUSED = 4
    STOPPED = 5
    ERROR = 6


# ==========================================================
# Message Model
# ==========================================================

@dataclass
class ServiceStateMessage:
    id: str
    state: ServiceState

    def to_dict(self):
        return {
            "id": self.id,
            "state": self.state.name
        }

# ==========================================================
# Service State Manager (per service)
# ==========================================================

class StateManager:
    """
    Used inside individual services.
    Publishes service state changes.
    """

    def __init__(self,
                 service_id: str,
                 initial_state: ServiceState,
                 message_publisher):

        self.service_id = service_id
        self.state = initial_state
        self.message_publisher = message_publisher
        self._lock = threading.Lock()

    # ------------------------------------------------------

    def update_state(self, new_state: ServiceState):
        with self._lock:
            if self.state == new_state:
                return

            self.state = new_state
            self._publish_state()

    # ------------------------------------------------------

    def _publish_state(self):
        message = ServiceStateMessage(
            id=self.service_id,
            state=self.state
        ).to_dict()

        self.message_publisher.publish_state(message)