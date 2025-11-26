import dearpygui.dearpygui as dpg
from ui.ui_theme import LOCKED_COLOR
from ui.ui_utils import parse_hex


class SectionsUI:
    def __init__(self, store, change_callback):
        self.store = store
        self.on_change = change_callback

        self.table_id = None

        # Section edit popup
        self.current_edit_sec_id = None
        self.edit_popup_id = None
        self.edit_name_id = None
        self.edit_start_id = None
        self.edit_end_id = None

        # Section add popup
        self.add_popup_id = None
        self.add_name_id = None
        self.add_start_id = None
        self.add_end_id = None

        # EXE RANGE popup
        self.exe_popup_id = None
        self.exe_start_id = None
        self.exe_end_id = None

        # error popup
        self.error_popup_id = None
        self.error_text_id = None

    # ==================================================================== UI BUILD

    def draw(self, tab_parent):

        with dpg.tab(label="Sections", parent=tab_parent):

            with dpg.group(horizontal=True):
                dpg.add_button(label="Add Section", callback=self._open_add_popup)
                dpg.add_button(label="Set Executable Range", callback=self._open_exe_popup)
                dpg.add_text("", tag="exe_range_preview")

            dpg.add_spacer(height=6)

            with dpg.table(header_row=True,
                           resizable=True,
                           policy=dpg.mvTable_SizingStretchProp) as table:
                self.table_id = table

                dpg.add_table_column(label="Name")
                dpg.add_table_column(label="Start")
                dpg.add_table_column(label="End")
                dpg.add_table_column(label="Size")
                dpg.add_table_column(label="Locked")
                dpg.add_table_column(label="Edit")
                dpg.add_table_column(label="Delete")

        self._create_edit_popup()
        self._create_add_popup()
        self._create_exe_popup()           # <-- NEW
        self._create_error_popup()

        self.refresh()

    # ==================================================================== REFRESH

    def refresh(self):
        p = self.store.project
        if p.exe_start is not None and p.exe_end is not None:
            dpg.set_value("exe_range_preview", f"[ EXE: 0x{p.exe_start:X} - 0x{p.exe_end:X} ]")
        else:
            dpg.set_value("exe_range_preview", "[ <no executable range set> ]")

        children = dpg.get_item_children(self.table_id)
        for row in children.get(1, []):
            dpg.delete_item(row)

        # sort by start always
        sections = sorted(
            self.store.project.sections.values(),
            key=lambda s: s.start
        )

        for sec in sections:
            with dpg.table_row(parent=self.table_id):

                dpg.add_text(sec.name)
                dpg.add_text(f"0x{sec.start:X}")
                dpg.add_text(f"0x{sec.end:X}")
                dpg.add_text(f"0x{sec.size:X}")

                dpg.add_checkbox(
                    label="",
                    default_value=sec.locked,
                    user_data=sec.id,
                    callback=self.toggle_lock
                )

                dpg.add_button(
                    label="Edit", user_data=sec.id,
                    callback=self._open_edit_popup,
                    enabled=not sec.locked
                )

                dpg.add_button(
                    label="Delete", user_data=sec.id,
                    callback=self._delete_section_confirm,
                    enabled=not sec.locked
                )

    # ==================================================================== POPUPS

    def _create_edit_popup(self):
        with dpg.window(
            tag="section_edit_popup", modal=True, show=False,
            no_collapse=True, autosize=True, label="Edit Section"
        ) as popup:

            self.edit_popup_id = popup
            self.edit_name_id  = dpg.add_input_text(label="Name")
            self.edit_start_id = dpg.add_input_text(label="Start (hex)")
            self.edit_end_id   = dpg.add_input_text(label="End (hex)")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=self._on_save_edit)
                dpg.add_button(label="Cancel", callback=self._on_cancel_edit)

    def _create_add_popup(self):
        with dpg.window(
            tag="section_add_popup", modal=True, show=False,
            no_collapse=True, autosize=True, label="Create Section"
        ) as popup:

            self.add_popup_id = popup
            self.add_name_id  = dpg.add_input_text(label="Name")
            self.add_start_id = dpg.add_input_text(label="Start (hex)")
            self.add_end_id   = dpg.add_input_text(label="End (hex)")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Create", callback=self._on_create_section)
                dpg.add_button(label="Cancel", callback=self._on_cancel_add)

    # -------------------- NEW EXECUTABLE RANGE POPUP

    def _create_exe_popup(self):
        with dpg.window(
            tag="exe_range_popup", modal=True, show=False,
            no_collapse=True, autosize=True, label="Executable Range"
        ) as popup:

            self.exe_popup_id  = popup
            self.exe_start_id = dpg.add_input_text(label="Start (hex)")
            self.exe_end_id   = dpg.add_input_text(label="End (hex)")

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save",   callback=self._save_exe_range)
                dpg.add_button(label="Cancel", callback=lambda:s_dpg_hide(self.exe_popup_id))

    def _create_error_popup(self):
        with dpg.window(
            tag="section_error_popup", modal=False, show=False,
            no_collapse=True, autosize=True, label="Error"
        ) as popup:

            self.error_popup_id = popup
            self.error_text_id  = dpg.add_text("")
            dpg.add_spacer(height=6)
            dpg.add_button(label="OK", callback=self._hide_error_popup)

    # ==================================================================== SECTION EDIT

    def _open_edit_popup(self, sender, app_data, sec_id):
        self.current_edit_sec_id = sec_id
        sec = self.store.project.sections[sec_id]

        dpg.set_value(self.edit_name_id, sec.name)
        dpg.set_value(self.edit_start_id, f"0x{sec.start:X}")
        dpg.set_value(self.edit_end_id, f"0x{sec.end:X}")

        dpg.configure_item(self.edit_popup_id, show=True)

    def _on_cancel_edit(self, *args):
        self.current_edit_sec_id = None
        dpg.configure_item(self.edit_popup_id, show=False)

    def _on_save_edit(self, *args):
        name = dpg.get_value(self.edit_name_id)
        start = parse_hex(dpg.get_value(self.edit_start_id))
        end = parse_hex(dpg.get_value(self.edit_end_id))

        try:
            self.store.update_section(self.current_edit_sec_id, name, start, end)

        except Exception as e:
            self._show_error(str(e))
            return

        self.current_edit_sec_id = None
        self.on_change()
        self.refresh()
        dpg.configure_item(self.edit_popup_id, show=False)

    # ==================================================================== SECTION ADD

    def _open_add_popup(self, *args):
        dpg.set_value(self.add_name_id, "")
        dpg.set_value(self.add_start_id, "")
        dpg.set_value(self.add_end_id, "")
        dpg.configure_item(self.add_popup_id, show=True)

    def _on_cancel_add(self, *args):
        dpg.configure_item(self.add_popup_id, show=False)

    def _on_create_section(self, *args):
        name  = dpg.get_value(self.add_name_id)
        start = parse_hex(dpg.get_value(self.add_start_id))
        end   = parse_hex(dpg.get_value(self.add_end_id))

        try:
            self.store.add_section(name, start, end)
        except Exception as e:
            self._show_error(str(e))
            return

        self.on_change()
        self.refresh()
        dpg.configure_item(self.add_popup_id, show=False)

    # ==================================================================== EXE RANGE LOGIC (NEW)

    def _open_exe_popup(self, *args):
        p = self.store.project
        dpg.set_value(self.exe_start_id, f"0x{p.exe_start:X}" if p.exe_start is not None else "")
        dpg.set_value(self.exe_end_id, f"0x{p.exe_end:X}" if p.exe_end is not None else "")
        dpg.configure_item(self.exe_popup_id, show=True)

    def _save_exe_range(self, *args):
        try:
            start = parse_hex(dpg.get_value(self.exe_start_id))
            end = parse_hex(dpg.get_value(self.exe_end_id))
        except:
            return self._show_error("Invalid hex input.")

        if start >= end:
            return self._show_error("Start must be < End.")

        # --- NEW: ensure exe range contains all sections
        for sec in self.store.project.sections.values():
            if sec.start < start or sec.end > end:
                return self._show_error(
                    f"New EXE range does not cover existing section '{sec.name}'."
                )

        if not self.store.set_executable_range(start, end):
            return self._show_error("Failed to set executable range.")

        self.on_change()
        dpg.configure_item(self.exe_popup_id, show=False)
        self.refresh()  # update preview text

    # ==================================================================== DELETE

    def _delete_section_confirm(self, sender, app_data, sec_id):
        self.store.delete_section(sec_id)
        self.on_change()
        self.refresh()

    # ==================================================================== ERROR + UTILS

    def _show_error(self, msg):
        dpg.set_value(self.error_text_id, msg)
        dpg.configure_item(self.error_popup_id, show=True)
        dpg.focus_item(self.error_popup_id)

    def _hide_error_popup(self, *args):
        dpg.configure_item(self.error_popup_id, show=False)

    def toggle_lock(self, sender, locked, sec_id):
        self.store.set_section_lock(sec_id, bool(locked))
        self.on_change()
        self.refresh()


def s_dpg_hide(id): dpg.configure_item(id, show=False)
