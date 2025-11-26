import os
import dearpygui.dearpygui as dpg

from store import ProjectStore
from ui.ui_sections import SectionsUI
from ui.ui_modules import ModulesUI
from ui.ui_reports import ReportsUI   # assuming you have this


SAVE_FILE = "project.json"   # single source of truth


# ===============================================================

def load_or_create_project():
    store = ProjectStore()

    if os.path.exists(SAVE_FILE):
        print(f"Loading project: {SAVE_FILE}")
        try:
            store.load(SAVE_FILE)        # <<—— MUST BE CALLED
        except Exception as e:
            print(f"Failed to load project, creating new: {e}")
    else:
        print("No save file found, starting fresh.")

    return store

# ===============================================================

def save_project(store):
    print("Saving project...")
    store.save(SAVE_FILE)

# ===============================================================

if __name__ == "__main__":

    store = load_or_create_project()

    dpg.create_context()
    dpg.create_viewport(title="Executable Map Tool", width=900, height=700)

    with dpg.font_registry():
        default_font = dpg.add_font("./JetBrainsMono-Regular.ttf", 16)
        dpg.bind_font(default_font)


    with dpg.window(label="Executable Map Tool", width=900, height=700, pos=(0,0)) as root:

        # Tabs container
        with dpg.tab_bar() as tabs:

            sections_ui = SectionsUI(store, change_callback=lambda: save_project(store))
            modules_ui  = ModulesUI(store, change_callback=lambda: save_project(store))
            reports_ui  = ReportsUI(store)

            # Build UI
            sections_ui.draw(tabs)
            modules_ui.draw(tabs)
            reports_ui.draw(tabs)

        # After building windows, force UI to refresh from loaded JSON
        sections_ui.refresh()
        modules_ui.refresh_modules()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
