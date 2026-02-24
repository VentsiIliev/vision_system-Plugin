"""
Concrete mapper: translates between CameraSettingsData (plugin DTO)
and CameraSettings (VisionSystem domain model / flat dict for the view).

This is the ONLY place in the codebase that imports from both sides.
Direction: adapter → plugin DTO, adapter → vision model.
"""
from __future__ import annotations

from copy import deepcopy
from typing import List, Tuple, cast

from src.VisionSystem.core.settings.CameraSettings import CameraSettings
from src.plugin.camera_settings.camera_settings_data import CameraSettingsData


class VisionSystemSettingsMapper:
    """
    Implements ISettingsMapper.

    to_flat_dict  : CameraSettings (vision)  → flat dict  (view)
    from_flat_dict: flat dict (view) + base  → CameraSettingsData (plugin DTO)

    Also provides:
    to_domain     : CameraSettingsData       → CameraSettings (vision)
    to_dto        : CameraSettings (vision)  → CameraSettingsData (plugin DTO)
    """

    # ── ISettingsMapper ──────────────────────────────────────────────────────

    def to_flat_dict(self, settings: CameraSettingsData) -> dict:
        """CameraSettingsData → flat dict consumed by SettingsView."""
        return {
            "index":                   settings.index,
            "width":                   settings.width,
            "height":                  settings.height,
            "skip_frames":             settings.skip_frames,
            "contour_detection":       settings.contour_detection,
            "draw_contours":           settings.draw_contours,
            "threshold":               settings.threshold,
            "threshold_pickup_area":   settings.threshold_pickup_area,
            "epsilon":                 settings.epsilon,
            "min_contour_area":        settings.min_contour_area,
            "max_contour_area":        settings.max_contour_area,
            "gaussian_blur":           settings.gaussian_blur,
            "blur_kernel_size":        settings.blur_kernel_size,
            "threshold_type":          settings.threshold_type,
            "dilate_enabled":          settings.dilate_enabled,
            "dilate_kernel_size":      settings.dilate_kernel_size,
            "dilate_iterations":       settings.dilate_iterations,
            "erode_enabled":           settings.erode_enabled,
            "erode_kernel_size":       settings.erode_kernel_size,
            "erode_iterations":        settings.erode_iterations,
            "chessboard_width":        settings.chessboard_width,
            "chessboard_height":       settings.chessboard_height,
            "square_size_mm":          settings.square_size_mm,
            "calibration_skip_frames": settings.calibration_skip_frames,
            "brightness_auto":         settings.brightness_auto,
            "brightness_kp":           settings.brightness_kp,
            "brightness_ki":           settings.brightness_ki,
            "brightness_kd":           settings.brightness_kd,
            "target_brightness":       settings.target_brightness,
            "aruco_enabled":           settings.aruco_enabled,
            "aruco_dictionary":        settings.aruco_dictionary,
            "aruco_flip_image":        settings.aruco_flip_image,
        }

    def from_flat_dict(self, flat: dict, base: CameraSettingsData) -> CameraSettingsData:
        """Merge a flat dict from SettingsView into a copy of the base DTO."""
        d = deepcopy(base)
        g = flat.get

        d.index                   = int(g("index",                   d.index))
        d.width                   = int(g("width",                   d.width))
        d.height                  = int(g("height",                  d.height))
        d.skip_frames             = int(g("skip_frames",             d.skip_frames))

        d.contour_detection       = bool(g("contour_detection",      d.contour_detection))
        d.draw_contours           = bool(g("draw_contours",          d.draw_contours))
        d.threshold               = int(g("threshold",               d.threshold))
        d.threshold_pickup_area   = int(g("threshold_pickup_area",   d.threshold_pickup_area))
        d.epsilon                 = float(g("epsilon",               d.epsilon))
        d.min_contour_area        = float(g("min_contour_area",      d.min_contour_area))
        d.max_contour_area        = float(g("max_contour_area",      d.max_contour_area))

        d.gaussian_blur           = bool(g("gaussian_blur",          d.gaussian_blur))
        d.blur_kernel_size        = int(g("blur_kernel_size",        d.blur_kernel_size))
        d.threshold_type          = str(g("threshold_type",          d.threshold_type))
        d.dilate_enabled          = bool(g("dilate_enabled",         d.dilate_enabled))
        d.dilate_kernel_size      = int(g("dilate_kernel_size",      d.dilate_kernel_size))
        d.dilate_iterations       = int(g("dilate_iterations",       d.dilate_iterations))
        d.erode_enabled           = bool(g("erode_enabled",          d.erode_enabled))
        d.erode_kernel_size       = int(g("erode_kernel_size",       d.erode_kernel_size))
        d.erode_iterations        = int(g("erode_iterations",        d.erode_iterations))

        d.chessboard_width        = int(g("chessboard_width",        d.chessboard_width))
        d.chessboard_height       = int(g("chessboard_height",       d.chessboard_height))
        d.square_size_mm          = float(g("square_size_mm",        d.square_size_mm))
        d.calibration_skip_frames = int(g("calibration_skip_frames", d.calibration_skip_frames))

        d.brightness_auto         = bool(g("brightness_auto",        d.brightness_auto))
        d.brightness_kp           = float(g("brightness_kp",         d.brightness_kp))
        d.brightness_ki           = float(g("brightness_ki",         d.brightness_ki))
        d.brightness_kd           = float(g("brightness_kd",         d.brightness_kd))
        d.target_brightness       = float(g("target_brightness",     d.target_brightness))

        d.aruco_enabled           = bool(g("aruco_enabled",          d.aruco_enabled))
        d.aruco_dictionary        = str(g("aruco_dictionary",        d.aruco_dictionary))
        d.aruco_flip_image        = bool(g("aruco_flip_image",       d.aruco_flip_image))

        return d

    # ── Cross-layer translation ──────────────────────────────────────────────

    def to_dto(self, domain: CameraSettings) -> CameraSettingsData:
        """CameraSettings (vision domain) → CameraSettingsData (plugin DTO)."""
        raw_points = domain.get_brightness_area_points() or []
        brightness_area_points = cast(
            List[Tuple[int, int]],
            [(int(pt[0]), int(pt[1])) for pt in raw_points if pt is not None],
        )

        return CameraSettingsData(
            index                   = domain.get_camera_index(),
            width                   = domain.get_camera_width(),
            height                  = domain.get_camera_height(),
            skip_frames             = domain.get_skip_frames(),
            contour_detection       = domain.get_contour_detection(),
            draw_contours           = domain.get_draw_contours(),
            threshold               = domain.get_threshold(),
            threshold_pickup_area   = domain.get_threshold_pickup_area(),
            epsilon                 = domain.get_epsilon(),
            min_contour_area        = domain.get_min_contour_area(),
            max_contour_area        = domain.get_max_contour_area(),
            gaussian_blur           = domain.get_gaussian_blur(),
            blur_kernel_size        = domain.get_blur_kernel_size(),
            threshold_type          = domain.get_threshold_type(),
            dilate_enabled          = domain.get_dilate_enabled(),
            dilate_kernel_size      = domain.get_dilate_kernel_size(),
            dilate_iterations       = domain.get_dilate_iterations(),
            erode_enabled           = domain.get_erode_enabled(),
            erode_kernel_size       = domain.get_erode_kernel_size(),
            erode_iterations        = domain.get_erode_iterations(),
            chessboard_width        = domain.get_chessboard_width(),
            chessboard_height       = domain.get_chessboard_height(),
            square_size_mm          = domain.get_square_size_mm(),
            calibration_skip_frames = domain.get_calibration_skip_frames(),
            brightness_auto         = domain.get_brightness_auto(),
            brightness_kp           = domain.get_brightness_kp(),
            brightness_ki           = domain.get_brightness_ki(),
            brightness_kd           = domain.get_brightness_kd(),
            target_brightness       = domain.get_target_brightness(),
            brightness_area_points  = brightness_area_points,
            aruco_enabled           = domain.get_aruco_enabled(),
            aruco_dictionary        = domain.get_aruco_dictionary(),
            aruco_flip_image        = domain.get_aruco_flip_image(),
        )

    def to_domain(self, dto: CameraSettingsData) -> dict:
        """
        CameraSettingsData (plugin DTO) → nested dict that matches the
        camera_settings.json file format and CameraSettingKey enum values.

        This format is accepted by both:
            VisionSystem.service.saveSettings()   (writes JSON to disk)
            VisionSystem.service.updateSettings() (applies to live domain object)
        """
        brightness: dict = {
            "Enable auto adjust": dto.brightness_auto,
            "Kp":                 dto.brightness_kp,
            "Ki":                 dto.brightness_ki,
            "Kd":                 dto.brightness_kd,
            "Target brightness":  dto.target_brightness,
        }
        for i, pt in enumerate(dto.brightness_area_points[:4], start=1):
            brightness[f"Brightness area point {i}"] = list(pt)

        return {
            "Index":                   dto.index,
            "Width":                   dto.width,
            "Height":                  dto.height,
            "Skip frames":             dto.skip_frames,
            "Capture position offset": dto.capture_position_offset,
            "Threshold":               dto.threshold,
            "Threshold pickup area":   dto.threshold_pickup_area,
            "Epsilon":                 dto.epsilon,
            "Min contour area":        dto.min_contour_area,
            "Max contour area":        dto.max_contour_area,
            "Contour detection":       dto.contour_detection,
            "Draw contours":           dto.draw_contours,
            "Preprocessing": {
                "Gaussian blur":      dto.gaussian_blur,
                "Blur kernel size":   dto.blur_kernel_size,
                "Threshold type":     dto.threshold_type,
                "Dilate enabled":     dto.dilate_enabled,
                "Dilate kernel size": dto.dilate_kernel_size,
                "Dilate iterations":  dto.dilate_iterations,
                "Erode enabled":      dto.erode_enabled,
                "Erode kernel size":  dto.erode_kernel_size,
                "Erode iterations":   dto.erode_iterations,
            },
            "Calibration": {
                "Chessboard width":  dto.chessboard_width,
                "Chessboard height": dto.chessboard_height,
                "Square size (mm)":  dto.square_size_mm,
                "Skip frames":       dto.calibration_skip_frames,
            },
            "Brightness Control": brightness,
            "Aruco": {
                "Enable detection": dto.aruco_enabled,
                "Dictionary":       dto.aruco_dictionary,
                "Flip image":       dto.aruco_flip_image,
            },
        }

