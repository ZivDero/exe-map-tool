from dataclasses import dataclass, field

@dataclass
class Section:
    id: int
    name: str
    start: int
    end: int
    locked: bool = False

    @property
    def size(self):
        return self.end - self.start


@dataclass
class ModuleRange:
    section_id: int
    start: int
    end: int
    locked: bool = False

    @property
    def size(self):
        return self.end - self.start


@dataclass
class Module:
    id: int
    name: str
    ranges: list = field(default_factory=list)


@dataclass
class Project:
    exe_start: int | None = None
    exe_end:   int | None = None

    sections: dict = field(default_factory=dict)
    modules: dict = field(default_factory=dict)

    next_section_id: int = 1
    next_module_id: int = 1
