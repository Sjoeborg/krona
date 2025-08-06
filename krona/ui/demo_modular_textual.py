from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from krona.ui.modules.data_display import CardDisplayModule, TableDisplayModule
from krona.ui.modules.interactive import FormModule
from krona.ui.modules.navigation import SidebarNavigationModule, TabNavigationModule
from krona.ui.modules.notifications import ToastNotificationModule
from krona.ui.modules.progress import SimpleProgressModule
from krona.ui.modules.settings import SettingsModule

# Example data for modules
table_data = [
    {"Name": "Alice", "Role": "Admin", "Active": True},
    {"Name": "Bob", "Role": "User", "Active": False},
    {"Name": "Charlie", "Role": "User", "Active": True},
]
card_data = [
    {"Title": "Card 1", "Description": "This is the first card."},
    {"Title": "Card 2", "Description": "This is the second card."},
    {"Title": "Card 3", "Description": "This is the third card."},
]

form_fields = [
    {"name": "username", "label": "Username", "type": "text", "required": True},
    {"name": "bio", "label": "Bio", "type": "textarea"},
    {"name": "role", "label": "Role", "type": "select", "options": ["Admin", "User"]},
    {"name": "active", "label": "Active", "type": "switch"},
]

sidebar_items = [
    {"id": "table", "text": "Table", "icon": "📋"},
    {"id": "cards", "text": "Cards", "icon": "🗂️"},
    {"id": "form", "text": "Form", "icon": "📝"},
    {"id": "progress", "text": "Progress", "icon": "⏳"},
    {"id": "notify", "text": "Notify", "icon": "🔔"},
    {"id": "settings", "text": "Settings", "icon": "⚙️"},
]

tabs = [
    {"id": "main", "text": "Main", "icon": "🏠"},
    {"id": "extra", "text": "Extra", "icon": "✨"},
]


class DemoModularTextualApp(App):
    """Demo app for modular Textual UI components."""

    CSS_PATH = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            # Sidebar navigation
            self.sidebar = SidebarNavigationModule(sidebar_items)
            yield self.sidebar.create_widget()
            # Main content area
            with Vertical(id="main_content"):
                # Tab navigation
                self.tabs = TabNavigationModule(tabs)
                yield self.tabs.create_widget()
                # Content area (populated by tab or sidebar selection)
                self.content_area = Vertical(id="content_area")
                yield self.content_area
        yield Footer()

    def on_mount(self) -> None:
        # Register navigation callbacks
        self.sidebar.navigation_callbacks["on_navigation"] = self.show_demo
        self.tabs.navigation_callbacks["on_tab_change"] = self.show_tab_content
        # Show default content
        self.show_demo("table")

    def show_demo(self, item_id: str) -> None:
        self.content_area.remove_children()
        if item_id == "table":
            table = TableDisplayModule(table_data, columns=["Name", "Role", "Active"])
            self.content_area.mount(table.create_widget())
        elif item_id == "cards":
            cards = CardDisplayModule(card_data)
            self.content_area.mount(cards.create_widget())
        elif item_id == "form":
            form = FormModule(form_fields)
            form.callbacks["on_submit"] = lambda values: self.notify(f"Form submitted: {values}")
            self.content_area.mount(form.create_widget())
        elif item_id == "progress":
            progress = SimpleProgressModule(total=100)
            widget = progress.create_widget()
            self.content_area.mount(widget)
            # Animate progress for demo
            self.set_interval(0.05, self._progress_tick, progress)
        elif item_id == "notify":
            notify = ToastNotificationModule()
            widget = notify.create_widget()
            self.content_area.mount(widget)
            notify.show_notification("This is a toast notification!", notification_type="info")
        elif item_id == "settings":
            settings = SettingsModule()
            self.content_area.mount(settings.create_widget())
        else:
            self.content_area.mount(Static(f"No demo for '{item_id}' yet."))

    def show_tab_content(self, tab_id: str) -> None:
        self.content_area.remove_children()
        self.content_area.mount(Static(f"Tab content for '{tab_id}' (add your own modules here!)"))

    def notify(self, message: str) -> None:
        # Show a notification in the notify tab
        self.show_demo("notify")
        # Optionally, you could keep a reference to the ToastNotificationModule and call show_notification

    def _progress_tick(self, progress: SimpleProgressModule) -> None:
        if progress.current_progress < progress.total:
            progress.update_progress(progress.current_progress + 1)
        else:
            self.set_interval(0, None)  # Stop the interval


if __name__ == "__main__":
    DemoModularTextualApp().run()
