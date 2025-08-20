"""
Onshape Part Manager Backend

This package provides tools for managing parts and assemblies in Onshape,
including an API client and data models.
"""

from .onshape_client import OnshapeClient
from .datatypes import Part, Assembly, Subsystem, Project

__all__ = ['OnshapeClient', 'Part', 'Assembly', 'Subsystem', 'Project']