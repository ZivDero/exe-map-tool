import os
import dearpygui.dearpygui as dpg

from store import ProjectStore
from ui.ui_sections import SectionsUI
from ui.ui_modules_by_name import ModulesNyNameUI
from ui.ui_modules_by_section import ModulesBySectionUI
from ui.ui_reports import ReportsUI
from ui.ui_utils import parse_hex


SAVE_FILE = "project.json"   # single source of truth


# ===============================================================

def load_or_create_project():
    store = ProjectStore()

    if os.path.exists(SAVE_FILE):
        print(f"Loading project: {SAVE_FILE}")
        try:
            store.load(SAVE_FILE)
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

def on_tab_change(sender, app_data):
    # app_data gives the tab *item id*, so we check its label
    if dpg.get_item_label(app_data) == "Reports":
        reports_ui.refresh()

# ===============================================================

def where_ok(store, input_id, label_id):
    addr_str = dpg.get_value(input_id).strip()
    try:
        addr = parse_hex(addr_str)
    except ValueError:
        dpg.set_value(label_id, "Invalid address")
        return

    # Find section
    section_name = None
    sec_id = None
    for sec in store.project.sections.values():
        if sec.start <= addr < sec.end:
            section_name = sec.name
            sec_id = sec.id
            break

    if not section_name:
        dpg.set_value(label_id, "Address not in any section")
        return

    # Find module
    module_name = None
    for mod in store.project.modules.values():
        for rng in mod.ranges:
            if rng.section_id == sec_id and rng.start <= addr < rng.end:
                module_name = mod.name
                break
        if module_name:
            break

    if module_name:
        dpg.set_value(label_id, f"Section: {section_name}, Module: {module_name}")
    else:
        dpg.set_value(label_id, f"Section: {section_name}, No module")

    dpg.hide_item("where_popup")

# ===============================================================

if __name__ == "__main__":

    store = load_or_create_project()

    dpg.create_context()
    dpg.create_viewport(title="Executable Map Tool", width=916, height=700)

    with dpg.font_registry():
        default_font = dpg.add_font("./JetBrainsMono-Regular.ttf", 16)
        dpg.bind_font(default_font)


    with dpg.window(label="Executable Map Tool", width=900, height=700, pos=(0,0)) as root:

        # Where? button and label above tabs
        with dpg.group(horizontal=True):
            dpg.add_button(label="Where?", callback=lambda: dpg.show_item("where_popup"))
            where_label_id = dpg.add_text("", tag="where_label")

        # Tabs container
        with dpg.tab_bar(tag="main_tabs") as tabs:

            sections_ui = SectionsUI(store, change_callback=lambda: save_project(store))
            modules_ui  = ModulesNyNameUI(store, change_callback=lambda: save_project(store))
            inverted_ui = ModulesBySectionUI(store, change_callback=lambda: save_project(store))
            reports_ui  = ReportsUI(store)

            # Build UI
            sections_ui.draw(tabs)
            modules_ui.draw(tabs)
            inverted_ui.draw(tabs)
            reports_ui.draw(tabs)

            dpg.set_item_callback("main_tabs", on_tab_change)

        # Create the Where? popup
        with dpg.window(tag="where_popup", modal=True, show=False, autosize=True, label="Where is this address?"):
            where_input_id = dpg.add_input_text(label="Address (hex)")
            with dpg.group(horizontal=True):
                dpg.add_button(label="OK", callback=lambda: where_ok(store, where_input_id, where_label_id))
                dpg.add_button(label="Cancel", callback=lambda: dpg.hide_item("where_popup"))

        # After building windows, force UI to refresh from loaded JSON
        sections_ui.refresh()
        modules_ui.refresh_modules()
        inverted_ui.refresh_sections()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
