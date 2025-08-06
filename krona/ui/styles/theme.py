"""CSS theme system for Krona UI."""

from __future__ import annotations


class Theme:
    """Theme configuration for Krona UI."""

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self.colors = self._get_default_colors()
        self.styles = self._get_default_styles()

    def _get_default_colors(self) -> dict[str, str]:
        """Get default color scheme."""
        return {
            "primary": "#2563eb",
            "primary-lighten-1": "#3b82f6",
            "primary-lighten-2": "#60a5fa",
            "primary-lighten-3": "#93c5fd",
            "primary-darken-1": "#1d4ed8",
            "primary-darken-2": "#1e40af",
            "accent": "#10b981",
            "error": "#ef4444",
            "warning": "#f59e0b",
            "success": "#10b981",
            "text": "#ffffff",
            "text-muted": "#9ca3af",
            "surface": "#1f2937",
            "background": "#111827",
        }

    def _get_default_styles(self) -> dict[str, str]:
        """Get default style definitions."""
        return {
            "sidebar": f"""
                dock: left;
                width: 30;
                background: {self.colors["surface"]};
                border-right: thick {self.colors["primary"]};
            """,
            "sidebar-title": f"""
                background: {self.colors["primary"]};
                color: {self.colors["text"]};
                text-align: center;
                text-style: bold;
                height: 3;
                content-align: center middle;
            """,
            "sidebar-item": f"""
                padding: 1 2;
                background: {self.colors["surface"]};
                color: {self.colors["text"]};
                height: 3;
                content-align: left middle;
            """,
            "sidebar-item-hover": f"""
                background: {self.colors["primary-lighten-3"]};
                text-style: bold;
            """,
            "view-title": f"""
                text-style: bold;
                text-align: center;
                height: 3;
                content-align: center middle;
                background: {self.colors["primary-darken-2"]};
                color: {self.colors["text"]};
                margin-bottom: 1;
            """,
            "dashboard-stats": f"""
                height: 8;
                margin: 1;
                border: solid {self.colors["primary"]};
            """,
            "stats-title": f"""
                text-style: bold;
                text-align: center;
                background: {self.colors["primary-darken-1"]};
                color: {self.colors["text"]};
                height: 1;
            """,
            "stats-row": """
                height: 6;
                padding: 1;
            """,
            "stat-card": f"""
                border: solid {self.colors["primary-lighten-2"]};
                margin: 0 1;
                padding: 1;
                text-align: center;
            """,
            "stat-label": """
                text-style: dim;
                height: 1;
            """,
            "stat-value": f"""
                text-style: bold;
                color: {self.colors["accent"]};
                height: 2;
                content-align: center middle;
            """,
            "controls": """
                height: 5;
                margin: 1;
            """,
            "progress-container": """
                height: 3;
                margin: 1;
                padding: 1;
            """,
            "progress-label": """
                width: 20;
                content-align: left middle;
            """,
            "table-base": """
                margin: 1;
            """,
            "table-header": f"""
                background: {self.colors["primary"]};
                color: {self.colors["text"]};
                text-style: bold;
            """,
            "table-cursor": f"""
                background: {self.colors["primary-lighten-2"]};
            """,
            "table-hover": f"""
                background: {self.colors["primary-lighten-3"]};
            """,
            "chart-title": f"""
                text-style: bold;
                text-align: center;
                background: {self.colors["primary-darken-1"]};
                color: {self.colors["text"]};
                height: 2;
                content-align: center middle;
                margin-bottom: 1;
            """,
            "chart-controls": f"""
                height: 4;
                margin: 1;
                padding: 1;
                border: solid {self.colors["primary-lighten-2"]};
            """,
            "switch-label": """
                margin: 0 1;
                content-align: left middle;
            """,
            "chart-display": f"""
                border: solid {self.colors["primary-lighten-1"]};
                margin: 1;
                padding: 1;
                min-height: 25;
            """,
            "error-display": f"""
                background: {self.colors["error"]};
                color: {self.colors["text"]};
                padding: 1;
                margin: 1;
                text-align: center;
            """,
        }

    def get_css(self) -> str:
        """Generate complete CSS for the theme."""
        css_parts = []

        # Add color variables
        css_parts.append("/* Color Variables */")
        for name, color in self.colors.items():
            css_parts.append(f"${name}: {color};")

        css_parts.append("")

        # Add style definitions
        css_parts.append("/* Style Definitions */")
        for selector, style in self.styles.items():
            css_parts.append(f".{selector} {{")
            css_parts.append(f"    {style}")
            css_parts.append("}")
            css_parts.append("")

        # Add hover states
        css_parts.append("/* Hover States */")
        css_parts.append(".sidebar-item:hover {")
        css_parts.append(f"    {self.styles['sidebar-item-hover']}")
        css_parts.append("}")
        css_parts.append("")

        # Add table styles
        css_parts.append("/* Table Styles */")
        css_parts.append("DataTable > .datatable--header {")
        css_parts.append(f"    {self.styles['table-header']}")
        css_parts.append("}")
        css_parts.append("")
        css_parts.append("DataTable > .datatable--cursor {")
        css_parts.append(f"    {self.styles['table-cursor']}")
        css_parts.append("}")
        css_parts.append("")
        css_parts.append("DataTable > .datatable--hover {")
        css_parts.append(f"    {self.styles['table-hover']}")
        css_parts.append("}")
        css_parts.append("")

        # Add layout styles
        css_parts.append("/* Layout Styles */")
        css_parts.append("TabbedContent {")
        css_parts.append("    margin-left: 30;")
        css_parts.append("}")
        css_parts.append("")
        css_parts.append("Button {")
        css_parts.append("    margin: 0 1;")
        css_parts.append("}")

        return "\n".join(css_parts)

    def update_color(self, name: str, value: str) -> None:
        """Update a color in the theme."""
        if name in self.colors:
            self.colors[name] = value

    def update_style(self, selector: str, style: str) -> None:
        """Update a style in the theme."""
        if selector in self.styles:
            self.styles[selector] = style


