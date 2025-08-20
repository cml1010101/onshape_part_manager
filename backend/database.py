"""
Database access layer for onshape_part_manager.

Provides MongoDB integration for Part, Assembly, Subsystem, and Project datatypes.
Includes part number generation and project management functionality.

Part Numbering System:
- 172 projects: 172-{project_code}-P{SS###} for parts, 172-{project_code}-A{SS###} for assemblies
  Where project_code = project identifier like "24A", "25B", "25C" for competition/offseason projects
  SS = subsystem number (00-99, where 00=full-robot, 99=miscellaneous)
  ### = sequential part/assembly number (000-999)

- NFR projects: NFR-SSSS-P{####} for parts, NFR-SSSS-A{####} for assemblies
  Where SSSS = subsystem number (0000-9999, where 0000=full-robot, 9999=miscellaneous)
  #### = sequential part/assembly number (0000-9999)
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
        

    
    def generate_part_number(self, project_type: str, project_identifier: str, subsystem: int, 
                           item_type: str) -> str:
        """
        Generate a unique part number based on the new numbering system.
        
        For robot-specific parts (various competition/offseason projects):
        - Parts: 172-{project_code}-P{SS###} 
        - Assemblies: 172-{project_code}-A{SS###}
        Where project_code=project identifier (e.g., "24A", "25B", "25C"), SS=subsystem (01-98, 00=full-robot, 99=misc), ###=part number (000-999)
        
        For non-specific parts (multi-year, single NFR project):
        - Parts: NFR-SSSS-P{####}
        - Assemblies: NFR-SSSS-A{####}
        Where SSSS=subsystem number (0000-9999), ####=part number (0000-9999)
        
        Args:
            project_type: Either '172' or 'nfr'
            project_identifier: Project code for 172 projects (e.g., "24A", "25B", "25C") or "nfr" for NFR projects
            subsystem: Subsystem number (0-99 for 172, 0-9999 for nfr, where 0=full-robot, 99/9999=misc)
            item_type: Either 'part' or 'assembly'
            
        Returns:
            Generated part number string
            
        Raises:
            ValueError: If parameters are invalid
        """
        if project_type not in ['172', 'nfr']:
            raise ValueError("project_type must be either '172' or 'nfr'")
        
        if item_type not in ['part', 'assembly']:
            raise ValueError("item_type must be either 'part' or 'assembly'")
        
        if project_type == '172':
            # Validate project_identifier format for 172 projects (should be like "24A", "25B", etc.)
            if not project_identifier or len(project_identifier) < 3:
                raise ValueError("project_identifier for 172 projects must be in format like '24A', '25B', '25C'")
            
        # Validate subsystem range based on project type
        if project_type == '172':
            if subsystem < 0 or subsystem > 99:
                raise ValueError("subsystem must be between 0 and 99 for 172 projects")
        else:  # nfr
            if subsystem < 0 or subsystem > 9999:
                raise ValueError("subsystem must be between 0 and 9999 for NFR projects")
        
        item_prefix = 'P' if item_type == 'part' else 'A'
        
        if project_type == '172':
            # Format: 172-{project_code}-P{SS###} or 172-{project_code}-A{SS###}
            prefix = f"172-{project_identifier}-{item_prefix}{subsystem:02d}"
            
            # Find existing part numbers with this prefix
            collection = self.parts if item_type == 'part' else self.assemblies
            existing_numbers = set()
            
            # Search for parts/assemblies with names starting with this prefix
            for doc in collection.find({"name": {"$regex": f"^{prefix}"}}):
                name = doc.get("name", "")
                if name.startswith(prefix) and len(name) >= len(prefix) + 3:
                    try:
                        number = int(name[len(prefix):len(prefix)+3])
                        existing_numbers.add(number)
                    except ValueError:
                        continue
            
            # Find the first available number (0-999)
            for i in range(1000):
                if i not in existing_numbers:
                    return f"{prefix}{i:03d}"
            
            raise RuntimeError("No available part numbers in range 000-999")
        
        else:  # nfr
            # Format: NFR-SSSS-P{####} or NFR-SSSS-A{####}
            prefix = f"NFR-{subsystem:04d}-{item_prefix}"
            
            # Find existing part numbers with this prefix
            collection = self.parts if item_type == 'part' else self.assemblies
            existing_numbers = set()
            
            # Search for parts/assemblies with names starting with this prefix
            for doc in collection.find({"name": {"$regex": f"^{prefix}"}}):
                name = doc.get("name", "")
                if name.startswith(prefix) and len(name) >= len(prefix) + 4:
                    try:
                        number = int(name[len(prefix):len(prefix)+4])
                        existing_numbers.add(number)
                    except ValueError:
                        continue
            
            # Find the first available number (0-9999)
            for i in range(10000):
                if i not in existing_numbers:
                    return f"{prefix}{i:04d}"
            
            raise RuntimeError("No available part numbers in range 0000-9999")
    
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
    
    def get_172_project_by_code(self, project_code: str) -> Optional[Project]:
        """Get a specific 172 project by its project code (e.g., '24A', '25B')."""
        project_dict = self.projects.find_one({"identifier": "172", "project_code": project_code})
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
    
    def print_summary(self, detailed: bool = False):
        """
        Print a comprehensive summary of the database contents.
        
        Args:
            detailed: If True, includes individual part and assembly names
        """
        print("=" * 60)
        print("DATABASE SUMMARY")
        print("=" * 60)
        
        # Get total counts
        total_parts = self.parts.count_documents({})
        total_assemblies = self.assemblies.count_documents({})
        total_subsystems = self.subsystems.count_documents({})
        total_projects = self.projects.count_documents({})
        
        print(f"\nTOTAL COUNTS:")
        print(f"  Parts: {total_parts}")
        print(f"  Assemblies: {total_assemblies}")
        print(f"  Subsystems: {total_subsystems}")
        print(f"  Projects: {total_projects}")
        
        # Get all projects
        projects = self.list_projects()
        
        if not projects:
            print("\nNo projects found in database.")
            return
        
        print(f"\nPROJECTS:")
        print("-" * 40)
        
        # Group projects by type
        team_172_projects = [p for p in projects if p.identifier == "172"]
        nfr_projects = [p for p in projects if p.identifier == "nfr"]
        
        # Show 172 projects
        if team_172_projects:
            print(f"\n172 TEAM PROJECTS ({len(team_172_projects)}):")
            for project in sorted(team_172_projects, key=lambda x: x.project_code or ""):
                print(f"  {project._id} ({project.project_code}) - {project.name}")
                print(f"    Year: {project.year}")
                print(f"    Description: {project.description}")
                print(f"    Subsystems: {len(project.subsystems)}")
                
                if project.subsystems:
                    total_project_parts = 0
                    total_project_assemblies = 0
                    
                    for subsystem in project.subsystems:
                        parts_count = len(subsystem.parts)
                        assemblies_count = len(subsystem.assemblies)
                        total_project_parts += parts_count
                        total_project_assemblies += assemblies_count
                        
                        print(f"      {subsystem.name} (ID: {subsystem._id}): {parts_count} parts, {assemblies_count} assemblies")
                        
                        if detailed and (parts_count > 0 or assemblies_count > 0):
                            if parts_count > 0:
                                print(f"        Parts: {', '.join([p.name for p in subsystem.parts])}")
                            if assemblies_count > 0:
                                print(f"        Assemblies: {', '.join([a.name for a in subsystem.assemblies])}")
                    
                    print(f"    Total: {total_project_parts} parts, {total_project_assemblies} assemblies")
                print()
        
        # Show NFR projects
        if nfr_projects:
            print(f"\nNFR PROJECTS ({len(nfr_projects)}):")
            for project in nfr_projects:
                print(f"  {project._id} - {project.name}")
                print(f"    Year: {project.year}")
                print(f"    Description: {project.description}")
                print(f"    Subsystems: {len(project.subsystems)}")
                
                if project.subsystems:
                    total_project_parts = 0
                    total_project_assemblies = 0
                    
                    for subsystem in project.subsystems:
                        parts_count = len(subsystem.parts)
                        assemblies_count = len(subsystem.assemblies)
                        total_project_parts += parts_count
                        total_project_assemblies += assemblies_count
                        
                        print(f"      {subsystem.name} (ID: {subsystem._id}): {parts_count} parts, {assemblies_count} assemblies")
                        
                        if detailed and (parts_count > 0 or assemblies_count > 0):
                            if parts_count > 0:
                                print(f"        Parts: {', '.join([p.name for p in subsystem.parts])}")
                            if assemblies_count > 0:
                                print(f"        Assemblies: {', '.join([a.name for a in subsystem.assemblies])}")
                    
                    print(f"    Total: {total_project_parts} parts, {total_project_assemblies} assemblies")
                print()
        
        # Show part numbering format information
        print("PART NUMBERING FORMATS:")
        print("-" * 40)
        print("172 Projects (Competition/Offseason):")
        print("  Parts:      172-{project_code}-P{SS###}")
        print("  Assemblies: 172-{project_code}-A{SS###}")
        print("  Where: project_code = '24A', '25B', '25C', etc.")
        print("         SS = subsystem number (00-99, 00=full-robot, 99=misc)")
        print("         ### = part/assembly number (000-999)")
        print()
        print("NFR Projects (Multi-year components):")
        print("  Parts:      NFR-SSSS-P{####}")
        print("  Assemblies: NFR-SSSS-A{####}")
        print("  Where: SSSS = subsystem number (0000-9999, 0000=full-robot, 9999=misc)")
        print("         #### = part/assembly number (0000-9999)")
        
        print("=" * 60)


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