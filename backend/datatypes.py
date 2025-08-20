from dataclasses import dataclass
from typing import Optional

@dataclass
class Part:
    name: str
    description: str
    drawing: str | None
    material: str | None
    stl_file: str | None
    icon_file: str | None

@dataclass
class Assembly:
    name: str
    description: str
    drawing: str | None
    icon_file: str | None

@dataclass
class Subsystem:
    name: str
    subsystem_number: int  # Auto-generated subsystem number
    parts: list[Part]
    assemblies: list[Assembly]

@dataclass
class Project:
    year: int
    identifier: str  # "172" or "nfr"
    project_code: str | None  # For 172 projects: "24A", "25B", "25C", etc. For NFR: None
    name: str
    description: str
    subsystems: list[Subsystem]