class ThemeManager:
    """Manager for UI themes."""

    def __init__(self) -> None:
        self._themes: dict[str, Theme] = {}
        self._current_theme: str | None = None
        self._load_default_themes()

    def _load_default_themes(self) -> None:
        """Load default themes."""
        # Default theme
        default_theme = Theme("default")
        self._themes["default"] = default_theme

        # Dark theme
        dark_theme = Theme("dark")
        dark_theme.colors.update(
            {
                "surface": "#0f172a",
                "background": "#020617",
                "text": "#f8fafc",
                "text-muted": "#64748b",
            }
        )
        self._themes["dark"] = dark_theme

        # Light theme
        light_theme = Theme("light")
        light_theme.colors.update(
            {
                "surface": "#f8fafc",
                "background": "#ffffff",
                "text": "#0f172a",
                "text-muted": "#475569",
                "primary": "#1d4ed8",
                "accent": "#059669",
            }
        )
        self._themes["light"] = light_theme

        self._current_theme = "default"

    def get_theme(self, name: str) -> Theme | None:
        """Get a theme by name."""
        return self._themes.get(name)

    def get_current_theme(self) -> Theme:
        """Get the current theme."""
        return self._themes[self._current_theme]

    def set_current_theme(self, name: str) -> bool:
        """Set the current theme."""
        if name in self._themes:
            self._current_theme = name
            return True
        return False

    def add_theme(self, theme: Theme) -> None:
        """Add a new theme."""
        self._themes[theme.name] = theme

    def get_available_themes(self) -> list[str]:
        """Get list of available theme names."""
        return list(self._themes.keys())


# Global theme manager instance
theme_manager = ThemeManager()
