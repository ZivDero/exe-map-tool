import dearpygui.dearpygui as dpg

HOLE_COLOR = (255, 255, 128, 255)  # soft yellow highlight
OVERLAP_COLOR = (255, 128, 128, 255)  # soft red


class ReportsUI:
    def __init__(self, store):
        self.store = store

        self.table_sections = None  # Section holes
        self.table_modules = None  # Module holes inside sections
        self.table_overlap = None  # Module overlap claims

    # ================================================================== BUILD UI

    def draw(self, tab_parent):
        with dpg.tab(label="Reports", parent=tab_parent):
            dpg.add_text("Executable Holes (No Section Covers These Ranges)")
            with dpg.table(header_row=True, resizable=True,
                           policy=dpg.mvTable_SizingStretchProp) as t1:
                self.table_sections = t1
                dpg.add_table_column(label="Start")
                dpg.add_table_column(label="End")
                dpg.add_table_column(label="Size")

            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            dpg.add_text("Module Holes (Sections Not Fully Mapped by Modules)")
            with dpg.table(header_row=True, resizable=True,
                           policy=dpg.mvTable_SizingStretchProp) as t2:
                self.table_modules = t2
                dpg.add_table_column(label="Section")
                dpg.add_table_column(label="Start")
                dpg.add_table_column(label="End")
                dpg.add_table_column(label="Size")

            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            dpg.add_text("Module Overlaps (Multiple Modules Claim Same Space)")
            with dpg.table(header_row=True, resizable=True,
                           policy=dpg.mvTable_SizingStretchProp) as t3:
                self.table_overlap = t3
                dpg.add_table_column(label="Section")
                dpg.add_table_column(label="Module A")
                dpg.add_table_column(label="A Start")
                dpg.add_table_column(label="A End")
                dpg.add_table_column(label="Module B")
                dpg.add_table_column(label="B Start")
                dpg.add_table_column(label="B End")
                dpg.add_table_column(label="Overlap Size")

        self.refresh()

    # ================================================================== REFRESH

    def refresh(self):
        self._refresh_section_holes()
        self._refresh_module_holes()
        self._refresh_overlaps()

    # ================================================================== HOLES: EXECUTABLE

    def _refresh_section_holes(self):
        children = dpg.get_item_children(self.table_sections)
        for row in children.get(1, []):
            dpg.delete_item(row)

        for start, end in self.store.compute_section_holes():
            size = end - start
            with dpg.table_row(parent=self.table_sections):
                id1 = dpg.add_text(f"0x{start:X}")
                id2 = dpg.add_text(f"0x{end:X}")
                id3 = dpg.add_text(f"0x{size:X}")

                # highlight
                dpg.bind_item_theme(id1, self._yellow())
                dpg.bind_item_theme(id2, self._yellow())
                dpg.bind_item_theme(id3, self._yellow())

    # ================================================================== HOLES: MODULE

    def _refresh_module_holes(self):
        children = dpg.get_item_children(self.table_modules)
        for row in children.get(1, []):
            dpg.delete_item(row)

        for sec_name, start, end in self.store.compute_module_holes():
            size = end - start
            with dpg.table_row(parent=self.table_modules):
                id0 = dpg.add_text(sec_name)
                id1 = dpg.add_text(f"0x{start:X}")
                id2 = dpg.add_text(f"0x{end:X}")
                id3 = dpg.add_text(f"0x{size:X}")

                dpg.bind_item_theme(id0, self._yellow())
                dpg.bind_item_theme(id1, self._yellow())
                dpg.bind_item_theme(id2, self._yellow())
                dpg.bind_item_theme(id3, self._yellow())

    # ================================================================== OVERLAPS

    def _refresh_overlaps(self):
        children = dpg.get_item_children(self.table_overlap)
        for row in children.get(1, []):
            dpg.delete_item(row)

        for A, B, rA, rB, size in self.store.compute_module_overlaps():
            sec = self.store.project.sections[rA.section_id].name

            with dpg.table_row(parent=self.table_overlap):
                id0 = dpg.add_text(sec)
                id1 = dpg.add_text(A.name)
                id2 = dpg.add_text(f"0x{rA.start:X}")
                id3 = dpg.add_text(f"0x{rA.end:X}")
                id4 = dpg.add_text(B.name)
                id5 = dpg.add_text(f"0x{rB.start:X}")
                id6 = dpg.add_text(f"0x{rB.end:X}")
                id7 = dpg.add_text(f"0x{size:X}")

                # red mark
                for item in (id0, id1, id2, id3, id4, id5, id6, id7):
                    dpg.bind_item_theme(item, self._red())

    # ================================================================== THEMES

    def _yellow(self):
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, HOLE_COLOR)
        return t

    def _red(self):
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, OVERLAP_COLOR)
        return t
