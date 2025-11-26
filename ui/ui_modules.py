import dearpygui.dearpygui as dpg
from models import ModuleRange   # must include .locked: bool default = False
from ui.ui_utils import parse_hex

class ModulesUI:
    def __init__(self, store, change_callback):
        self.store = store
        self.on_change = change_callback
        self.selected_module_id = None

        # POPUP INTERNALS
        self.module_popup_id     = "module_popup"
        self.range_popup_id      = "range_popup"
        self.error_popup_id      = "module_error_popup"

        self.module_name_input   = None
        self.range_sec_combo     = None
        self.range_start_input   = None
        self.range_end_input     = None

        self.editing_new_module  = False
        self.editing_range_old_sec = None  # None = adding new

        # THEMES -----------------------------
        self.locked_text_theme = self._create_locked_text_theme()

    # ========================================================= THEMES

    def _create_locked_text_theme(self):
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 200, 0, 255))
        return t

    # ========================================================= UI BUILD

    def draw(self, parent):
        self._create_popups()

        with dpg.tab(label="Modules", parent=parent):

            with dpg.group(horizontal=True):                     # <--- ADD/RENAME/DELETE grouped
                dpg.add_button(label="Add",    callback=self._add_module_clicked)
                dpg.add_button(label="Rename", callback=self._rename_module_clicked)
                dpg.add_button(label="Delete", callback=self._delete_module_clicked)

            dpg.add_spacer(height=6)

            with dpg.group(horizontal=True):

                # ---------------- LEFT (Modules)
                with dpg.child_window(width=240, height=500):
                    dpg.add_text("Modules")
                    self.module_list_id = dpg.add_listbox(
                        items=[],
                        num_items=22,  # fills entire height available
                        width=-1,
                        callback=self._select_module
                    )

                # ---------------- RIGHT (Ranges)
                with dpg.child_window(width=-1, height=500):
                    dpg.add_text("Ranges")

                    with dpg.table(header_row=True, resizable=True,
                                   policy=dpg.mvTable_SizingStretchProp) as t:
                        self.range_table_id = t
                        dpg.add_table_column(label="Section")
                        dpg.add_table_column(label="Start")
                        dpg.add_table_column(label="End")
                        dpg.add_table_column(label="Size")
                        dpg.add_table_column(label="Locked")     # <<< NEW
                        dpg.add_table_column(label="Edit")
                        dpg.add_table_column(label="Delete")

                    dpg.add_spacer(height=6)
                    dpg.add_button(label="Add Range",
                                   callback=self._add_range_clicked)

        self.refresh_modules()

    # ========================================================= POPUPS

    def _create_popups(self):

        # MODULE popup -------------------------------------------
        with dpg.window(tag=self.module_popup_id, modal=True,
                        show=False, autosize=True, label="Module Editor"):
            self.module_name_input = dpg.add_input_text(label="Module Name")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save",   callback=self._save_module)
                dpg.add_button(label="Cancel", callback=lambda s,a,u: dpg.hide_item(self.module_popup_id))

        # RANGE popup --------------------------------------------
        with dpg.window(tag=self.range_popup_id, modal=True,
                        show=False, autosize=True, label="Range Editor"):

            self.range_sec_combo   = dpg.add_combo(label="Section")
            self.range_start_input = dpg.add_input_text(label="Start (hex)")
            self.range_end_input   = dpg.add_input_text(label="End (hex)")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save",   callback=self._save_range)
                dpg.add_button(label="Cancel", callback=lambda s,a,u: dpg.hide_item(self.range_popup_id))

        # ERROR popup --------------------------------------------
        with dpg.window(tag=self.error_popup_id, modal=True,
                        autosize=True, show=False, label="Error"):
            self.error_text_id = dpg.add_text("")
            dpg.add_button(label="OK", callback=lambda s,a,u: dpg.hide_item(self.error_popup_id))

    # ========================================================= MODULE MGMT

    def refresh_modules(self):
        names = [m.name for m in self.store.project.modules.values()]
        dpg.configure_item(self.module_list_id, items=names)

        # auto-select something if nothing is selected
        if self.selected_module_id not in self.store.project.modules:
            if names:
                first = next(iter(self.store.project.modules.values()))
                self.selected_module_id = first.id
                dpg.set_value(self.module_list_id, first.name)

        self.refresh_ranges()

    def _select_module(self, s, name, u):
        # listbox returns name (DPG 2.x)
        for m in self.store.project.modules.values():
            if m.name == name:
                self.selected_module_id = m.id
                break
        self.refresh_ranges()

    def _add_module_clicked(self):
        self.editing_new_module = True
        dpg.set_value(self.module_name_input, "")
        dpg.show_item(self.module_popup_id)

    def _rename_module_clicked(self):
        if not self.selected_module_id: return self._err("No module selected")
        m = self.store.project.modules[self.selected_module_id]
        self.editing_new_module = False
        dpg.set_value(self.module_name_input, m.name)
        dpg.show_item(self.module_popup_id)

    def _delete_module_clicked(self):
        if not self.selected_module_id: return self._err("No module selected")
        self.store.delete_module(self.selected_module_id)
        self.selected_module_id = None
        self.on_change()
        self.refresh_modules()

    def _save_module(self, sender=None, app_data=None, user_data=None):
        name = dpg.get_value(self.module_name_input).strip()
        if not name:
            return self._err("Module name cannot be empty.")

        # ----- enforce unique names -----
        for m in self.store.project.modules.values():
            if m.name.lower() == name.lower():
                # allowed only if renaming this same module
                if not self.editing_new_module and m.id == self.selected_module_id:
                    break  # renaming to same name is fine
                return self._err(f"Module '{name}' already exists.")

        # ----- create or rename -----
        if self.editing_new_module:
            mod = self.store.add_module(name)
            self.selected_module_id = mod.id  # auto-select
        else:
            self.store.update_module(self.selected_module_id, name)

        # ----- finalize -----
        self.on_change()
        dpg.hide_item(self.module_popup_id)
        self.refresh_modules()

    # ========================================================= RANGES

    def refresh_ranges(self):
        rows = dpg.get_item_children(self.range_table_id).get(1,[])
        for r in rows: dpg.delete_item(r)

        if not self.selected_module_id: return

        mod = self.store.project.modules[self.selected_module_id]

        # <<<<<<<<<<<<<<<<<<<<<< SORT BY START >>>>>>>>>>>>>>>>>>>>>>
        ranges = sorted(mod.ranges, key=lambda r: r.start)

        for rng in ranges:
            sec = self.store.project.sections[rng.section_id]
            with dpg.table_row(parent=self.range_table_id) as row:

                # name + values
                txt_sec = dpg.add_text(sec.name)
                txt_start = dpg.add_text(f"0x{rng.start:X}")
                txt_end = dpg.add_text(f"0x{rng.end:X}")
                txt_size = dpg.add_text(f"0x{rng.size:X}")

                # LOCK TOGGLE
                dpg.add_checkbox(label="", default_value=rng.locked,
                                 user_data=rng, callback=self._toggle_range_lock)

                dpg.add_button(label="Edit", user_data=rng,
                               enabled=not rng.locked,
                               callback=self._edit_range_clicked)

                dpg.add_button(label="Delete", user_data=rng,
                               enabled=not rng.locked,
                               callback=self._delete_range_clicked)

                # color text if locked
                text_items = [txt_sec, txt_start, txt_end, txt_size]
                if rng.locked:
                    for item in text_items:
                        dpg.bind_item_theme(item, self.locked_text_theme)
                else:
                    # ensure previously themed items get reset if range was unlocked
                    for item in text_items:
                        dpg.bind_item_theme(item, 0)

    # ------------------------- ADD RANGE

    def _add_range_clicked(self):
        if not self.selected_module_id: return self._err("Select module first")
        if not self.store.project.sections: return self._err("No sections exist")

        sec_names = [s.name for s in self.store.project.sections.values()]
        dpg.configure_item(self.range_sec_combo, items=sec_names)
        dpg.set_value(self.range_sec_combo, sec_names[0])
        dpg.set_value(self.range_start_input, "")
        dpg.set_value(self.range_end_input, "")
        self.editing_range_old_sec = None  # NEW RANGE
        dpg.show_item(self.range_popup_id)

    # ------------------------- EDIT RANGE

    def _edit_range_clicked(self, sender, app_data, rng: ModuleRange):
        # rng comes from user_data, NOT app_data
        if rng is None:
            return

        # Make sure we operate on the currently selected module
        mod = self.store.project.modules[self.selected_module_id]

        # Section combo content
        sections = list(self.store.project.sections.values())
        sec_names = [s.name for s in sections]

        # Find current section
        sec = self.store.project.sections[rng.section_id]

        dpg.configure_item(self.range_sec_combo, items=sec_names)
        dpg.set_value(self.range_sec_combo, sec.name)
        dpg.set_value(self.range_start_input, f"0x{rng.start:X}")
        dpg.set_value(self.range_end_input, f"0x{rng.end:X}")

        self.editing_range_old_sec = rng.section_id
        dpg.show_item(self.range_popup_id)

    # ------------------------- SAVE RANGE

    def _save_range(self):
        sec_name = dpg.get_value(self.range_sec_combo)
        target = next(s for s in self.store.project.sections.values() if s.name==sec_name)

        try:
            start = parse_hex(dpg.get_value(self.range_start_input))
            end   = parse_hex(dpg.get_value(self.range_end_input))
        except ValueError as e: return self._err(str(e))

        if start >= end: return self._err("Start < End required")

        # check bounds
        if not(target.start <= start < end <= target.end):
            return self._err("Range outside section bounds")

        mod = self.store.project.modules[self.selected_module_id]

        # adding new
        if self.editing_range_old_sec is None:
            for r in mod.ranges:
                if r.section_id == target.id:
                    return self._err("Module already has range in this section")

            mod.ranges.append(ModuleRange(
                section_id=target.id, start=start, end=end, locked=False
            ))

        # editing existing
        else:
            rng = next(r for r in mod.ranges if r.section_id == self.editing_range_old_sec)
            rng.section_id = target.id
            rng.start = start
            rng.end = end

        self.on_change()
        dpg.hide_item(self.range_popup_id)
        self.refresh_ranges()

    # ------------------- DELETE RANGE

    def _delete_range_clicked(self, sender, app_data, rng: ModuleRange):
        if not self.selected_module_id or rng is None:
            return

        mod = self.store.project.modules[self.selected_module_id]
        try:
            mod.ranges.remove(rng)
        except ValueError:
            # In case something got out of sync, bail quietly instead of crashing
            return

        self.on_change()
        self.refresh_ranges()

    # ------------------- LOCK RANGE

    def _toggle_range_lock(self, s, new_state, rng):
        rng.locked = bool(new_state)
        self.on_change()
        self.refresh_ranges()

    # ========================================================= UTIL

    def _err(self,msg):
        dpg.set_value(self.error_text_id,msg)
        dpg.show_item(self.error_popup_id)
