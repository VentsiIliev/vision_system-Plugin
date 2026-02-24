"""
CameraSettingsView — horizontal split panel (optimised for 1280×1024).

Left  (1/3 width): ClickableLabel preview  +  CameraControlsWidget
Right (2/3 width): schema-driven SettingsView (tabs: Core, Detection,
                   Calibration, Brightness, ArUco)

The persistence controller works with the inner SettingsView.
A separate ICameraActionsService handles the action controls (DI).
The application can also plug in a real camera feed via set_preview_widget().

All internal widget signals are re-emitted for convenient access.
"""
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal

from src.gui.settings.settings_view.settings_view import SettingsView
from src.gui.utils_widgets.clickable_label import ClickableLabel
from src.gui.camera_settings.view.camera_controls_widget import CameraControlsWidget


class CameraSettingsView(QWidget):
    """
    Left (1/3): ClickableLabel + CameraControlsWidget
    Right (2/3): SettingsView tabs

    Signals (re-emitted from internal widgets):
        # From ClickableLabel
        corner_updated(str, int, float, float) — area_name, corner_index, x_norm, y_norm
        empty_clicked(str, float, float) — area_name, x_norm, y_norm

        # From CameraControlsWidget
        raw_mode_toggled(bool) — raw mode enabled/disabled
        capture_requested() — capture image button clicked
        calibrate_camera_requested() — calibrate camera button clicked
        calibrate_robot_requested() — calibrate robot button clicked
        active_area_changed(str) — active area name for editing

        # From SettingsView
        value_changed_signal(str, object, str) — key, value, component_name
        save_requested(dict) — save button clicked with all values

    Expose points::
        view.preview_label — ClickableLabel (None after set_preview_widget)
        view.controls — CameraControlsWidget with raw_mode / capture / calibrate signals
        view.settings_view — inner SettingsView for the persistence controller
    """

    # ============================================================================
    # Signal Definitions - MUST be class attributes (not instance attributes)
    # ============================================================================

    # Signals from ClickableLabel
    corner_updated = pyqtSignal(str, int, float, float)  # area_name, index, xn, yn
    empty_clicked = pyqtSignal(str, float, float)  # area_name, xn, yn

    # Signals from CameraControlsWidget
    raw_mode_toggled = pyqtSignal(bool)
    capture_requested = pyqtSignal()
    calibrate_camera_requested = pyqtSignal()
    calibrate_robot_requested = pyqtSignal()
    active_area_changed = pyqtSignal(str)
    view_mode_changed = pyqtSignal(str)  # "live" | "threshold"

    # Signals from SettingsView
    value_changed_signal = pyqtSignal(str, object, str)  # key, value, component_name
    save_requested = pyqtSignal(dict)

    def __init__(self, settings_view: SettingsView, parent=None):
        super().__init__(parent)
        self._settings_view = settings_view
        self._build_ui()
        self._connect_signals()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_left_panel(), stretch=1)
        root.addWidget(self._settings_view,      stretch=2)

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        # panel.setStyleSheet("background: #12121F;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._preview_label = ClickableLabel()
        self._preview_label.add_area("pickup_area")
        self._preview_label.add_area("spray_area")
        self._preview_label.add_area("brightness_area")
        layout.addWidget(self._preview_label, stretch=1)

        self._controls = CameraControlsWidget()
        layout.addWidget(self._controls, stretch=0)

        self._left_layout = layout
        return panel

    def _connect_signals(self) -> None:
        """Wire up all internal widget signals to re-emit them."""
        # ClickableLabel signals
        if self._preview_label:
            self._preview_label.corner_updated.connect(self.corner_updated.emit)
            self._preview_label.empty_clicked.connect(self.empty_clicked.emit)

        # CameraControlsWidget signals
        self._controls.raw_mode_toggled.connect(self.raw_mode_toggled.emit)
        self._controls.capture_requested.connect(self.capture_requested.emit)
        self._controls.calibrate_camera_requested.connect(self.calibrate_camera_requested.emit)
        self._controls.calibrate_robot_requested.connect(self.calibrate_robot_requested.emit)
        self._controls.active_area_changed.connect(self._on_active_area_changed)
        self._controls.view_mode_changed.connect(self.view_mode_changed.emit)

        # SettingsView signals
        self._settings_view.value_changed_signal.connect(self.value_changed_signal.emit)
        self._settings_view.save_requested.connect(self.save_requested.emit)

    # ── Internal slots ─────────────────────────────────────────────────────────

    def _on_active_area_changed(self, name: str) -> None:
        """Handle active area change internally and re-emit."""
        if self._preview_label:
            self._preview_label.set_active_area(name if name else None)
        # Re-emit the signal
        self.active_area_changed.emit(name)

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_preview_widget(self, widget: QWidget) -> None:
        """Replace the ClickableLabel with a real camera feed widget."""
        self._preview_label.setParent(None)
        self._preview_label = None
        self._left_layout.insertWidget(0, widget, stretch=1)

    @property
    def preview_label(self) -> ClickableLabel | None:
        """ClickableLabel for brightness area corner editing, or None if replaced."""
        return self._preview_label

    @property
    def controls(self) -> CameraControlsWidget:
        """Action controls strip (raw mode, capture, calibrate signals)."""
        return self._controls

    @property
    def settings_view(self) -> SettingsView:
        """Inner SettingsView — used by the persistence controller."""
        return self._settings_view

    def update_camera_view(self,image):
        self._preview_label.set_frame(image)
