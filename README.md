# onshape_part_manager
A way to easily manage part numbering and production on onshape

## Project Structure

- **backend/**: Python backend with MongoDB integration for managing parts, assemblies, subsystems, and projects
- **frontend/**: React TypeScript frontend with clean UI for database management

## Features

### Backend
- MongoDB database integration
- Part numbering system for 172 projects (competition/offseason) and NFR projects (multi-year components)
- CRUD operations for parts, assemblies, subsystems, and projects
- Auto-generated part numbers and subsystem numbers

### Frontend
- Database summary dashboard showing total counts
- Project management interface
- Create and manage parts, assemblies, subsystems, and projects
- Clean, responsive UI built with React and TypeScript

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
python test.py  # Requires MongoDB running
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Part Numbering System

### 172 Projects (Competition/Offseason)
- **Parts**: `172-{project_code}-P{SS###}`
- **Assemblies**: `172-{project_code}-A{SS###}`
- Where `project_code` = "24A", "25B", "25C", etc.
- `SS` = subsystem number (00-99, 00=full-robot, 99=misc)
- `###` = part/assembly number (000-999)

### NFR Projects (Multi-year components)
- **Parts**: `NFR-SSSS-P{####}`
- **Assemblies**: `NFR-SSSS-A{####}`
- Where `SSSS` = subsystem number (0000-9999, 0000=full-robot, 9999=misc)
- `####` = part/assembly number (0000-9999)
