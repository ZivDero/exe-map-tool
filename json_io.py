import json
from models import Project, Section, Module, ModuleRange, asdict

def project_to_dict(store) -> dict:
    p = store.project
    return {
        "sections": [vars(s) for s in p.sections.values()],
        "modules": [
            {"id": m.id, "name": m.name,
             "ranges": [vars(r) for r in m.ranges]}
            for m in p.modules.values()
        ]
    }


def project_from_dict(data) -> "ProjectStore":
    from store import ProjectStore
    store = ProjectStore()
    for s in data.get("sections", []):
        sec = Section(**s)
        store.project.sections[sec.id] = sec

    for m in data.get("modules", []):
        mod = Module(id=m["id"], name=m["name"],
                     ranges=[ModuleRange(**r) for r in m.get("ranges", [])])
        store.project.modules[mod.id] = mod
    return store


def save_to_json(store, filename="project.json"):
    with open(filename, "w") as f:
        json.dump(project_to_dict(store), f, indent=2)


def load_from_json(filename="project.json"):
    with open(filename,"r") as f:
        data = json.load(f)
    return project_from_dict(data)
