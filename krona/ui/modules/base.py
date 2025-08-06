"""Base module system for modular Textual components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.widget import Widget

if TYPE_CHECKING:
    pass


class BaseModule(ABC):
    """Base class for all modular Textual components."""

    def __init__(self, name: str, description: str = "", config: dict[str, Any] | None = None) -> None:
        self.name = name
        self.description = description
        self.config = config or {}
        self.widget: Widget | None = None
        self._enabled = True
        self._visible = True

    @property
    def enabled(self) -> bool:
        """Whether the module is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set whether the module is enabled."""
        self._enabled = value
        if self.widget:
            self.widget.disabled = not value

    @property
    def visible(self) -> bool:
        """Whether the module is visible."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """Set whether the module is visible."""
        self._visible = value
        if self.widget:
            self.widget.display = value

    @abstractmethod
    def create_widget(self) -> Widget:
        """Create the main widget for this module."""
        pass

    @abstractmethod
    def compose(self) -> ComposeResult:
        """Compose the module's widgets."""
        pass

    def mount(self, parent: Widget) -> None:
        """Mount this module to a parent widget."""
        self.widget = self.create_widget()
        parent.mount(self.widget)

    def unmount(self) -> None:
        """Unmount this module from its parent."""
        if self.widget and self.widget.parent:
            self.widget.remove()
            self.widget = None

    def update_config(self, config: dict[str, Any]) -> None:
        """Update the module's configuration."""
        self.config.update(config)
        self._apply_config()

    def _apply_config(self) -> None:
        """Apply the current configuration to the widget."""
        if self.widget:
            # Apply common config options
            if "enabled" in self.config:
                self.enabled = self.config["enabled"]
            if "visible" in self.config:
                self.visible = self.config["visible"]

    def get_info(self) -> dict[str, Any]:
        """Get information about this module."""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "visible": self.visible,
            "config": self.config.copy(),
        }


class ModuleRegistry:
    """Registry for managing modular components."""

    def __init__(self) -> None:
        self._modules: dict[str, BaseModule] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, module: BaseModule, category: str = "default") -> None:
        """Register a module."""
        self._modules[module.name] = module
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(module.name)

    def unregister(self, name: str) -> None:
        """Unregister a module."""
        if name in self._modules:
            module = self._modules[name]
            module.unmount()
            del self._modules[name]

            # Remove from categories
            for category_modules in self._categories.values():
                if name in category_modules:
                    category_modules.remove(name)

    def get_module(self, name: str) -> BaseModule | None:
        """Get a module by name."""
        return self._modules.get(name)

    def get_modules_by_category(self, category: str) -> list[BaseModule]:
        """Get all modules in a category."""
        module_names = self._categories.get(category, [])
        return [self._modules[name] for name in module_names if name in self._modules]

    def get_all_modules(self) -> list[BaseModule]:
        """Get all registered modules."""
        return list(self._modules.values())

    def get_categories(self) -> list[str]:
        """Get all available categories."""
        return list(self._categories.keys())

    def mount_all(self, parent: Widget, category: str | None = None) -> None:
        """Mount all modules (or modules in a category) to a parent widget."""
        modules = self.get_modules_by_category(category) if category else self.get_all_modules()
        for module in modules:
            if module.enabled and module.visible:
                module.mount(parent)

    def unmount_all(self) -> None:
        """Unmount all modules."""
        for module in self._modules.values():
            module.unmount()


# Global module registry
module_registry = ModuleRegistry()
