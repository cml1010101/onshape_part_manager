from dataclasses import dataclass

@dataclass
class Part:
    _id: int
    name: str
    description: str
    drawing: str
    material: str
    stl_file: str | None

@dataclass
class Assembly:
    _id: int
    name: str
    description: str
    drawing: str

@dataclass
class Subsystem:
    _id: int
    name: str
    parts: list[Part]
    assemblies: list[Assembly]

@dataclass
class Project:
    _id: str
    year: int
    identifier: str  # "172" or "nfr"
    project_code: str | None  # For 172 projects: "24A", "25B", "25C", etc. For NFR: None
    name: str
    description: str
    subsystems: list[Subsystem]