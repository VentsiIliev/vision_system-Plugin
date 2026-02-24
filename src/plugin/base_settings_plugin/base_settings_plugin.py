from typing import Generic, TypeVar, Optional, Tuple
from PyQt6.QtWidgets import QWidget

# Type variables
TService = TypeVar("TService")
TModel = TypeVar("TModel")
TController = TypeVar("TController")
TView = TypeVar("TView", bound=QWidget)


class BaseSettingsPlugin(Generic[TService, TModel, TController, TView]):
    """
    Generic base class for MVC-style settings plugins.

    Handles wiring of service → model → controller → view,
    exposes widget, load(), save() consistently.

    Usage:
        class MyPlugin(BaseSettingsPlugin[MyService, MyModel, MyController, QWidget]):
            def _create_model(self, service: MyService) -> MyModel:
                return MyModel(service)

            def _create_view(self) -> QWidget:
                return my_tab_factory()[0]

            def _create_controller(self, model: MyModel, view: QWidget) -> MyController:
                return MyController(model, view)
    """

    def __init__(self, service: TService):
        """
        Initialize the plugin with dependency injection.

        Args:
            service: The service that handles data persistence
        """
        self._service = service
        self._model: TModel = self._create_model(service)
        self._view: TView = self._create_view()
        self._controller: TController = self._create_controller(self._model, self._view)
        self._widget: QWidget = self._extract_main_widget(self._view)

    # ── Abstract Methods ─────────────────────────────────────────────────────────

    def _create_model(self, service: TService) -> TModel:
        raise NotImplementedError("Subclass must implement _create_model()")

    def _create_view(self) -> TView | Tuple[TView, ...]:
        raise NotImplementedError("Subclass must implement _create_view()")

    def _create_controller(self, model: TModel, view: TView) -> TController:
        raise NotImplementedError("Subclass must implement _create_controller()")

    # ── Helpers ─────────────────────────────────────────────────────────────────

    def _extract_main_widget(self, view_result) -> TView:
        """Extract main QWidget if factory returned a tuple (view, extra_tabs)."""
        if isinstance(view_result, tuple):
            return view_result[0]
        return view_result

    # ── Public API ───────────────────────────────────────────────────────────────

    @property
    def widget(self) -> TView:
        """Returns the main QWidget for this settings plugin."""
        return self._widget

    def load(self) -> None:
        """Load data from model/service into the UI via controller."""
        if hasattr(self._controller, "load"):
            self._controller.load()

    def save(self) -> None:
        """Save current settings via controller/model to service."""
        if hasattr(self._controller, "save"):
            self._controller.save()
        else:
            print(f"[{self.__class__.__name__}] Save not implemented; may auto-save on change")