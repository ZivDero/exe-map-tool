import json
from dataclasses import asdict
from models import Project, Section, Module, ModuleRange


class ProjectStore:
    def __init__(self):
        self.project = Project()

    # =============================================================
    # SAVE PROJECT → JSON
    # =============================================================

    def save(self, filename="project.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(asdict(self.project), f, indent=4)
        print(f"[STORE] Saved {filename}")

    # =============================================================
    # LOAD PROJECT ← JSON
    # =============================================================

    def load(self, filename="project.json"):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        p = Project()

        p.exe_start = data.get("exe_start", None)
        p.exe_end   = data.get("exe_end", None)

        p.next_section_id = data.get("next_section_id", 1)
        p.next_module_id  = data.get("next_module_id", 1)

        # =============== Sections ================================
        sec_data = data.get("sections", {})

        # support legacy dict { "1":{...}, ... }
        if isinstance(sec_data, dict):
            sec_data = sec_data.values()

        for s in sec_data:
            section = Section(
                id=s["id"],
                name=s["name"],
                start=s["start"],
                end=s["end"],
                locked=s.get("locked", False)
            )
            p.sections[section.id] = section

        # =============== Modules + ranges ========================
        mod_data = data.get("modules", {})

        if isinstance(mod_data, dict):
            mod_data = mod_data.values()

        for m in mod_data:
            mod = Module(id=m["id"], name=m["name"])

            for r in m.get("ranges", []):
                mod.ranges.append(ModuleRange(
                    section_id=r["section_id"],
                    start=r["start"],
                    end=r["end"],
                    locked=r.get("locked", False)
                ))

            p.modules[mod.id] = mod

        self.project = p
        print(f"[STORE] Loaded {filename}")

    # =============================================================
    # -----   SECTION MANAGEMENT   ---------------------------------
    # =============================================================

    def add_section(self, name, start, end, locked=False):
        # validation
        if start >= end:
            raise ValueError("Section start must be < end.")

        # must be within EXE range if defined
        if self.project.exe_start is not None and self.project.exe_end is not None:
            if start < self.project.exe_start or end > self.project.exe_end:
                raise ValueError("Section must lie inside executable range.")

        # no overlaps allowed
        for sec in self.project.sections.values():
            if not (end <= sec.start or start >= sec.end):  # overlap check
                raise ValueError(f"Section '{name}' overlaps existing section '{sec.name}'.")

        # commit after validation
        p = self.project
        sec = Section(p.next_section_id, name, start, end, locked)
        p.sections[sec.id] = sec
        p.next_section_id += 1
        return sec

    def update_section(self, sec_id, name, start, end):
        if start >= end:
            raise ValueError("Section start must be < end.")

        # must be within EXE range if defined
        if self.project.exe_start is not None and self.project.exe_end is not None:
            if start < self.project.exe_start or end > self.project.exe_end:
                raise ValueError("Section must lie inside executable range.")

        # cannot overlap other existing sections
        for sid, sec in self.project.sections.items():
            if sid == sec_id:
                continue
            if not (end <= sec.start or start >= sec.end):
                raise ValueError(f"Section '{name}' overlaps existing section '{sec.name}'.")

        # commit
        s = self.project.sections[sec_id]
        s.name = name
        s.start = start
        s.end = end

    def delete_section(self, sec_id):
        del self.project.sections[sec_id]

    def set_section_lock(self, sec_id, state):
        self.project.sections[sec_id].locked = bool(state)

    # =============================================================
    # -----   MODULE MANAGEMENT   ----------------------------------
    # =============================================================

    def add_module(self, name):
        p = self.project
        mod = Module(p.next_module_id, name)
        p.modules[mod.id] = mod
        p.next_module_id += 1
        return mod

    def update_module(self, mod_id, new_name):
        self.project.modules[mod_id].name = new_name

    def delete_module(self, mod_id):
        del self.project.modules[mod_id]

    # =============================================================
    # ----- MODULE RANGES ------------------------------------------
    # =============================================================

    def set_module_range(self, mod_id, section_id, start, end, locked=False):
        mod = self.project.modules[mod_id]
        mod.ranges.append(ModuleRange(section_id, start, end, locked))
        return True

    def remove_module_range(self, mod_id, section_id):
        mod = self.project.modules[mod_id]
        mod.ranges = [r for r in mod.ranges if r.section_id != section_id]

    # =============================================================
    # ----- EXECUTABLE RANGE ---------------------------------------
    # =============================================================

    def set_executable_range(self, start, end):
        if start >= end:
            return False
        self.project.exe_start = start
        self.project.exe_end   = end
        return True

    # =============================================================
    # ----- ANALYSIS (Holes + Overlaps) ----------------------------
    # =============================================================

    def compute_section_holes(self):
        p = self.project
        if not (p.exe_start is not None and p.exe_end is not None):
            return []

        secs = sorted(p.sections.values(), key=lambda s: s.start)
        holes, cursor = [], p.exe_start

        for s in secs:
            if s.start > cursor:
                holes.append((cursor, s.start))
            cursor = max(cursor, s.end)

        if cursor < p.exe_end:
            holes.append((cursor, p.exe_end))

        return holes

    def compute_module_holes(self):
        holes = []
        for sec in sorted(self.project.sections.values(), key=lambda s: s.start):
            used = [(r.start, r.end)
                    for m in self.project.modules.values()
                    for r in m.ranges if r.section_id == sec.id]

            if not used:
                holes.append((sec.name, sec.start, sec.end))
                continue

            used.sort()
            cursor = sec.start

            for s, e in used:
                if s > cursor:
                    holes.append((sec.name, cursor, s))
                cursor = max(cursor, e)

            if cursor < sec.end:
                holes.append((sec.name, cursor, sec.end))

        return holes

    def compute_module_overlaps(self):
        overlaps = []
        mods = list(self.project.modules.values())

        for i in range(len(mods)):
            for j in range(i + 1, len(mods)):
                A, B = mods[i], mods[j]

                for rA in A.ranges:
                    for rB in B.ranges:
                        if rA.section_id != rB.section_id:
                            continue
                        if rA.start < rB.end and rB.start < rA.end:
                            overlaps.append((A, B, rA, rB,
                                             min(rA.end, rB.end) - max(rA.start, rB.start)))
        return overlaps
