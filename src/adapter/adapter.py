"""
Composition root.

The only responsibility of this module is to instantiate and wire together:
    VisionSystem  ←→  adapters  ←→  CameraSettingsPlugin

No business logic lives here.  Dependency direction:
    adapter → plugin interfaces
    adapter → vision system
    plugin  ↛  vision system
    vision  ↛  plugin
"""
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from external_dependencies.MessageBroker import MessageBroker
from src.VisionSystem.VisionSystem import VisionSystem
from src.VisionSystem.core.external_communication.system_state_management import VisionTopics

from src.adapter.mapper import VisionSystemSettingsMapper
from src.adapter.vision_system_settings_adapter import VisionSystemSettingsAdapter
from src.adapter.vision_system_actions_adapter import VisionSystemActionsAdapter
from src.adapter.frame_bridge import FrameBridge

from src.plugin.camera_settings import CameraSettingsPlugin


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ── Infrastructure ───────────────────────────────────────────────────────
    broker = MessageBroker()
    vs = VisionSystem(message_broker=broker)
    vs.start_system()

    # ── Adapters (only these know both sides) ────────────────────────────────
    mapper      = VisionSystemSettingsMapper()
    persistence = VisionSystemSettingsAdapter(vision_system=vs, mapper=mapper)
    actions     = VisionSystemActionsAdapter(vision_system=vs)

    # ── Plugin (receives only plugin-owned protocols) ────────────────────────
    plugin = CameraSettingsPlugin(
        persistence=persistence,
        actions=actions,
        mapper=mapper,
    )
    plugin.load()

    # ── Frame bridge: vision thread → Qt main thread → preview label ─────────
    bridge = FrameBridge(preview_label=plugin.preview_label)
    broker.subscribe(VisionTopics.LATEST_IMAGE,    bridge.on_live_frame)
    broker.subscribe(VisionTopics.THRESHOLD_IMAGE, bridge.on_threshold_frame)
    plugin.widget.controls.view_mode_changed.connect(bridge.set_mode)

    # ── Window ───────────────────────────────────────────────────────────────
    win = QMainWindow()
    win.setWindowTitle("Camera Settings")
    win.resize(1280, 1024)
    win.setCentralWidget(plugin.widget)
    win.show()

    app.aboutToQuit.connect(vs.stop_system)
    sys.exit(app.exec())
