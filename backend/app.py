"""
FastAPI application for Onshape Part Manager.

Provides REST API endpoints for managing projects, subsystems, parts, and assemblies.
Uses MongoDB via DatabaseManager when available, falls back to in-memory storage for development.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import uuid

# Try to import MongoDB components
try:
    from database import DatabaseManager, get_database_manager
    from datatypes import Part as DBPart, Assembly as DBAssembly, Subsystem as DBSubsystem, Project as DBProject
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError as e:
    logging.warning(f"MongoDB components not available: {e}. Using in-memory storage.")
    MONGODB_AVAILABLE = False

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

# Database manager instance (will be None if MongoDB not available)
db_manager: Optional[DatabaseManager] = None

# In-memory storage for development (fallback when MongoDB not available)
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
    id: str = Field(alias="_id")
    name: str
    description: str
    drawing: Optional[str] = None
    material: Optional[str] = None
    stl_file: Optional[str] = None
    icon_file: Optional[str] = None
    
    class Config:
        populate_by_name = True

class AssemblyCreate(BaseModel):
    name: str
    description: str
    drawing: Optional[str] = None
    icon_file: Optional[str] = None

class AssemblyResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: str
    drawing: Optional[str] = None
    icon_file: Optional[str] = None
    
    class Config:
        populate_by_name = True

class SubsystemCreate(BaseModel):
    name: str

class SubsystemResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    subsystem_number: int
    parts: List[PartResponse]
    assemblies: List[AssemblyResponse]
    
    class Config:
        populate_by_name = True

class ProjectCreate(BaseModel):
    year: int
    identifier: str = Field(..., pattern="^(172|nfr)$")
    project_code: Optional[str] = None
    name: str
    description: str

class ProjectResponse(BaseModel):
    id: str = Field(alias="_id")
    year: int
    identifier: str
    project_code: Optional[str] = None
    name: str
    description: str
    subsystems: List[SubsystemResponse]
    
    class Config:
        populate_by_name = True

class DatabaseSummaryResponse(BaseModel):
    total_parts: int
    total_assemblies: int
    total_subsystems: int
    total_projects: int
    projects: List[ProjectResponse]

def generate_subsystem_number(project_identifier: str, project_code: str = None) -> int:
    """Generate the next available subsystem number for a project."""
    if MONGODB_AVAILABLE and db_manager:
        return db_manager.generate_subsystem_number(project_identifier, project_code)
    
    # Fallback to in-memory logic
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

# Database initialization
def init_database():
    """Initialize database connection and setup."""
    global db_manager
    
    if MONGODB_AVAILABLE:
        try:
            db_manager = get_database_manager()
            logger.info("Connected to MongoDB database")
            # Test the connection
            db_manager.list_projects(limit=1)
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to MongoDB: {e}. Using in-memory storage.")
            db_manager = None
            return False
    else:
        logger.info("MongoDB not available, using in-memory storage")
        return False

# Convert database objects to API response format
def convert_db_part_to_response(part: DBPart) -> Dict:
    """Convert database Part to API response format."""
    return {
        "_id": str(ObjectId()),  # Generate a fake ID for API consistency
        "name": part.name,
        "description": part.description,
        "drawing": part.drawing,
        "material": part.material,
        "stl_file": part.stl_file,
        "icon_file": part.icon_file
    }

def convert_db_assembly_to_response(assembly: DBAssembly) -> Dict:
    """Convert database Assembly to API response format."""
    return {
        "_id": str(ObjectId()),  # Generate a fake ID for API consistency
        "name": assembly.name,
        "description": assembly.description,
        "drawing": assembly.drawing,
        "icon_file": assembly.icon_file
    }

def convert_db_subsystem_to_response(subsystem: DBSubsystem) -> Dict:
    """Convert database Subsystem to API response format."""
    return {
        "_id": str(ObjectId()),  # Generate a fake ID for API consistency
        "name": subsystem.name,
        "subsystem_number": subsystem.subsystem_number,
        "parts": [convert_db_part_to_response(part) for part in subsystem.parts],
        "assemblies": [convert_db_assembly_to_response(assembly) for assembly in subsystem.assemblies]
    }

def convert_db_project_to_response(project: DBProject) -> Dict:
    """Convert database Project to API response format."""
    return {
        "_id": str(ObjectId()),  # Generate a fake ID for API consistency
        "year": project.year,
        "identifier": project.identifier,
        "project_code": project.project_code,
        "name": project.name,
        "description": project.description,
        "subsystems": [convert_db_subsystem_to_response(subsystem) for subsystem in project.subsystems]
    }



# Initialize database connection
mongodb_connected = init_database()

# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {"message": "Onshape Part Manager API", "version": "1.0.0"}

@app.get("/api/database/summary", response_model=DatabaseSummaryResponse)
async def get_database_summary():
    """Get database summary with counts and all projects."""
    try:
        if MONGODB_AVAILABLE and db_manager:
            # Use MongoDB
            projects_data = []
            
            # Get projects with their actual ObjectIds from MongoDB
            for project_doc in db_manager.projects.find():
                project_id = str(project_doc["_id"])
                
                # Convert document to Project object
                project = db_manager._document_to_object(project_doc, Project)
                
                subsystems = []
                for i, subsystem in enumerate(project.subsystems):
                    parts = [PartResponse(
                        id=str(ObjectId()),
                        name=part.name,
                        description=part.description,
                        drawing=part.drawing,
                        material=part.material,
                        stl_file=part.stl_file,
                        icon_file=part.icon_file
                    ) for part in subsystem.parts]
                    
                    assemblies = [AssemblyResponse(
                        id=str(ObjectId()),
                        name=assembly.name,
                        description=assembly.description,
                        drawing=assembly.drawing,
                        icon_file=assembly.icon_file
                    ) for assembly in subsystem.assemblies]
                    
                    # Use subsystem index as a temporary ID since subsystems are embedded
                    subsystems.append(SubsystemResponse(
                        id=str(i),  # Use index as subsystem ID
                        name=subsystem.name,
                        subsystem_number=subsystem.subsystem_number,
                        parts=parts,
                        assemblies=assemblies
                    ))
                
                projects_data.append(ProjectResponse(
                    id=project_id,  # Use the real MongoDB ObjectId
                    year=project.year,
                    identifier=project.identifier,
                    project_code=project.project_code,
                    name=project.name,
                    description=project.description,
                    subsystems=subsystems
                ))
        else:
            # Use in-memory storage
            projects_data = []
            
            for project in projects_storage.values():
                subsystems = []
                for subsystem in project['subsystems']:
                    parts = [PartResponse(**part) for part in subsystem['parts']]
                    assemblies = [AssemblyResponse(**assembly) for assembly in subsystem['assemblies']]
                    subsystems.append(SubsystemResponse(
                        id=subsystem['_id'],
                        name=subsystem['name'],
                        subsystem_number=subsystem['subsystem_number'],
                        parts=parts,
                        assemblies=assemblies
                    ))
                
                projects_data.append(ProjectResponse(
                    id=project['_id'],
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
        
        if MONGODB_AVAILABLE and db_manager:
            # Use MongoDB
            # Check if 172 project with same code already exists
            if project_data.identifier == "172":
                existing_project = db_manager.get_172_project_by_code(project_data.project_code)
                if existing_project:
                    raise HTTPException(status_code=400, detail=f"172 project with code {project_data.project_code} already exists")
            
            # Check if NFR project already exists (should be only one)
            if project_data.identifier == "nfr":
                existing_nfr = db_manager.get_nfr_project()
                if existing_nfr:
                    raise HTTPException(status_code=400, detail="NFR project already exists")
            
            # Create project dataclass
            project = DBProject(
                year=project_data.year,
                identifier=project_data.identifier,
                project_code=project_data.project_code,
                name=project_data.name,
                description=project_data.description,
                subsystems=[]
            )
            
            # Save to MongoDB
            object_id = db_manager.create_project(project)
            project_id = str(object_id)
        else:
            # Use in-memory storage
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
            id=project_id,
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
        if MONGODB_AVAILABLE and db_manager:
            # Use MongoDB
            # First find the project by ObjectId
            try:
                mongo_project_id = ObjectId(project_id)
                project = db_manager.get_project(mongo_project_id)
            except:
                # If ObjectId conversion fails, the project doesn't exist in MongoDB
                raise HTTPException(status_code=404, detail="Project not found")
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Generate subsystem number
            subsystem_number = db_manager.generate_subsystem_number(project.identifier, project.project_code)
            
            # Create subsystem dataclass
            new_subsystem = DBSubsystem(
                name=subsystem_data.name,
                subsystem_number=subsystem_number,
                parts=[],
                assemblies=[]
            )
            
            # Add subsystem to project and update in MongoDB
            project.subsystems.append(new_subsystem)
            db_manager.update_project(mongo_project_id, project)
            
            # Generate a subsystem ID for the response (since MongoDB doesn't store subsystem IDs separately)
            subsystem_id = str(ObjectId())
            
        else:
            # Use in-memory storage
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
            id=subsystem_id,
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
        if MONGODB_AVAILABLE and db_manager:
            # Use MongoDB
            try:
                mongo_project_id = ObjectId(project_id)
                project = db_manager.get_project(mongo_project_id)
            except:
                raise HTTPException(status_code=404, detail="Project not found")
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Find the subsystem by subsystem_id (which is the index in the frontend)
            try:
                subsystem_index = int(subsystem_id)
                if 0 <= subsystem_index < len(project.subsystems):
                    target_subsystem = project.subsystems[subsystem_index]
                else:
                    raise HTTPException(status_code=404, detail="Subsystem not found")
            except ValueError:
                raise HTTPException(status_code=404, detail="Invalid subsystem ID")
            
            # Create part dataclass
            new_part = DBPart(
                name=part_data.name,
                description=part_data.description,
                drawing=part_data.drawing,
                material=part_data.material,
                stl_file=part_data.stl_file,
                icon_file=part_data.icon_file
            )
            
            # Add part to subsystem and update project in MongoDB
            target_subsystem.parts.append(new_part)
            db_manager.update_project(mongo_project_id, project)
            
            # Generate a part ID for the response
            part_id = str(ObjectId())
            
        else:
            # Use in-memory storage
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
        
        return PartResponse(
            id=part_id,
            name=part_data.name,
            description=part_data.description,
            drawing=part_data.drawing,
            material=part_data.material,
            stl_file=part_data.stl_file,
            icon_file=part_data.icon_file
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating part: {e}")
        raise HTTPException(status_code=500, detail="Failed to create part")

@app.post("/api/projects/{project_id}/subsystems/{subsystem_id}/assemblies", response_model=AssemblyResponse)
async def create_assembly(project_id: str, subsystem_id: str, assembly_data: AssemblyCreate):
    """Create a new assembly in a subsystem."""
    try:
        if MONGODB_AVAILABLE and db_manager:
            # Use MongoDB
            try:
                mongo_project_id = ObjectId(project_id)
                project = db_manager.get_project(mongo_project_id)
            except:
                raise HTTPException(status_code=404, detail="Project not found")
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Find the subsystem by subsystem_id (which is the index in the frontend)
            try:
                subsystem_index = int(subsystem_id)
                if 0 <= subsystem_index < len(project.subsystems):
                    target_subsystem = project.subsystems[subsystem_index]
                else:
                    raise HTTPException(status_code=404, detail="Subsystem not found")
            except ValueError:
                raise HTTPException(status_code=404, detail="Invalid subsystem ID")
            
            # Create assembly dataclass
            new_assembly = DBAssembly(
                name=assembly_data.name,
                description=assembly_data.description,
                drawing=assembly_data.drawing,
                icon_file=assembly_data.icon_file
            )
            
            # Add assembly to subsystem and update project in MongoDB
            target_subsystem.assemblies.append(new_assembly)
            db_manager.update_project(mongo_project_id, project)
            
            # Generate an assembly ID for the response
            assembly_id = str(ObjectId())
            
        else:
            # Use in-memory storage
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
        
        return AssemblyResponse(
            id=assembly_id,
            name=assembly_data.name,
            description=assembly_data.description,
            drawing=assembly_data.drawing,
            icon_file=assembly_data.icon_file
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating assembly: {e}")
        raise HTTPException(status_code=500, detail="Failed to create assembly")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    storage_type = "mongodb" if (MONGODB_AVAILABLE and db_manager) else "in-memory"
    return {
        "status": "healthy", 
        "storage": storage_type,
        "mongodb_available": MONGODB_AVAILABLE,
        "mongodb_connected": db_manager is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)