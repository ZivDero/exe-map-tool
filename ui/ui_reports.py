import dearpygui.dearpygui as dpg

# ============================================================
# BAR COLORS
# ============================================================
COLOR_NOSEC     = (40,40,40,255)       # EXE region not in any section
COLOR_SECTION   = (80,80,180,255)      # Section exists but unknown module state
COLOR_HOLE      = (240,240,120,255)    # Inside section but no module owns area
COLOR_OVERLAP   = (255,70,70,255)      # Red conflict
COLOR_OK        = (70,140,255,255)     # Section + module coverage

HOLE_COLOR      = (255,255,128,255)
OVERLAP_COLOR   = (255,128,128,255)



class ReportsUI:
    def __init__(self, store):
        self.store = store
        self.bar = None

        self.table_sections = None
        self.table_modules = None
        self.table_overlap = None


    # ================================================================== BUILD UI

    def draw(self, tab_parent):
        with dpg.tab(label="Reports", parent=tab_parent):

            dpg.add_text("Executable Visual Map")
            dpg.add_spacer(height=4)

            # BAR
            self.bar = dpg.add_drawlist(width=900, height=55)

            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # ==== 1) SECTION HOLES (NO SECTION) ====
            with dpg.group(horizontal=True):
                dpg.add_text("Executable Holes (No section covers this area):")
                dpg.add_button(label="Export CSV",
                               callback=lambda: self._export_table_csv(self.table_sections, "section_holes.csv"))

            with dpg.table(header_row=True, resizable=True,
                           policy=dpg.mvTable_SizingStretchProp) as t1:
                self.table_sections = t1
                dpg.add_table_column(label="Start")
                dpg.add_table_column(label="End")
                dpg.add_table_column(label="Size")

            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # ==== 2) MODULE HOLES ====
            with dpg.group(horizontal=True):
                dpg.add_text("Executable Holes (No section covers this area):")
                dpg.add_button(label="Export CSV",
                               callback=lambda: self._export_table_csv(self.table_sections, "section_holes.csv"))

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

            # ==== 3) OVERLAP ====
            with dpg.group(horizontal=True):
                dpg.add_text("Module Overlap Conflicts:")
                dpg.add_button(label="Export CSV",
                               callback=lambda: self._export_table_csv(self.table_overlap, "overlaps.csv"))

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
        self._refresh_bar()
        self._refresh_section_holes()
        self._refresh_module_holes()
        self._refresh_overlaps()


    # ================================================================== BAR DRAW

    def _refresh_bar(self):
        dpg.delete_item(self.bar, children_only=True)

        p = self.store.project
        if p.exe_start is None or p.exe_end is None:
            dpg.draw_text((10,20),"No EXE range defined",parent=self.bar)
            return

        start,end = p.exe_start,p.exe_end
        if start>=end:
            dpg.draw_text((10,20),"Invalid EXE range",parent=self.bar)
            return

        L,R,T,B = 20,880,10,40
        span = float(end-start)
        def X(x): return L+((x-start)/span)*(R-L)


        # 1) grey — unmapped exe space
        dpg.draw_rectangle((L,T),(R,B), fill=COLOR_NOSEC, parent=self.bar)


        # 2) section coverage base
        for s in sorted(p.sections.values(),key=lambda x:x.start):
            dpg.draw_rectangle((X(s.start),T),(X(s.end),B),
                               fill=COLOR_SECTION,parent=self.bar)


        # 3) module holes (yellow)
        for sec, a, b in self.store.compute_module_holes():
            dpg.draw_rectangle((X(a),T),(X(b),B),
                               fill=COLOR_HOLE,parent=self.bar)


        # 4) OK = module-owned inside section
        for s in sorted(p.sections.values(),key=lambda x:x.start):
            cov=[]
            for m in p.modules.values():
                for r in m.ranges:
                    if r.section_id==s.id:
                        cov.append((r.start,r.end))
            cov=sorted(cov)
            for a,b in cov:
                dpg.draw_rectangle((X(a),T),(X(b),B),
                                   fill=COLOR_OK,parent=self.bar)


        # 5) overlaps (draw before OK so they stay visible)
        overlaps = self.store.compute_module_overlaps()
        for A,Bm,rA,rB,size in overlaps:
            lo,hi = max(rA.start,rB.start), min(rA.end,rB.end)
            dpg.draw_rectangle((X(lo),T),(X(hi),B),
                               fill=COLOR_OVERLAP,parent=self.bar)


        # labels
        dpg.draw_text((L,B+2),f"0x{start:X}",parent=self.bar)
        txt=f"0x{end:X}"
        dpg.draw_text((R-(6.8*len(txt)),B+2),txt,parent=self.bar)



    # ================================================================== TABLES

    def _refresh_section_holes(self):
        rows = dpg.get_item_children(self.table_sections).get(1,[])
        for r in rows: dpg.delete_item(r)

        for a,b in self.store.compute_section_holes():
            size=b-a
            with dpg.table_row(parent=self.table_sections):
                id1=dpg.add_text(f"0x{a:X}")
                id2=dpg.add_text(f"0x{b:X}")
                id3=dpg.add_text(f"0x{size:X}")
                for id in (id1,id2,id3):
                    dpg.bind_item_theme(id,self._yellow())

    def _refresh_module_holes(self):
        rows=dpg.get_item_children(self.table_modules).get(1,[])
        for r in rows: dpg.delete_item(r)

        for sec,a,b in self.store.compute_module_holes():
            size=b-a
            with dpg.table_row(parent=self.table_modules):
                id0=dpg.add_text(sec)
                id1=dpg.add_text(f"0x{a:X}")
                id2=dpg.add_text(f"0x{b:X}")
                id3=dpg.add_text(f"0x{size:X}")
                for id in (id0,id1,id2,id3):
                    dpg.bind_item_theme(id,self._yellow())

    def _refresh_overlaps(self):
        rows=dpg.get_item_children(self.table_overlap).get(1,[])
        for r in rows: dpg.delete_item(r)

        for A,B,rA,rB,size in self.store.compute_module_overlaps():
            sec=self.store.project.sections[rA.section_id].name
            with dpg.table_row(parent=self.table_overlap):
                items=[
                    dpg.add_text(sec),
                    dpg.add_text(A.name),
                    dpg.add_text(f"0x{rA.start:X}"),
                    dpg.add_text(f"0x{rA.end:X}"),
                    dpg.add_text(B.name),
                    dpg.add_text(f"0x{rB.start:X}"),
                    dpg.add_text(f"0x{rB.end:X}"),
                    dpg.add_text(f"0x{size:X}")
                ]
                for id in items:
                    dpg.bind_item_theme(id,self._red())

    def _export_table_csv(self, table_id, filename):
        import csv

        # COLUMN HEADERS -------------------------------------------------
        cols = dpg.get_item_children(table_id).get(0, [])
        headers = [dpg.get_item_label(col) for col in cols]

        # TABLE ROWS -----------------------------------------------------
        rows = []
        for row in dpg.get_item_children(table_id).get(1, []):  # slot 1 = table rows
            cell_items = dpg.get_item_children(row).get(1, [])  # slot 1 = individual cell widgets
            row_values = [dpg.get_value(item) for item in cell_items]
            rows.append(row_values)

        # WRITE CSV ------------------------------------------------------
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        print(f"[CSV EXPORT] {filename} — {len(rows)} rows + headers written.")

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
