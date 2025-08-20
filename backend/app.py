"""
FastAPI application for Onshape Part Manager.

Provides REST API endpoints for managing projects, subsystems, parts, and assemblies.
Uses in-memory storage for development/testing when MongoDB is not available.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Onshape Part Manager API",
    description="API for managing FRC robot parts, assemblies, subsystems, and projects",
    version="1.0.0"
)

# CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for development
projects_storage: Dict[str, Dict] = {}

# Pydantic models for API requests/responses
class PartCreate(BaseModel):
    name: str
    description: str
    drawing: Optional[str] = None
    material: Optional[str] = None
    stl_file: Optional[str] = None
    icon_file: Optional[str] = None

class PartResponse(BaseModel):
    _id: str
    name: str
    description: str
    drawing: Optional[str] = None
    material: Optional[str] = None
    stl_file: Optional[str] = None
    icon_file: Optional[str] = None

class AssemblyCreate(BaseModel):
    name: str
    description: str
    drawing: Optional[str] = None
    icon_file: Optional[str] = None

class AssemblyResponse(BaseModel):
    _id: str
    name: str
    description: str
    drawing: Optional[str] = None
    icon_file: Optional[str] = None

class SubsystemCreate(BaseModel):
    name: str

class SubsystemResponse(BaseModel):
    _id: str
    name: str
    subsystem_number: int
    parts: List[PartResponse]
    assemblies: List[AssemblyResponse]

class ProjectCreate(BaseModel):
    year: int
    identifier: str = Field(..., pattern="^(172|nfr)$")
    project_code: Optional[str] = None
    name: str
    description: str

class ProjectResponse(BaseModel):
    _id: str
    year: int
    identifier: str
    project_code: Optional[str] = None
    name: str
    description: str
    subsystems: List[SubsystemResponse]

class DatabaseSummaryResponse(BaseModel):
    total_parts: int
    total_assemblies: int
    total_subsystems: int
    total_projects: int
    projects: List[ProjectResponse]

def generate_subsystem_number(project_identifier: str, project_code: str = None) -> int:
    """Generate the next available subsystem number for a project."""
    max_subsystem = 99 if project_identifier == '172' else 9999
    
    existing_numbers = set()
    for project in projects_storage.values():
        if (project['identifier'] == project_identifier and 
            (project_identifier == 'nfr' or project.get('project_code') == project_code)):
            for subsystem in project['subsystems']:
                existing_numbers.add(subsystem['subsystem_number'])
    
    # Find the first available number
    for i in range(max_subsystem + 1):
        if i not in existing_numbers:
            return i
    
    raise RuntimeError(f"No available subsystem numbers in range 0-{max_subsystem}")

# Initialize with some sample data
def init_sample_data():
    """Initialize the storage with sample data matching the frontend mock."""
    # Create first project
    project1_id = str(uuid.uuid4())
    projects_storage[project1_id] = {
        "_id": project1_id,
        "year": 2025,
        "identifier": "172",
        "project_code": "25A",
        "name": "172 Project 25A",
        "description": "Project 25A for the 172 team.",
        "subsystems": [
            {
                "_id": "s1",
                "name": "Drivetrain",
                "subsystem_number": 1,
                "parts": [
                    {
                        "_id": "p1",
                        "name": "Drive Wheel",
                        "description": "Main drive wheel for robot",
                        "material": "Aluminum",
                        "drawing": None,
                        "stl_file": None,
                        "icon_file": None
                    }
                ],
                "assemblies": [
                    {
                        "_id": "a1",
                        "name": "Gearbox Assembly",
                        "description": "Main gearbox for drivetrain",
                        "drawing": None,
                        "icon_file": None
                    }
                ]
            }
        ]
    }

    # Create second project
    project2_id = str(uuid.uuid4())
    projects_storage[project2_id] = {
        "_id": project2_id,
        "year": 2023,
        "identifier": "nfr",
        "project_code": None,
        "name": "NFR Project",
        "description": "The central project for all continuing CAD development.",
        "subsystems": [
            {
                "_id": "s2",
                "name": "Common Components",
                "subsystem_number": 0,
                "parts": [
                    {
                        "_id": "p2",
                        "name": "Standard Bracket",
                        "description": "Reusable mounting bracket",
                        "material": "Steel",
                        "drawing": None,
                        "stl_file": None,
                        "icon_file": None
                    }
                ],
                "assemblies": []
            }
        ]
    }

# Initialize sample data
init_sample_data()

# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {"message": "Onshape Part Manager API", "version": "1.0.0"}

@app.get("/api/database/summary", response_model=DatabaseSummaryResponse)
async def get_database_summary():
    """Get database summary with counts and all projects."""
    try:
        projects_data = []
        
        for project in projects_storage.values():
            subsystems = []
            for subsystem in project['subsystems']:
                parts = [PartResponse(**part) for part in subsystem['parts']]
                assemblies = [AssemblyResponse(**assembly) for assembly in subsystem['assemblies']]
                subsystems.append(SubsystemResponse(
                    _id=subsystem['_id'],
                    name=subsystem['name'],
                    subsystem_number=subsystem['subsystem_number'],
                    parts=parts,
                    assemblies=assemblies
                ))
            
            projects_data.append(ProjectResponse(
                _id=project['_id'],
                year=project['year'],
                identifier=project['identifier'],
                project_code=project['project_code'],
                name=project['name'],
                description=project['description'],
                subsystems=subsystems
            ))
        
        # Calculate totals
        total_parts = sum(
            len(subsystem.parts) 
            for project in projects_data 
            for subsystem in project.subsystems
        )
        total_assemblies = sum(
            len(subsystem.assemblies) 
            for project in projects_data 
            for subsystem in project.subsystems
        )
        total_subsystems = sum(len(project.subsystems) for project in projects_data)
        total_projects = len(projects_data)
        
        return DatabaseSummaryResponse(
            total_parts=total_parts,
            total_assemblies=total_assemblies,
            total_subsystems=total_subsystems,
            total_projects=total_projects,
            projects=projects_data
        )
    except Exception as e:
        logger.error(f"Error getting database summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database summary")

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate):
    """Create a new project."""
    try:
        # Validate 172 project requires project_code
        if project_data.identifier == "172" and not project_data.project_code:
            raise HTTPException(status_code=400, detail="172 projects must have a project_code")
        
        # Validate NFR project should not have project_code
        if project_data.identifier == "nfr" and project_data.project_code:
            raise HTTPException(status_code=400, detail="NFR projects should not have a project_code")
        
        # Check if 172 project with same code already exists
        if project_data.identifier == "172":
            for project in projects_storage.values():
                if (project['identifier'] == "172" and 
                    project.get('project_code') == project_data.project_code):
                    raise HTTPException(status_code=400, detail=f"172 project with code {project_data.project_code} already exists")
        
        # Check if NFR project already exists (should be only one)
        if project_data.identifier == "nfr":
            for project in projects_storage.values():
                if project['identifier'] == "nfr":
                    raise HTTPException(status_code=400, detail="NFR project already exists")
        
        # Create project
        project_id = str(uuid.uuid4())
        new_project = {
            "_id": project_id,
            "year": project_data.year,
            "identifier": project_data.identifier,
            "project_code": project_data.project_code,
            "name": project_data.name,
            "description": project_data.description,
            "subsystems": []
        }
        
        projects_storage[project_id] = new_project
        
        return ProjectResponse(
            _id=project_id,
            year=project_data.year,
            identifier=project_data.identifier,
            project_code=project_data.project_code,
            name=project_data.name,
            description=project_data.description,
            subsystems=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")

@app.post("/api/projects/{project_id}/subsystems", response_model=SubsystemResponse)
async def create_subsystem(project_id: str, subsystem_data: SubsystemCreate):
    """Create a new subsystem in a project."""
    try:
        if project_id not in projects_storage:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_storage[project_id]
        
        # Generate subsystem number
        subsystem_number = generate_subsystem_number(project['identifier'], project.get('project_code'))
        
        # Create subsystem
        subsystem_id = str(uuid.uuid4())
        new_subsystem = {
            "_id": subsystem_id,
            "name": subsystem_data.name,
            "subsystem_number": subsystem_number,
            "parts": [],
            "assemblies": []
        }
        
        # Add subsystem to project
        project['subsystems'].append(new_subsystem)
        
        return SubsystemResponse(
            _id=subsystem_id,
            name=subsystem_data.name,
            subsystem_number=subsystem_number,
            parts=[],
            assemblies=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subsystem: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subsystem")

@app.post("/api/projects/{project_id}/subsystems/{subsystem_id}/parts", response_model=PartResponse)
async def create_part(project_id: str, subsystem_id: str, part_data: PartCreate):
    """Create a new part in a subsystem."""
    try:
        if project_id not in projects_storage:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_storage[project_id]
        
        # Find the subsystem
        subsystem = None
        for sub in project['subsystems']:
            if sub['_id'] == subsystem_id:
                subsystem = sub
                break
        
        if not subsystem:
            raise HTTPException(status_code=404, detail="Subsystem not found")
        
        # Create part
        part_id = str(uuid.uuid4())
        new_part = {
            "_id": part_id,
            "name": part_data.name,
            "description": part_data.description,
            "drawing": part_data.drawing,
            "material": part_data.material,
            "stl_file": part_data.stl_file,
            "icon_file": part_data.icon_file
        }
        
        # Add part to subsystem
        subsystem['parts'].append(new_part)
        
        return PartResponse(**new_part)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating part: {e}")
        raise HTTPException(status_code=500, detail="Failed to create part")

@app.post("/api/projects/{project_id}/subsystems/{subsystem_id}/assemblies", response_model=AssemblyResponse)
async def create_assembly(project_id: str, subsystem_id: str, assembly_data: AssemblyCreate):
    """Create a new assembly in a subsystem."""
    try:
        if project_id not in projects_storage:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_storage[project_id]
        
        # Find the subsystem
        subsystem = None
        for sub in project['subsystems']:
            if sub['_id'] == subsystem_id:
                subsystem = sub
                break
        
        if not subsystem:
            raise HTTPException(status_code=404, detail="Subsystem not found")
        
        # Create assembly
        assembly_id = str(uuid.uuid4())
        new_assembly = {
            "_id": assembly_id,
            "name": assembly_data.name,
            "description": assembly_data.description,
            "drawing": assembly_data.drawing,
            "icon_file": assembly_data.icon_file
        }
        
        # Add assembly to subsystem
        subsystem['assemblies'].append(new_assembly)
        
        return AssemblyResponse(**new_assembly)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating assembly: {e}")
        raise HTTPException(status_code=500, detail="Failed to create assembly")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "storage": "in-memory"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)