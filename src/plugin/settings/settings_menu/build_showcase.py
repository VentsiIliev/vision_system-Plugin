from src.plugins.camera_settings.view.camera_tab import camera_tab_factory
from src.plugins.glue_settings.view.glue_tab import glue_tab_factory
from src.plugins.robot_settings.view.robot_tab import robot_tab_factory
from src.settings.settings_menu.category_descriptor import CategoryDescriptor
from src.settings.settings_menu.settings_menu import SettingsNavigationWidget
from src.settings.settings_view.build_showcase import build_showcase

def build_settings_menu_showcase():
    CUSTOM_CATEGORIES = [
        CategoryDescriptor(
            id = "robot",
            icon = "mdi.robot-industrial"
        ),
        CategoryDescriptor(
            id = "glue",
            icon = "fa6s.droplet"
        ),
        CategoryDescriptor(
            id = "camera",
            icon = "mdi.camera"
        ),
    ]

    # Define factory map - functions that create widgets for each category
    factory_map = {
        "robot":  lambda: robot_tab_factory()[0],
        "glue":   lambda: glue_tab_factory()[0],
        "camera": lambda: camera_tab_factory()[0],
        "users": build_showcase,
        "database": build_showcase,
        "api": build_showcase,
        "backup": build_showcase,
        "logging": build_showcase,
    }

    nav = SettingsNavigationWidget(
            categories=CUSTOM_CATEGORIES,
            factory_map=factory_map
        )

    return nav