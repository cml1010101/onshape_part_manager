#!/usr/bin/env python3
"""
Usage example for the onshape_part_manager database functionality.

This script demonstrates how to use the database API in practice for:
- Creating projects and managing parts
- Generating part numbers
- Organizing subsystems and assemblies
"""

import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datatypes import Part, Assembly, Subsystem, Project
from database import get_database_manager

def example_usage():
    """Example usage of the database functionality."""
    print("=== Onshape Part Manager Usage Example ===\n")
    
    # Note: This example shows usage but would require MongoDB to actually run
    print("# Example: Creating a new 172 project with parts and assemblies\n")
    
    print("# 1. Get database manager")
    print("db = get_database_manager()")
    print("")
    
    print("# 2. Generate part numbers")
    print("part_num_1 = db.generate_part_number('172')  # Returns: '172-0001'")
    print("part_num_2 = db.generate_part_number('172')  # Returns: '172-0002'")
    print("nfr_part_num = db.generate_part_number('nfr')  # Returns: 'NFR-0001'")
    print("")
    
    print("# 3. Create parts")
    print("""part1 = Part(
    _id=1,
    name=f"Drive Wheel {part_num_1}",
    description="Main drive wheel for robot",
    drawing="DRV-001.pdf",
    material="Aluminum 6061-T6",
    stl_file="drive_wheel.stl"
)""")
    print("")
    
    print("""part2 = Part(
    _id=2,
    name=f"Motor Mount {part_num_2}",
    description="Mount for drive motor",
    drawing="MTR-001.pdf", 
    material="Steel 1018",
    stl_file="motor_mount.stl"
)""")
    print("")
    
    print("# 4. Store parts in database")
    print("db.create_part(part1)")
    print("db.create_part(part2)")
    print("")
    
    print("# 5. Create assembly")
    print("""drive_assembly = Assembly(
    _id=1,
    name="Drive Assembly",
    description="Complete drive system assembly",
    drawing="DRV-ASM-001.pdf"
)""")
    print("db.create_assembly(drive_assembly)")
    print("")
    
    print("# 6. Create subsystem with parts and assemblies")
    print("""drivetrain_subsystem = Subsystem(
    _id=1,
    name="Drivetrain",
    parts=[part1, part2],
    assemblies=[drive_assembly]
)""")
    print("db.create_subsystem(drivetrain_subsystem)")
    print("")
    
    print("# 7. Create 172 project")
    print("""project_172 = Project(
    _id="172_2024_001",
    year=2024,
    identifier="172",
    name="Crescendo Robot 2024",
    description="FRC Team 172 robot for the 2024 Crescendo game",
    subsystems=[drivetrain_subsystem]
)""")
    print("db.create_project(project_172)")
    print("")
    
    print("# 8. Create NFR project")
    print("""project_nfr = Project(
    _id="nfr_2024_001", 
    year=2024,
    identifier="nfr",
    name="Off-Season Projects 2024",
    description="Non-FRC projects and prototypes",
    subsystems=[]
)""")
    print("db.create_project(project_nfr)")
    print("")
    
    print("# 9. Query projects")
    print("all_172_projects = db.get_172_projects()")
    print("nfr_project = db.get_nfr_project()")
    print("print(f'Found {len(all_172_projects)} 172 projects')")
    print("print(f'NFR project: {nfr_project.name if nfr_project else \"Not found\"}')")
    print("")
    
    print("# 10. Query parts and assemblies")
    print("all_parts = db.list_parts()")
    print("specific_part = db.get_part(1)")
    print("all_assemblies = db.list_assemblies()")
    print("")
    
    print("# 11. Update existing data")
    print("part1.description = 'Updated description for drive wheel'")
    print("db.update_part(part1)")
    print("")
    
    print("# 12. Clean up")
    print("db.close()")
    print("")
    
    print("=== Key Features Demonstrated ===")
    print("✓ Part number generation with project-specific formatting")
    print("✓ Full CRUD operations for all datatypes (Part, Assembly, Subsystem, Project)")
    print("✓ Support for multiple 172 projects and single NFR project")
    print("✓ Nested object storage and retrieval")
    print("✓ Project-specific queries")
    print("✓ Atomic counter operations for part numbering")
    print("")
    
    print("=== Usage Notes ===")
    print("- Part numbers are automatically incremented per project type")
    print("- 172 projects use format '172-XXXX', NFR uses 'NFR-XXXX'")
    print("- All nested objects (parts in subsystems, etc.) are properly serialized/deserialized")
    print("- Database connection is configurable via environment variables")
    print("- Counter operations are atomic to prevent duplicate part numbers")

if __name__ == "__main__":
    example_usage()