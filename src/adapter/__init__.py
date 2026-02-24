"""
Adapter package public API.

Exposes the three adapter types that a composition root (e.g. adapter.py __main__)
needs to wire the plugin to the vision system.
"""
from src.adapter.mapper import VisionSystemSettingsMapper
from src.adapter.vision_system_settings_adapter import VisionSystemSettingsAdapter
from src.adapter.vision_system_actions_adapter import VisionSystemActionsAdapter
from src.adapter.frame_bridge import FrameBridge

__all__ = [
    "VisionSystemSettingsMapper",
    "VisionSystemSettingsAdapter",
    "VisionSystemActionsAdapter",
    "FrameBridge",
]

