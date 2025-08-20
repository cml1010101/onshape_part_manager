#!/usr/bin/env python3
"""
Test script to demonstrate database functionality for onshape_part_manager.

This script creates sample data and tests the database operations including:
- Part number generation
- Creating and retrieving projects (172 and NFR types)
- CRUD operations for all datatypes
"""

import sys
import os
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datatypes import Part, Assembly, Subsystem, Project
from database import DatabaseManager

def test_part_number_generation():
    """Test part number generation for both project types."""
    print("Testing part number generation...")
    
    # Use a test database
    db = DatabaseManager(database_name="onshape_part_manager_test")
    
    try:
        # Test 172 project part numbers
        part_num_1 = db.generate_part_number("172")
        part_num_2 = db.generate_part_number("172")
        print(f"Generated 172 part numbers: {part_num_1}, {part_num_2}")
        
        # Test NFR project part numbers
        nfr_num_1 = db.generate_part_number("nfr")
        nfr_num_2 = db.generate_part_number("nfr")
        print(f"Generated NFR part numbers: {nfr_num_1}, {nfr_num_2}")
        
        # Test invalid project type
        try:
            db.generate_part_number("invalid")
            print("ERROR: Should have raised ValueError for invalid project type")
        except ValueError as e:
            print(f"Correctly caught error for invalid project type: {e}")
        
        print("✓ Part number generation test passed\n")
        
    except Exception as e:
        print(f"✗ Part number generation test failed: {e}\n")
    finally:
        db.close()

def test_crud_operations():
    """Test CRUD operations for all datatypes."""
    print("Testing CRUD operations...")
    
    db = DatabaseManager(database_name="onshape_part_manager_test")
    
    try:
        # Test Part CRUD
        print("Testing Part CRUD...")
        part = Part(
            _id=1,
            name="Test Part",
            description="A test part for validation",
            drawing="drawing_001.pdf",
            material="Aluminum 6061",
            stl_file="test_part.stl"
        )
        
        # Create
        created_part = db.create_part(part)
        print(f"Created part: {created_part.name}")
        
        # Read
        retrieved_part = db.get_part(1)
        if retrieved_part and retrieved_part.name == "Test Part":
            print("✓ Part retrieval successful")
        else:
            print("✗ Part retrieval failed")
        
        # Update
        part.description = "Updated test part description"
        updated = db.update_part(part)
        if updated:
            print("✓ Part update successful")
        else:
            print("✗ Part update failed")
        
        # List
        parts = db.list_parts()
        print(f"Listed {len(parts)} parts")
        
        # Test Assembly CRUD
        print("Testing Assembly CRUD...")
        assembly = Assembly(
            _id=1,
            name="Test Assembly",
            description="A test assembly",
            drawing="assembly_001.pdf"
        )
        
        db.create_assembly(assembly)
        retrieved_assembly = db.get_assembly(1)
        if retrieved_assembly:
            print("✓ Assembly CRUD basic operations successful")
        
        # Test Subsystem with nested objects
        print("Testing Subsystem CRUD...")
        subsystem = Subsystem(
            _id=1,
            name="Test Subsystem",
            parts=[part],
            assemblies=[assembly]
        )
        
        db.create_subsystem(subsystem)
        retrieved_subsystem = db.get_subsystem(1)
        if retrieved_subsystem and len(retrieved_subsystem.parts) == 1:
            print("✓ Subsystem CRUD with nested objects successful")
        
        # Test Project with nested objects
        print("Testing Project CRUD...")
        project_172 = Project(
            _id="172_2024_001",
            year=2024,
            identifier="172",
            name="Test 172 Project",
            description="A test 172 project",
            subsystems=[subsystem]
        )
        
        db.create_project(project_172)
        retrieved_project = db.get_project("172_2024_001")
        if retrieved_project and len(retrieved_project.subsystems) == 1:
            print("✓ Project CRUD with nested objects successful")
        
        # Create NFR project
        project_nfr = Project(
            _id="nfr_2024_001",
            year=2024,
            identifier="nfr",
            name="Test NFR Project",
            description="A test NFR project",
            subsystems=[]
        )
        
        db.create_project(project_nfr)
        
        # Test specialized project retrieval methods
        projects_172 = db.get_172_projects()
        nfr_project = db.get_nfr_project()
        
        if len(projects_172) >= 1 and nfr_project:
            print("✓ Specialized project retrieval successful")
            print(f"Found {len(projects_172)} 172 projects and 1 NFR project")
        
        print("✓ All CRUD operations test passed\n")
        
    except Exception as e:
        print(f"✗ CRUD operations test failed: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_project_structure():
    """Test the specific project structure requirements."""
    print("Testing project structure requirements...")
    
    db = DatabaseManager(database_name="onshape_part_manager_test")
    
    try:
        # Create multiple 172 projects
        for i in range(3):
            project = Project(
                _id=f"172_2024_{i+1:03d}",
                year=2024,
                identifier="172",
                name=f"172 Project {i+1}",
                description=f"Test 172 project number {i+1}",
                subsystems=[]
            )
            db.create_project(project)
        
        # Create one NFR project
        nfr_project = Project(
            _id="nfr_2024_001",
            year=2024,
            identifier="nfr",
            name="NFR Project",
            description="Test NFR project",
            subsystems=[]
        )
        db.create_project(nfr_project)
        
        # Verify the structure
        projects_172 = db.get_172_projects()
        nfr_project_retrieved = db.get_nfr_project()
        
        if len(projects_172) >= 3 and nfr_project_retrieved:
            print(f"✓ Project structure correct: {len(projects_172)} 172 projects, 1 NFR project")
        else:
            print(f"✗ Project structure incorrect: {len(projects_172)} 172 projects, {'1' if nfr_project_retrieved else '0'} NFR project")
        
        print("✓ Project structure test passed\n")
        
    except Exception as e:
        print(f"✗ Project structure test failed: {e}\n")
    finally:
        db.close()

def cleanup_test_database():
    """Clean up test database."""
    print("Cleaning up test database...")
    
    db = DatabaseManager(database_name="onshape_part_manager_test")
    try:
        # Drop the test database
        db.client.drop_database("onshape_part_manager_test")
        print("✓ Test database cleaned up")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=== Onshape Part Manager Database Test ===\n")
    
    # Run all tests
    test_part_number_generation()
    test_crud_operations()
    test_project_structure()
    
    # Cleanup
    cleanup_test_database()
    
    print("=== Test Complete ===")