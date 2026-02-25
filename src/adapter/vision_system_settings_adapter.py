"""
Persistence adapter: bridges VisionSystem.service to ISettingsPersistenceService.

Dependency direction: adapter → vision, adapter → plugin DTO, adapter → mapper.
The plugin never imports this class.
"""
from src.VisionSystem.VisionSystem import VisionSystem
from src.adapter.mapper import VisionSystemSettingsMapper
from src.plugin.camera_settings.camera_settings_data import CameraSettingsData


class VisionSystemSettingsAdapter:
    """
    Implements ISettingsPersistenceService.

    Translates load/save calls between the plugin's CameraSettingsData DTO
    and the VisionSystem's internal CameraSettings / dict representation.
    """

    def __init__(self, vision_system: VisionSystem, mapper: VisionSystemSettingsMapper):
        self._vs = vision_system
        self._mapper = mapper

    # ── ISettingsPersistenceService ──────────────────────────────────────────

    def load_settings(self) -> CameraSettingsData:
        domain_settings = self._vs.service.loadSettings()
        return self._mapper.to_dto(domain_settings)

    def save_settings(self, settings: CameraSettingsData) -> None:
        settings_dict = self._mapper.to_domain(settings)
        self._vs.service.saveSettings(settings_dict)
        # Delegate to VisionSystem.updateSettings which wires all side-effects
        self._vs.updateSettings(settings_dict)

