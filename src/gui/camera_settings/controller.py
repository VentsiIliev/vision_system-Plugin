from src.gui.camera_settings.model import CameraSettingsModel
from src.gui.camera_settings.mapper import CameraSettingsMapper
from src.gui.camera_settings.view.camera_settings_view import CameraSettingsView


class CameraSettingsController:
    def __init__(self, model: CameraSettingsModel, view: CameraSettingsView):
        self._model = model
        self._view = view

        # Connect settings persistence signals
        self._view.save_requested.connect(self._on_save)


    def load(self) -> None:
        settings = self._model.load()
        # Access the internal settings_view to set values
        self._view.settings_view.set_values(CameraSettingsMapper.to_flat_dict(settings))

    def _on_save(self, flat: dict) -> None:
        # Convert flat dict to CameraSettingsData using mapper
        # Use current model settings as base
        current_settings = self._model._settings
        settings = CameraSettingsMapper.from_flat_dict(flat, current_settings)
        self._model.save(settings)
        print(f"[controller] Camera settings saved successfully")
