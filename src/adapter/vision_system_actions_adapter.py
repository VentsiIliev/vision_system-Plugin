"""
Actions adapter: bridges VisionSystem to ICameraActionsService.

Dependency direction: adapter → vision only.
The plugin never imports this class.
"""
from src.VisionSystem.VisionSystem import VisionSystem


class VisionSystemActionsAdapter:
    """
    Implements ICameraActionsService.

    Delegates every camera action directly to VisionSystem without any
    data translation — actions are fire-and-forget side effects.
    """

    def __init__(self, vision_system: VisionSystem):
        self._vs = vision_system

    # ── ICameraActionsService ────────────────────────────────────────────────

    def set_raw_mode(self, enabled: bool) -> None:
        self._vs.rawMode = enabled

    def capture_image(self) -> None:
        print("[VisionSystemActionsAdapter] Capturing calibration image...")
        self._vs.captureCalibrationImage()

    def calibrate_camera(self) -> None:
        print("[VisionSystemActionsAdapter] Starting camera calibration...")
        success, message = self._vs.calibrateCamera()
        print(f"[VisionSystemActionsAdapter] Calibration result: {success} — {message}")

    def calibrate_robot(self) -> None:
        # TODO: wire to robot calibration flow
        print("[VisionSystemActionsAdapter] calibrate_robot — not yet implemented")

