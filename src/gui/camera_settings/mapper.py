from __future__ import annotations

from copy import deepcopy
from typing import List, Tuple

from src.VisionSystem.core.settings.CameraSettings import CameraSettings
from src.gui.camera_settings.camera_settings_data import CameraSettingsData


class CameraSettingsMapper:
    """Converts between CameraSettingsData, flat dict (SettingsView), and JSON (repo)."""

    # ── flat dict ↔ SettingsView ───────────────────────────────────────────────

    @staticmethod
    def to_flat_dict(data: CameraSettings) -> dict:
        """All schema fields as a flat dict — brightness_area_points excluded."""
        return {
            "index":                   data.get_camera_index(),
            "width":                   data.get_camera_width(),
            "height":                  data.get_camera_height(),
            "skip_frames":             data.get_skip_frames(),
            # "capture_position_offset": data.get_capture_position_offset(),
            "contour_detection":       data.get_contour_detection(),
            "draw_contours":           data.get_draw_contours(),
            "threshold":               data.get_threshold(),
            "threshold_pickup_area":   data.get_threshold_pickup_area(),
            "epsilon":                 data.get_epsilon(),
            "min_contour_area":        data.get_min_contour_area(),
            "max_contour_area":        data.get_max_contour_area(),
            "gaussian_blur":           data.get_gaussian_blur(),
            "blur_kernel_size":        data.get_blur_kernel_size(),
            "threshold_type":          data.get_threshold_type(),
            "dilate_enabled":          data.get_dilate_enabled(),
            "dilate_kernel_size":      data.get_dilate_kernel_size(),
            "dilate_iterations":       data.get_dilate_iterations(),
            "erode_enabled":           data.get_erode_enabled(),
            "erode_kernel_size":       data.get_erode_kernel_size(),
            "erode_iterations":        data.get_erode_iterations(),
            "chessboard_width":        data.get_chessboard_width(),
            "chessboard_height":       data.get_chessboard_height(),
            "square_size_mm":          data.get_square_size_mm(),
            "calibration_skip_frames": data.get_calibration_skip_frames(),
            "brightness_auto":         data.get_brightness_auto(),
            "brightness_kp":           data.get_brightness_kp(),
            "brightness_ki":           data.get_brightness_ki(),
            "brightness_kd":           data.get_brightness_kd(),
            "target_brightness":       data.get_target_brightness(),
            "aruco_enabled":           data.get_aruco_enabled(),
            "aruco_dictionary":        data.get_aruco_dictionary(),
            "aruco_flip_image":        data.get_aruco_flip_image(),
        }

    @staticmethod
    def from_flat_dict(flat: dict, base: CameraSettings) -> CameraSettings:
        """Merge flat dict from the SettingsView into a copy of base."""
        d = deepcopy(base)
        g = flat.get

        d.set_camera_index(int(g("index", d.get_camera_index())))
        d.set_width(int(g("width", d.get_camera_width())))
        d.set_height(int(g("height", d.get_camera_height())))
        d.set_skip_frames(int(g("skip_frames", d.get_skip_frames())))

        d.set_contour_detection(bool(g("contour_detection", d.get_contour_detection())))
        d.set_draw_contours(bool(g("draw_contours", d.get_draw_contours())))
        d.set_threshold(int(g("threshold", d.get_threshold())))
        d.set_threshold_pickup_area(int(g("threshold_pickup_area", d.get_threshold_pickup_area())))
        d.set_epsilon(float(g("epsilon", d.get_epsilon())))
        d.set_min_contour_area(float(g("min_contour_area", d.get_min_contour_area())))
        d.set_max_contour_area(float(g("max_contour_area", d.get_max_contour_area())))

        d.set_gaussian_blur(bool(g("gaussian_blur", d.get_gaussian_blur())))
        d.set_blur_kernel_size(int(g("blur_kernel_size", d.get_blur_kernel_size())))
        d.set_threshold_type(str(g("threshold_type", d.get_threshold_type())))
        d.set_dilate_enabled(bool(g("dilate_enabled", d.get_dilate_enabled())))
        d.set_dilate_kernel_size(int(g("dilate_kernel_size", d.get_dilate_kernel_size())))
        d.set_dilate_iterations(int(g("dilate_iterations", d.get_dilate_iterations())))
        d.set_erode_enabled(bool(g("erode_enabled", d.get_erode_enabled())))
        d.set_erode_kernel_size(int(g("erode_kernel_size", d.get_erode_kernel_size())))
        d.set_erode_iterations(int(g("erode_iterations", d.get_erode_iterations())))

        d.set_chessboard_width(int(g("chessboard_width", d.get_chessboard_width())))
        d.set_chessboard_height(int(g("chessboard_height", d.get_chessboard_height())))
        d.set_square_size_mm(float(g("square_size_mm", d.get_square_size_mm())))
        d.set_calibration_skip_frames(int(g("calibration_skip_frames", d.get_calibration_skip_frames())))

        d.set_brightness_auto(bool(g("brightness_auto", d.get_brightness_auto())))
        d.set_brightness_kp(float(g("brightness_kp", d.get_brightness_kp())))
        d.set_brightness_ki(float(g("brightness_ki", d.get_brightness_ki())))
        d.set_brightness_kd(float(g("brightness_kd", d.get_brightness_kd())))
        d.set_target_brightness(float(g("target_brightness", d.get_target_brightness())))

        d.set_aruco_enabled(bool(g("aruco_enabled", d.get_aruco_enabled())))
        d.set_aruco_dictionary(str(g("aruco_dictionary", d.get_aruco_dictionary())))
        d.set_aruco_flip_image(bool(g("aruco_flip_image", d.get_aruco_flip_image())))

        return d

    # ── nested JSON ↔ CameraSettingsData ──────────────────────────────────────

    @staticmethod
    def from_json(data: dict) -> CameraSettingsData:
        """Parse from the nested JSON format used by the repository."""
        pre   = data.get("Preprocessing",     {})
        cal   = data.get("Calibration",       {})
        bri   = data.get("Brightness Control", {})
        aruco = data.get("Aruco",             {})

        points: List[Tuple[int, int]] = []
        for i in range(1, 5):
            pt = bri.get(f"Brightness area point {i}")
            if pt:
                points.append((int(pt[0]), int(pt[1])))

        return CameraSettingsData(
            index                   = data.get("Index",                    0),
            width                   = data.get("Width",                    1280),
            height                  = data.get("Height",                   720),
            skip_frames             = data.get("Skip frames",              30),
            capture_position_offset = data.get("Capture position offset",  -4),
            contour_detection       = data.get("Contour detection",        True),
            draw_contours           = data.get("Draw contours",            True),
            threshold               = data.get("Threshold",                150),
            threshold_pickup_area   = data.get("Threshold pickup area",    200),
            epsilon                 = data.get("Epsilon",                  0.05),
            min_contour_area        = data.get("Min contour area",         1000.0),
            max_contour_area        = data.get("Max contour area",         10_000_000.0),
            gaussian_blur           = pre.get("Gaussian blur",             True),
            blur_kernel_size        = pre.get("Blur kernel size",          3),
            threshold_type          = pre.get("Threshold type",            "binary_inv"),
            dilate_enabled          = pre.get("Dilate enabled",            True),
            dilate_kernel_size      = pre.get("Dilate kernel size",        3),
            dilate_iterations       = pre.get("Dilate iterations",         2),
            erode_enabled           = pre.get("Erode enabled",             True),
            erode_kernel_size       = pre.get("Erode kernel size",         3),
            erode_iterations        = pre.get("Erode iterations",          4),
            chessboard_width        = cal.get("Chessboard width",          32),
            chessboard_height       = cal.get("Chessboard height",         20),
            square_size_mm          = cal.get("Square size (mm)",          25.0),
            calibration_skip_frames = cal.get("Skip frames",               30),
            brightness_auto         = bri.get("Enable auto adjust",        True),
            brightness_kp           = bri.get("Kp",                        0.0),
            brightness_ki           = bri.get("Ki",                        0.2),
            brightness_kd           = bri.get("Kd",                        0.05),
            target_brightness       = bri.get("Target brightness",         200.0),
            brightness_area_points  = points,
            aruco_enabled           = aruco.get("Enable detection",        False),
            aruco_dictionary        = aruco.get("Dictionary",              "DICT_4X4_1000"),
            aruco_flip_image        = aruco.get("Flip image",              False),
        )

    @staticmethod
    def to_json(data: CameraSettingsData) -> dict:
        """Serialize to the nested JSON format used by the repository."""
        bri: dict = {
            "Enable auto adjust": data.brightness_auto,
            "Kp":                 data.brightness_kp,
            "Ki":                 data.brightness_ki,
            "Kd":                 data.brightness_kd,
            "Target brightness":  data.target_brightness,
        }
        for i, pt in enumerate(data.brightness_area_points[:4], start=1):
            bri[f"Brightness area point {i}"] = list(pt)

        return {
            "Index":                   data.index,
            "Width":                   data.width,
            "Height":                  data.height,
            "Skip frames":             data.skip_frames,
            # "Capture position offset": data.capture_position_offset,
            "Contour detection":       data.contour_detection,
            "Draw contours":           data.draw_contours,
            "Threshold":               data.threshold,
            "Threshold pickup area":   data.threshold_pickup_area,
            "Epsilon":                 data.epsilon,
            "Min contour area":        data.min_contour_area,
            "Max contour area":        data.max_contour_area,
            "Preprocessing": {
                "Gaussian blur":      data.gaussian_blur,
                "Blur kernel size":   data.blur_kernel_size,
                "Threshold type":     data.threshold_type,
                "Dilate enabled":     data.dilate_enabled,
                "Dilate kernel size": data.dilate_kernel_size,
                "Dilate iterations":  data.dilate_iterations,
                "Erode enabled":      data.erode_enabled,
                "Erode kernel size":  data.erode_kernel_size,
                "Erode iterations":   data.erode_iterations,
            },
            "Calibration": {
                "Chessboard width":  data.chessboard_width,
                "Chessboard height": data.chessboard_height,
                "Square size (mm)":  data.square_size_mm,
                "Skip frames":       data.calibration_skip_frames,
            },
            "Brightness Control": bri,
            "Aruco": {
                "Enable detection": data.aruco_enabled,
                "Dictionary":       data.aruco_dictionary,
                "Flip image":       data.aruco_flip_image,
            },
        }
