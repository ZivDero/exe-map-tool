import dearpygui.dearpygui as dpg
from models import ModuleRange
from ui.ui_utils import parse_hex

class ModulesBySectionUI:
    def __init__(self, store, change_callback):
        self.store = store
        self.on_change = change_callback
        self.selected_section_id = None
        self.last_selected_module = None

        # POPUP INTERNALS
        self.range_popup_id             = "inverted_range_popup"
        self.error_popup_id             = "inverted_error_popup"

        self.range_module_combo = None
        self.range_start_input = None
        self.range_end_input   = None

        self.editing_range = None  # the ModuleRange being edited

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

        with dpg.tab(label="Modules by Section", parent=parent):

            with dpg.group(horizontal=True):

                # ---------------- LEFT (Sections)
                with dpg.child_window(width=240, height=500):
                    dpg.add_text("Sections")
                    self.section_list_id = dpg.add_listbox(
                        items=[],
                        num_items=22,  # fills entire height available
                        width=-1,
                        callback=self._select_section
                    )

                # ---------------- RIGHT (Ranges)
                with dpg.child_window(width=-1, height=500):
                    dpg.add_text("Ranges")

                    with dpg.table(header_row=True, resizable=True,
                                   policy=dpg.mvTable_SizingStretchProp) as t:
                        self.range_table_id = t
                        dpg.add_table_column(label="Module")
                        dpg.add_table_column(label="Start")
                        dpg.add_table_column(label="End")
                        dpg.add_table_column(label="Size")
                        dpg.add_table_column(label="Locked")     # <<< for real rows
                        dpg.add_table_column(label="Edit")
                        dpg.add_table_column(label="Delete")

                    dpg.add_spacer(height=6)
                    dpg.add_button(label="Add Range",
                                   callback=self._add_range_clicked)

        self.refresh_sections()

    # ========================================================= POPUPS

    def _create_popups(self):

        # RANGE popup --------------------------------------------
        with dpg.window(tag=self.range_popup_id, modal=False,
                        show=False, autosize=True, label="Range Editor"):

            self.range_module_combo = dpg.add_combo(label="Module", callback=self._range_module_changed)
            self.range_start_input = dpg.add_input_text(label="Start (hex)", callback=self._recalc_from_start)
            self.range_end_input   = dpg.add_input_text(label="End (hex)", callback=self._recalc_from_end)
            self.range_size_input  = dpg.add_input_text(label="Size (hex)", callback=self._recalc_from_size)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save",   callback=self._save_range)
                dpg.add_button(label="Cancel", callback=lambda s,a,u: dpg.hide_item(self.range_popup_id))

        # ERROR popup --------------------------------------------
        with dpg.window(tag=self.error_popup_id, modal=True,
                        autosize=True, show=False, label="Error"):
            self.error_text_id = dpg.add_text("")
            dpg.add_button(label="OK", callback=lambda s,a,u: dpg.hide_item(self.error_popup_id))

    # ============================ RANGE MATH ============================

    def _to_int(self, v):
        v = str(v).strip()
        if v.lower().startswith("0x"): v = v[2:]
        if v.endswith(("h", "H")): v = v[:-1]
        return int(v, 16)

    def _hx(self, v):
        if v < 0:
            return f"-0x{abs(v):X}"
        return f"0x{v:X}"

    def _recalc_from_start(self, s, a, u=None):
        try:
            st = self._to_int(dpg.get_value(self.range_start_input))
            en = self._to_int(dpg.get_value(self.range_end_input))
            dpg.set_value(self.range_size_input, self._hx(en - st))
        except:
            pass

    def _recalc_from_end(self, s, a, u=None):
        try:
            st = self._to_int(dpg.get_value(self.range_start_input))
            en = self._to_int(dpg.get_value(self.range_end_input))
            dpg.set_value(self.range_size_input, self._hx(en - st))
        except:
            pass

    def _recalc_from_size(self, s, a, u=None):
        try:
            st = self._to_int(dpg.get_value(self.range_start_input))
            sz = self._to_int(dpg.get_value(self.range_size_input))
            dpg.set_value(self.range_end_input, self._hx(st + sz))
        except:
            pass

    def _range_module_changed(self, sender, app_data, user_data=None):
        selected_name = app_data
        self.last_selected_module = selected_name

    # ========================================================= SECTION MGMT

    def refresh_sections(self):
        names = [s.name for s in self.store.project.sections.values()]
        dpg.configure_item(self.section_list_id, items=names)

        # auto-select something if nothing is selected
        if self.selected_section_id not in self.store.project.sections:
            if names:
                first = next(iter(self.store.project.sections.values()))
                self.selected_section_id = first.id
                dpg.set_value(self.section_list_id, first.name)

        self.refresh_ranges()

    def _select_section(self, s, name, u):
        # listbox returns name
        for sec in self.store.project.sections.values():
            if sec.name == name:
                self.selected_section_id = sec.id
                break
        self.refresh_ranges()

    # ========================================================= RANGES

    def refresh_ranges(self):
        rows = dpg.get_item_children(self.range_table_id).get(1,[])
        for r in rows: dpg.delete_item(r)

        if not self.selected_section_id: return

        sec = self.store.project.sections[self.selected_section_id]

        # Collect all ranges in this section, with their modules
        ranges_with_modules = []
        for mod in self.store.project.modules.values():
            for rng in mod.ranges:
                if rng.section_id == sec.id:
                    ranges_with_modules.append((mod, rng))

        # Sort ranges by start
        ranges_with_modules.sort(key=lambda x: x[1].start)

        # Collect all items to display: ranges and gaps
        items = []

        # Add real ranges
        for mod, rng in ranges_with_modules:
            items.append((rng.start, 'range', mod, rng))

        # Compute gaps and add them
        used = [(rng.start, rng.end) for mod, rng in ranges_with_modules]
        used.sort()
        cursor = sec.start
        for s, e in used:
            if s > cursor:
                gap_start = cursor
                gap_end = s
                gap_size = gap_end - gap_start
                items.append((gap_start, 'gap', gap_start, gap_end, gap_size))
            cursor = max(cursor, e)

        if cursor < sec.end:
            gap_start = cursor
            gap_end = sec.end
            gap_size = gap_end - gap_start
            items.append((gap_start, 'gap', gap_start, gap_end, gap_size))

        # Sort all items by start
        items.sort(key=lambda x: x[0])

        # Add rows in sorted order
        for item in items:
            if item[1] == 'range':
                mod, rng = item[2], item[3]
                with dpg.table_row(parent=self.range_table_id):
                    # module name + values
                    txt_mod = dpg.add_text(mod.name)
                    txt_start = dpg.add_text(f"0x{rng.start:X}")
                    txt_end = dpg.add_text(f"0x{rng.end:X}")
                    txt_size = dpg.add_text(f"0x{rng.size:X}")

                    # LOCK TOGGLE
                    chk_locked = dpg.add_checkbox(label="", default_value=rng.locked,
                                                  user_data=(mod, rng), callback=self._toggle_range_lock)

                    btn_edit = dpg.add_button(label="Edit", user_data=(mod, rng),
                                              enabled=not rng.locked,
                                              callback=self._edit_range_clicked)

                    btn_delete = dpg.add_button(label="Delete", user_data=(mod, rng),
                                                enabled=not rng.locked,
                                                callback=self._delete_range_clicked)

                    # color text if locked
                    text_items = [txt_mod, txt_start, txt_end, txt_size]
                    if rng.locked:
                        for item in text_items:
                            dpg.bind_item_theme(item, self.locked_text_theme)
                    else:
                        for item in text_items:
                            dpg.bind_item_theme(item, 0)
            elif item[1] == 'gap':
                gap_start, gap_end, gap_size = item[2], item[3], item[4]
                with dpg.table_row(parent=self.range_table_id):
                    dpg.add_text("Gap")
                    dpg.add_text(f"0x{gap_start:X}")
                    dpg.add_text(f"0x{gap_end:X}")
                    dpg.add_text(f"0x{gap_size:X}")
                    dpg.add_text("")  # locked
                    dpg.add_button(label="Add", user_data=gap_start, callback=self._add_range_for_gap)
                    dpg.add_text("")  # delete

    # ------------------------- ADD RANGE

    def _add_range_clicked(self):
        if not self.selected_section_id: return self._err("Select section first")
        sec = self.store.project.sections[self.selected_section_id]

        # Filter modules that don't have range in this section
        available_mods = [m for m in self.store.project.modules.values() if not any(r.section_id == sec.id for r in m.ranges)]
        if not available_mods: return self._err("All modules already have ranges in this section")

        mod_names = [m.name for m in available_mods]
        if self.last_selected_module:
            if self.last_selected_module in mod_names:
                selected = self.last_selected_module
            else:
                sorted_names = sorted(mod_names)
                candidates = [n for n in sorted_names if n > self.last_selected_module]
                selected = candidates[0] if candidates else mod_names[0]
        else:
            selected = mod_names[0]
        dpg.configure_item(self.range_module_combo, items=mod_names)
        dpg.set_value(self.range_module_combo, selected)
        dpg.set_value(self.range_start_input, "")
        dpg.set_value(self.range_end_input, "")
        dpg.set_value(self.range_size_input, "")
        self.editing_range = None  # ADDING NEW
        dpg.show_item(self.range_popup_id)

    # ------------------------- ADD RANGE FOR GAP

    def _add_range_for_gap(self, sender, app_data, gap_start):
        self._add_range_clicked()
        dpg.set_value(self.range_start_input, f"0x{gap_start:X}")

    # ------------------------- EDIT RANGE

    def _edit_range_clicked(self, sender, app_data, user_data):
        mod, rng = user_data
        if rng is None:
            return

        # Module combo
        mod_names = [m.name for m in self.store.project.modules.values()]
        dpg.configure_item(self.range_module_combo, items=mod_names)
        dpg.set_value(self.range_module_combo, mod.name)
        self.last_selected_module = mod.name

        dpg.set_value(self.range_start_input, f"0x{rng.start:X}")
        dpg.set_value(self.range_end_input, f"0x{rng.end:X}")
        dpg.set_value(self.range_size_input, self._hx(rng.end - rng.start))

        self.editing_range = rng
        dpg.show_item(self.range_popup_id)

    # ------------------------- SAVE RANGE

    def _save_range(self):
        mod_name = dpg.get_value(self.range_module_combo)
        target_mod = next(m for m in self.store.project.modules.values() if m.name == mod_name)

        try:
            start = parse_hex(dpg.get_value(self.range_start_input))
            end   = parse_hex(dpg.get_value(self.range_end_input))
        except ValueError as e: return self._err(str(e))

        if start >= end: return self._err("Start < End required")

        sec = self.store.project.sections[self.selected_section_id]

        # check bounds
        if not(sec.start <= start < end <= sec.end):
            return self._err("Range outside section bounds")

        if self.editing_range is None:
            # adding new
            target_mod.ranges.append(ModuleRange(
                section_id=sec.id, start=start, end=end, locked=False
            ))
        else:
            # editing existing
            self.editing_range.start = start
            self.editing_range.end = end
            # If module changed, need to move the range
            if self.editing_range not in target_mod.ranges:
                # Find current module and remove
                for m in self.store.project.modules.values():
                    if self.editing_range in m.ranges:
                        m.ranges.remove(self.editing_range)
                        break
                target_mod.ranges.append(self.editing_range)

        self.on_change()
        dpg.hide_item(self.range_popup_id)
        self.last_selected_module = target_mod.name
        self.refresh_ranges()

    # ------------------- DELETE RANGE

    def _delete_range_clicked(self, sender, app_data, user_data):
        mod, rng = user_data
        if rng is None:
            return

        try:
            mod.ranges.remove(rng)
        except ValueError:
            return

        self.on_change()
        self.refresh_ranges()

    # ------------------- LOCK RANGE

    def _toggle_range_lock(self, s, new_state, user_data):
        mod, rng = user_data
        rng.locked = bool(new_state)
        self.on_change()
        self.refresh_ranges()

    # ========================================================= UTIL

    def _err(self,msg):
        dpg.set_value(self.error_text_id,msg)
        dpg.show_item(self.error_popup_id)