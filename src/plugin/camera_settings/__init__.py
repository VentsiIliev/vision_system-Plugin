from typing import Optional
from PyQt6.QtWidgets import QWidget

from src.VisionSystem.core.external_communication.system_state_management import VisionTopics
from src.plugin.base_settings_plugin.base_settings_plugin import BaseSettingsPlugin
from src.plugin.settings.settings_view import SettingsView
from src.plugin.utils_widgets.clickable_label import ClickableLabel

from src.plugin.camera_settings.controller import CameraSettingsController
from src.plugin.camera_settings.model import CameraSettingsModel
from src.plugin.camera_settings.ICameraSettingsService import ICameraSettingsService
from src.plugin.camera_settings.view.camera_tab import camera_tab_factory
from src.plugin.camera_settings.view.camera_settings_view import CameraSettingsView
# from src.plugin.base_settings_plugin.base_settings_plugin import BaseSettingsPlugin


class CameraSettingsPlugin(
    BaseSettingsPlugin[
        ICameraSettingsService,  # Service
        CameraSettingsModel,     # Model
        CameraSettingsController,# Controller
        CameraSettingsView       # View
    ]
):
    """
    Camera settings plugin with optional camera actions service.

    Usage:
        plugin = CameraSettingsPlugin(service)
        plugin.load()
        window.setCentralWidget(plugin.widget)
    """

    def __init__(self, service: ICameraSettingsService):
        super().__init__(service)



    def _create_model(self, service: ICameraSettingsService) -> CameraSettingsModel:
        return CameraSettingsModel(service)

    def _create_view(self) -> CameraSettingsView:
        view, settings_view = camera_tab_factory()
        self._connect_actions(view)
        return view

    def _create_controller(self, model: CameraSettingsModel, view: CameraSettingsView) -> CameraSettingsController:
        return CameraSettingsController(model, view)

    # ── Private helpers ────────────────────────────────────────────
    def _connect_actions(self, view: CameraSettingsView) -> None:
        ctrl = view.controls
        svc = self._service
        ctrl.raw_mode_toggled.connect(svc.set_raw_mode)
        ctrl.capture_requested.connect(svc.capture_image)
        ctrl.calibrate_camera_requested.connect(svc.calibrate_camera)
        ctrl.calibrate_robot_requested.connect(svc.calibrate_robot)

    # Optional: convenience to access preview label
    @property
    def preview_label(self) -> ClickableLabel | None:
        return self.widget.preview_label

    def set_preview_widget(self, widget: QWidget) -> None:
        self.widget.set_preview_widget(widget)