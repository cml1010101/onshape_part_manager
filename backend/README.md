# Backend Database Functionality

This directory contains the database access layer for the Onshape Part Manager.

## Files

- **`datatypes.py`** - Core dataclass definitions for Part, Assembly, Subsystem, and Project
- **`database.py`** - MongoDB database access layer with CRUD operations and part number generation
- **`requirements.txt`** - Python dependencies (pymongo)
- **`demo_api.py`** - API demonstration script (runs without MongoDB)
- **`usage_example.py`** - Practical usage examples
- **`test_database.py`** - Comprehensive test suite (requires MongoDB)

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. View API demonstration:
   ```bash
   python3 demo_api.py
   ```

3. See usage examples:
   ```bash
   python3 usage_example.py
   ```

4. Run tests (requires MongoDB):
   ```bash
   # Start MongoDB first, then:
   python3 test_database.py
   ```

## Key Features

### Part Number Generation
- Automatic part number generation for project types
- Format: `172-XXXX` for 172 projects, `NFR-XXXX` for NFR projects
- Atomic counter operations prevent duplicates

### Project Management
- Support for multiple '172' projects
- Single 'NFR' project support
- Project-specific queries: `get_172_projects()`, `get_nfr_project()`

### Full CRUD Operations
- **Parts**: Create, read, update, delete, list
- **Assemblies**: Create, read, update, delete, list  
- **Subsystems**: Create, read, update, delete, list (with nested parts/assemblies)
- **Projects**: Create, read, update, delete, list (with nested subsystems)

### Database Configuration
Environment variables:
- `MONGODB_CONNECTION_STRING` (default: `mongodb://localhost:27017/`)
- `MONGODB_DATABASE_NAME` (default: `onshape_part_manager`)

## Usage Example

```python
from database import get_database_manager
from datatypes import Part, Project

# Get database manager
db = get_database_manager()

# Generate part number
part_num = db.generate_part_number('172')  # Returns '172-0001'

# Create and store a part
part = Part(
    _id=1,
    name=f"Drive Wheel {part_num}",
    description="Main drive wheel",
    drawing="DRV-001.pdf",
    material="Aluminum 6061",
    stl_file="wheel.stl"
)
db.create_part(part)

# Query parts
all_parts = db.list_parts()
specific_part = db.get_part(1)

# Clean up
db.close()
```

## Database Schema

The system uses MongoDB with the following collections:

- **`parts`** - Individual parts with materials, drawings, STL files
- **`assemblies`** - Assembly definitions with drawings
- **`subsystems`** - Groupings of parts and assemblies
- **`projects`** - Top-level projects containing subsystems
- **`counters`** - Atomic counters for part number generation

All nested relationships are properly serialized and deserialized automatically.