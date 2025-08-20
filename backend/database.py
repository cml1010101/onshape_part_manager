"""
Database access layer for onshape_part_manager.

Provides MongoDB integration for Part, Assembly, Subsystem, and Project datatypes.
Includes part number generation and project management functionality.
"""

from typing import List, Optional, Union
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from dataclasses import asdict, fields
import os
from datetime import datetime

from datatypes import Part, Assembly, Subsystem, Project


class DatabaseManager:
    """Manages MongoDB connection and provides CRUD operations for all datatypes."""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", 
                 database_name: str = "onshape_part_manager"):
        """
        Initialize database connection.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.client: MongoClient = MongoClient(connection_string)
        self.db: Database = self.client[database_name]
        
        # Collections for each datatype
        self.parts: Collection = self.db.parts
        self.assemblies: Collection = self.db.assemblies
        self.subsystems: Collection = self.db.subsystems
        self.projects: Collection = self.db.projects
        
        # Counters collection for part number generation
        self.counters: Collection = self.db.counters
        
        # Initialize part number counters if they don't exist
        self._initialize_counters()
    
    def _initialize_counters(self):
        """Initialize part number counters for different project types."""
        # Initialize counter for 172 projects if it doesn't exist
        if not self.counters.find_one({"_id": "172_part_counter"}):
            self.counters.insert_one({"_id": "172_part_counter", "value": 0})
        
        # Initialize counter for NFR project if it doesn't exist
        if not self.counters.find_one({"_id": "nfr_part_counter"}):
            self.counters.insert_one({"_id": "nfr_part_counter", "value": 0})
    
    def generate_part_number(self, project_type: str) -> str:
        """
        Generate a unique part number for the given project type.
        
        Args:
            project_type: Either '172' or 'nfr'
            
        Returns:
            Generated part number string
            
        Raises:
            ValueError: If project_type is not '172' or 'nfr'
        """
        if project_type not in ['172', 'nfr']:
            raise ValueError("project_type must be either '172' or 'nfr'")
        
        counter_id = f"{project_type}_part_counter"
        
        # Atomically increment the counter and get the new value
        result = self.counters.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"value": 1}},
            return_document=pymongo.ReturnDocument.AFTER
        )
        
        if not result:
            raise RuntimeError(f"Counter {counter_id} not found")
        
        # Format part number based on project type
        if project_type == '172':
            return f"172-{result['value']:04d}"
        else:  # nfr
            return f"NFR-{result['value']:04d}"
    
    def close(self):
        """Close the database connection."""
        self.client.close()
    
    # Part CRUD operations
    def create_part(self, part: Part) -> Part:
        """Create a new part in the database."""
        part_dict = asdict(part)
        result = self.parts.insert_one(part_dict)
        part._id = result.inserted_id
        return part
    
    def get_part(self, part_id: int) -> Optional[Part]:
        """Retrieve a part by its ID."""
        part_dict = self.parts.find_one({"_id": part_id})
        if part_dict:
            return Part(**part_dict)
        return None
    
    def update_part(self, part: Part) -> bool:
        """Update an existing part in the database."""
        part_dict = asdict(part)
        result = self.parts.replace_one({"_id": part._id}, part_dict)
        return result.modified_count > 0
    
    def delete_part(self, part_id: int) -> bool:
        """Delete a part from the database."""
        result = self.parts.delete_one({"_id": part_id})
        return result.deleted_count > 0
    
    def list_parts(self, limit: int = 100) -> List[Part]:
        """List all parts with optional limit."""
        parts = []
        for part_dict in self.parts.find().limit(limit):
            parts.append(Part(**part_dict))
        return parts
    
    # Assembly CRUD operations
    def create_assembly(self, assembly: Assembly) -> Assembly:
        """Create a new assembly in the database."""
        assembly_dict = asdict(assembly)
        result = self.assemblies.insert_one(assembly_dict)
        assembly._id = result.inserted_id
        return assembly
    
    def get_assembly(self, assembly_id: int) -> Optional[Assembly]:
        """Retrieve an assembly by its ID."""
        assembly_dict = self.assemblies.find_one({"_id": assembly_id})
        if assembly_dict:
            return Assembly(**assembly_dict)
        return None
    
    def update_assembly(self, assembly: Assembly) -> bool:
        """Update an existing assembly in the database."""
        assembly_dict = asdict(assembly)
        result = self.assemblies.replace_one({"_id": assembly._id}, assembly_dict)
        return result.modified_count > 0
    
    def delete_assembly(self, assembly_id: int) -> bool:
        """Delete an assembly from the database."""
        result = self.assemblies.delete_one({"_id": assembly_id})
        return result.deleted_count > 0
    
    def list_assemblies(self, limit: int = 100) -> List[Assembly]:
        """List all assemblies with optional limit."""
        assemblies = []
        for assembly_dict in self.assemblies.find().limit(limit):
            assemblies.append(Assembly(**assembly_dict))
        return assemblies
    
    # Subsystem CRUD operations
    def create_subsystem(self, subsystem: Subsystem) -> Subsystem:
        """Create a new subsystem in the database."""
        subsystem_dict = asdict(subsystem)
        result = self.subsystems.insert_one(subsystem_dict)
        subsystem._id = result.inserted_id
        return subsystem
    
    def get_subsystem(self, subsystem_id: int) -> Optional[Subsystem]:
        """Retrieve a subsystem by its ID."""
        subsystem_dict = self.subsystems.find_one({"_id": subsystem_id})
        if subsystem_dict:
            # Convert nested parts and assemblies back to objects
            parts = [Part(**part_dict) for part_dict in subsystem_dict.get('parts', [])]
            assemblies = [Assembly(**assembly_dict) for assembly_dict in subsystem_dict.get('assemblies', [])]
            
            subsystem_dict['parts'] = parts
            subsystem_dict['assemblies'] = assemblies
            return Subsystem(**subsystem_dict)
        return None
    
    def update_subsystem(self, subsystem: Subsystem) -> bool:
        """Update an existing subsystem in the database."""
        subsystem_dict = asdict(subsystem)
        result = self.subsystems.replace_one({"_id": subsystem._id}, subsystem_dict)
        return result.modified_count > 0
    
    def delete_subsystem(self, subsystem_id: int) -> bool:
        """Delete a subsystem from the database."""
        result = self.subsystems.delete_one({"_id": subsystem_id})
        return result.deleted_count > 0
    
    def list_subsystems(self, limit: int = 100) -> List[Subsystem]:
        """List all subsystems with optional limit."""
        subsystems = []
        for subsystem_dict in self.subsystems.find().limit(limit):
            # Convert nested parts and assemblies back to objects
            parts = [Part(**part_dict) for part_dict in subsystem_dict.get('parts', [])]
            assemblies = [Assembly(**assembly_dict) for assembly_dict in subsystem_dict.get('assemblies', [])]
            
            subsystem_dict['parts'] = parts
            subsystem_dict['assemblies'] = assemblies
            subsystems.append(Subsystem(**subsystem_dict))
        return subsystems
    
    # Project CRUD operations
    def create_project(self, project: Project) -> Project:
        """Create a new project in the database."""
        project_dict = asdict(project)
        result = self.projects.insert_one(project_dict)
        # Note: Project _id is a string, so we don't override it with MongoDB's ObjectId
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieve a project by its ID."""
        project_dict = self.projects.find_one({"_id": project_id})
        if project_dict:
            # Convert nested subsystems back to objects
            subsystems = []
            for subsystem_dict in project_dict.get('subsystems', []):
                parts = [Part(**part_dict) for part_dict in subsystem_dict.get('parts', [])]
                assemblies = [Assembly(**assembly_dict) for assembly_dict in subsystem_dict.get('assemblies', [])]
                
                subsystem_dict['parts'] = parts
                subsystem_dict['assemblies'] = assemblies
                subsystems.append(Subsystem(**subsystem_dict))
            
            project_dict['subsystems'] = subsystems
            return Project(**project_dict)
        return None
    
    def update_project(self, project: Project) -> bool:
        """Update an existing project in the database."""
        project_dict = asdict(project)
        result = self.projects.replace_one({"_id": project._id}, project_dict)
        return result.modified_count > 0
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project from the database."""
        result = self.projects.delete_one({"_id": project_id})
        return result.deleted_count > 0
    
    def list_projects(self, limit: int = 100) -> List[Project]:
        """List all projects with optional limit."""
        projects = []
        for project_dict in self.projects.find().limit(limit):
            # Convert nested subsystems back to objects
            subsystems = []
            for subsystem_dict in project_dict.get('subsystems', []):
                parts = [Part(**part_dict) for part_dict in subsystem_dict.get('parts', [])]
                assemblies = [Assembly(**assembly_dict) for assembly_dict in subsystem_dict.get('assemblies', [])]
                
                subsystem_dict['parts'] = parts
                subsystem_dict['assemblies'] = assemblies
                subsystems.append(Subsystem(**subsystem_dict))
            
            project_dict['subsystems'] = subsystems
            projects.append(Project(**project_dict))
        return projects
    
    def get_172_projects(self) -> List[Project]:
        """Get all projects with identifier '172'."""
        projects = []
        for project_dict in self.projects.find({"identifier": "172"}):
            # Convert nested subsystems back to objects
            subsystems = []
            for subsystem_dict in project_dict.get('subsystems', []):
                parts = [Part(**part_dict) for part_dict in subsystem_dict.get('parts', [])]
                assemblies = [Assembly(**assembly_dict) for assembly_dict in subsystem_dict.get('assemblies', [])]
                
                subsystem_dict['parts'] = parts
                subsystem_dict['assemblies'] = assemblies
                subsystems.append(Subsystem(**subsystem_dict))
            
            project_dict['subsystems'] = subsystems
            projects.append(Project(**project_dict))
        return projects
    
    def get_nfr_project(self) -> Optional[Project]:
        """Get the NFR project (there should be only one)."""
        project_dict = self.projects.find_one({"identifier": "nfr"})
        if project_dict:
            # Convert nested subsystems back to objects
            subsystems = []
            for subsystem_dict in project_dict.get('subsystems', []):
                parts = [Part(**part_dict) for part_dict in subsystem_dict.get('parts', [])]
                assemblies = [Assembly(**assembly_dict) for assembly_dict in subsystem_dict.get('assemblies', [])]
                
                subsystem_dict['parts'] = parts
                subsystem_dict['assemblies'] = assemblies
                subsystems.append(Subsystem(**subsystem_dict))
            
            project_dict['subsystems'] = subsystems
            return Project(**project_dict)
        return None


def get_database_manager() -> DatabaseManager:
    """
    Factory function to get a DatabaseManager instance.
    
    Uses environment variables for configuration:
    - MONGODB_CONNECTION_STRING: MongoDB connection string (default: mongodb://localhost:27017/)
    - MONGODB_DATABASE_NAME: Database name (default: onshape_part_manager)
    """
    connection_string = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/")
    database_name = os.getenv("MONGODB_DATABASE_NAME", "onshape_part_manager")
    
    return DatabaseManager(connection_string, database_name)