from fastapi import FastAPI, Request
import uvicorn
import requests
import os
import base64
from typing import Any, Optional, Dict, List
import gspread

ONSHAPE_API_KEY = os.getenv("ONSHAPE_API_KEY")
ONSHAPE_API_SECRET = os.getenv("ONSHAPE_API_SECRET")
ONSHAPE_BASE_URL = "https://cad.onshape.com/api/v10"


def get_auth_header() -> str:
    """Generate the basic authentication header for Onshape API"""
    credentials = f"{ONSHAPE_API_KEY}:{ONSHAPE_API_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"


async def get_document_property(document_id: str, property_name: str) -> Optional[str]:
    """Fetch a specific document property from Onshape API"""
    url = f"{ONSHAPE_BASE_URL}/metadata/d/{document_id}"
    headers = {
        "Accept": "application/json",
        "Authorization": get_auth_header()
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if not response.ok:
            raise Exception(f"HTTP error! status: {response.status_code}")
        
        data = response.json()
        
        if data.get("properties") and isinstance(data["properties"], list):
            for prop in data["properties"]:
                if prop.get("name") == property_name:
                    return prop.get("value")
        
        return None
    except Exception as error:
        print(f"Error fetching document property {property_name}: {error}")
        return None


async def get_part_info(document_id: str, workspace_id: str, element_id: str, part_id: Optional[str] = None) -> Dict[str, str]:
    """Get part/assembly information from Onshape"""
    
    if part_id:
        # For parts in part studios
        url = f"{ONSHAPE_BASE_URL}/metadata/d/{document_id}/w/{workspace_id}/e/{element_id}/p/{part_id}"
    else:
        # For assemblies or part studios
        url = f"{ONSHAPE_BASE_URL}/metadata/d/{document_id}/w/{workspace_id}/e/{element_id}"
    
    headers = {
        "Accept": "application/json",
        "Authorization": get_auth_header()
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if not response.ok:
            raise Exception(f"HTTP error! status: {response.status_code}")
        
        data = response.json()
        print(data)
        if not data.get("properties") or not isinstance(data["properties"], list):
            return {
                "name": "Unknown",
                "description": ""
            }
        name = None
        description = None
        for property in data["properties"]:
            if property.get("name") == "Name":
                name = property.get("value")
            elif property.get("name") == "Description":
                description = property.get("value")
        return {
            "name": name or "Unknown",
            "description": description or ""
        }
    except Exception as error:
        print(f"Error fetching part info: {error}")
        return {
            "name": "Unknown",
            "description": ""
        }


def compose_part_number(subsystem_number: str, project_code: str, part_uid: int, part_type: str) -> str:
    """Compose part number based on convention"""
    type_map = {
        'Part': 'PRT',
        'Assembly': 'ASM',
        'Drawing': 'DWG',
        'default': 'PRT'
    }
    
    type_code = type_map.get(part_type, type_map['default'])
    
    if project_code == 'NFR':
        return f"NFR-{type_code}-{str(part_uid).zfill(5)}"
    
    return f"{project_code}-{str(subsystem_number).zfill(2)}-{type_code}-{str(part_uid).zfill(5)}"


# Google Sheets setup
creds_path = 'credentials.json' if os.path.exists('credentials.json') else '/secrets/credentials.json'
gc = gspread.service_account(filename=creds_path)
sh = gc.open_by_key('1uTOmapNyBX1aN_QvnkIVoj-CXfeBm_LdSEAp7a-GiNk')

def check_existing_part(document_id: str, element_id: str, part_id: Optional[str] = None) -> Optional[Dict]:
    """Check if part already exists in Google Sheets"""
    try:
        worksheet = sh.worksheet('Master')
        all_records = worksheet.get_all_records()
        
        for record in all_records:
            if (record.get('documentId') == document_id and 
                record.get('elementId') == element_id and
                record.get('partId') == part_id):
                return record
        
        return None
        
    except Exception as e:
        print(f"Error checking existing part: {e}")
        return None


def get_next_free_part_uid() -> int:
    """Get the next available part UID from Google Sheets"""
    try:
        worksheet = sh.worksheet('Master')
        uids = worksheet.col_values(1)[1:]  # Skip header row
        
        if len(uids) == 0:
            return 0 
            
        # Filter out empty cells and convert to integers
        uid_ints = []
        for uid in uids:
            if uid.strip() and uid.strip().isdigit():
                uid_ints.append(int(uid.strip()))
        
        if not uid_ints:
            return 0
        
        perfect_range = set(range(0, max(uid_ints) + 1))
        
        existing_uids = set(uid_ints)
        missing_uids = sorted(perfect_range - existing_uids)
        if missing_uids:
            return missing_uids[0]
        return max(uid_ints) + 1
        
    except Exception as e:
        print(f"Error fetching partUIDs: {e}")
        return None


def add_part_to_google_sheets(part_uid: int, part_number: str, subsystem_id: str, project_code: str, element_id: str, workspace_id: str, document_id: str, company_id: str, part_name: str, part_description: str, part_id: Optional[str], part_type: str):
    """Add part to Google Sheets"""
    try:
        worksheet = sh.worksheet('Master')
        new_row = [part_uid, part_type, part_number, project_code, subsystem_id, part_name, part_description, company_id, document_id, workspace_id, element_id, part_id or '']
        worksheet.append_row(new_row)
        print(f"Part added to Google Sheets: {part_number}")
        return True
    except Exception as error:
        print(f"Error adding part to Google Sheets: {error}")
        return False


app = FastAPI()

@app.post("/generatePartNumber")
async def generate_part_number(request: Request):
    """Generate part numbers for Onshape parts/assemblies"""
    print("Received event:", await request.body())
    
    try:
        request_body = await request.json()
        results = []
        
        for record in request_body:
            id = record.get('id')
            document_id = record.get('documentId')
            element_id = record.get('elementId')
            workspace_id = record.get('workSpaceId')
            company_id = record.get('companyId')
            part_id = record.get('partId')
            element_type = record.get('elementType')
            categories = record.get('categories', [])
            
            print(f"Processing record: documentId={document_id}, elementId={element_id}, partId={part_id}")
            
            # Check if part already exists
            existing_part = check_existing_part(document_id, element_id, part_id)
            if existing_part:
                print(f"Part already exists: {existing_part.get('part_number', 'Unknown')}")
                results.append({
                    "id": id,
                    "documentId": document_id,
                    "elementId": element_id,
                    "workspaceId": workspace_id,
                    "elementType": element_type,
                    "partId": part_id,
                    "partNumber": existing_part.get('part_number')
                })
                continue
            
            # Get document properties
            subsystem_number = await get_document_property(document_id, "Subsystem Number")
            project_code = await get_document_property(document_id, "Project Code")
            
            if subsystem_number is None or not project_code:
                print(f"Missing required document properties: subsystemNumber={subsystem_number}, projectCode={project_code}")
                continue
            
            # Get part information
            part_info = await get_part_info(document_id, workspace_id, element_id, part_id)
            
            # Determine part type from categories
            part_type = 'Part'  # default
            if categories and len(categories) > 0:
                part_type = categories[0].get('name', 'Part')
            else:
                # Try to determine type from element type
                if element_type == 0:
                    part_type = 'Part'
                elif element_type == 1:
                    part_type = 'Assembly'
                elif element_type == 2:
                    part_type = 'Drawing'
                else:
                    part_type = 'Part'
            
            # Get next available part UID
            part_uid = get_next_free_part_uid()
            if part_uid is None:
                print('Failed to generate part UID')
                continue
            
            # Compose part number
            part_number = compose_part_number(subsystem_number, project_code, part_uid, part_type)
            
            # Add to Google Sheets
            success = add_part_to_google_sheets(
                part_uid,
                part_number,
                subsystem_number,
                project_code,
                element_id,
                workspace_id,
                document_id,
                company_id,
                part_info['name'],
                part_info['description'],
                part_id,
                part_type
            )
            
            if success:
                results.append({
                    "id": id,
                    "documentId": document_id,
                    "elementId": element_id,
                    "workspaceId": workspace_id,
                    "elementType": element_type,
                    "partId": part_id,
                    "partNumber": part_number
                })
        
        return results
        
    except Exception as error:
        print('Error processing request:', error)
        return []


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)