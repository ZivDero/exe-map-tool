
# Executable Mapping Tool

A DearPyGui-based utility for interactively mapping executable memory layout — defining sections, assigning module ownership, and visualizing unmapped or overlapping regions.  
Designed for reverse engineering, engine analysis, and binary architecture research.

---

## Features

### Section Mapping
- Define named executable sections with address ranges
- Sections are sorted by start address
- Overlapping definitions are prevented automatically
- Sections may be **locked** to avoid modification

### Module Range Assignment
- Create modules and assign their owned address ranges
- One range per module per section
- Module ranges may be locked
- Supports conflict detection between modules

### Executable Range Definition
- Configure global EXE address space
- Sections must reside within EXE boundaries
- Enables top-level unmapped-space detection

### Reporting System
The **Reports** tab highlights integrity issues and unused regions:

| Report Type | Meaning |
|---|---|
| **Executable Holes** | Areas not covered by sections |
| **Module Holes** | Unclaimed space *inside* valid sections |
| **Overlap Conflicts** | Multiple modules claim the same region |

Color highlights make gaps (yellow) and overlaps (red) stand out immediately.

---

## UI Layout

```
[TABS]
 ├── Sections              → define + lock sections + set EXE bounds
 ├── Modules by Name       → assign in-section ranges per module
 ├── Modules by Section    → assign module owned ranges per section
 └── Reports               → holes and overlaps table view
```

All address inputs accept hex (`0x`, plain hex, or hex + `H/h` suffix).

Add/Edit dialogs support pasting 2 space/new line-separated values for start and end bounds of a range.

---

## Typical Usage Flow

1. **Set Executable Range**
2. **Define Sections**
   (.text, .data, .rdata, virtual pools, custom regions)
3. **Add Modules & allocate ranges**
4. View **Reports** for:
   - Global unmapped space
   - Section gaps
   - Multi-module overlap collisions

Refine until map becomes complete & conflict-free.

---

## Persistence

- Saves automatically to `project.json`
- Loaded on startup
- Persists sections, modules, ranges, locks, and EXE bounds

---

## Requirements

```
Python 3.10+
DearPyGui 2.1.x
```

Install + Run:

```
pip install dearpygui
python main.py
```

---
