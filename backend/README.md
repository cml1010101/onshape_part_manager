# Onshape Part Manager Backend

FastAPI backend for the Onshape Part Manager application.

## Features

- REST API for managing projects, subsystems, parts, and assemblies
- In-memory storage for development/testing
- CORS enabled for frontend integration
- Auto-generated subsystem numbers
- Support for both 172 and NFR project types

## Requirements

- Python 3.8+
- FastAPI 0.115.6
- Uvicorn 0.32.1

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

### Development
```bash
python app.py
```

### Production
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Database Summary
- `GET /api/database/summary` - Get database summary with counts and all projects

### Projects
- `POST /api/projects` - Create a new project

### Subsystems
- `POST /api/projects/{project_id}/subsystems` - Create a new subsystem in a project

### Parts
- `POST /api/projects/{project_id}/subsystems/{subsystem_id}/parts` - Create a new part in a subsystem

### Assemblies
- `POST /api/projects/{project_id}/subsystems/{subsystem_id}/assemblies` - Create a new assembly in a subsystem

### Health Check
- `GET /health` - Health check endpoint

## API Documentation

When the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Project Types

### 172 Projects
- Used for competition/offseason projects
- Require a project_code (e.g., "25A", "25B", "25C")
- Subsystem numbers: 0-99 (00=full-robot, 99=miscellaneous)

### NFR Projects
- Used for multi-year components
- No project_code needed (only one NFR project allowed)
- Subsystem numbers: 0-9999 (0000=full-robot, 9999=miscellaneous)

## Storage

The backend currently uses in-memory storage for development purposes. For production, replace the `projects_storage` dictionary with actual database integration using the provided `database.py` module with MongoDB.