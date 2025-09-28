from fastapi import FastAPI, Request
import uvicorn
import requests
import os
import base64
from typing import Any, Optional, Dict, List
import gspread

ONSHAPE_API_KEY = os.getenv("ONSHAPE_API_KEY")
ONSHAPE_API_SECRET = os.getenv("ONSHAPE_API_SECRET")
ONSHAPE_BASE_URL = "https://cad.onshape.com/api/v12"


def get_auth_header() -> str:
    """Generate the basic authentication header for Onshape API"""
    credentials = f"{ONSHAPE_API_KEY}:{ONSHAPE_API_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"


async def get_document_properties(document_id: str) -> Dict[str, Any]:
    """Fetch document properties from Onshape API"""
    url = f"{ONSHAPE_BASE_URL}/metadata/d/{document_id}"
    headers = {
        "Accept": "application/json",
        "Authorization": get_auth_header()
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if "properties" in data and isinstance(data["properties"], list):
            # Convert properties list to a more convenient dict format
            properties_dict = {}
            for prop in data["properties"]:
                if "name" in prop and "value" in prop:
                    properties_dict[prop["name"]] = prop["value"]
            return properties_dict
        
        return {}
    except requests.exceptions.RequestException as error:
        print(f"Error fetching document properties: {error}")
        return {}


async def get_document_property(document_id: str, property_name: str) -> Optional[str]:
    """Fetch a specific document property from Onshape API"""
    url = f"{ONSHAPE_BASE_URL}/metadata/d/{document_id}"
    headers = {
        "Accept": "application/json",
        "Authorization": get_auth_header()
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if "properties" in data and isinstance(data["properties"], list):
            for prop in data["properties"]:
                if prop.get("name") == property_name:
                    return prop.get("value")
        
        return None
    except requests.exceptions.RequestException as error:
        print(f"Error fetching document property {property_name}: {error}")
        return None


async def get_part_info(document_id: str, workspace_id: str, element_id: str, part_id: Optional[str] = None) -> Dict[str, str]:
    """Get part/assembly information from Onshape"""
    
    # Handle JFD (Just For Display) parts - these are derived/reference parts
    if part_id and part_id.upper() == "JFD":
        print(f"Handling JFD (derived/reference) part: {part_id}")
        # For JFD parts, we can't get individual part metadata, so get element info instead
        url = f"{ONSHAPE_BASE_URL}/elements/d/{document_id}/w/{workspace_id}/e/{element_id}"
        headers = {
            "Accept": "application/json",
            "Authorization": get_auth_header()
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # For JFD parts, use element name with JFD suffix to distinguish
            element_name = data.get("name", "Unnamed Element")
            return {
                "name": f"{element_name} (JFD Reference)",
                "description": f"Derived/reference part from {element_name}"
            }
        except requests.exceptions.RequestException as error:
            print(f"Error fetching element info for JFD part: {error}")
            return {
                "name": "JFD Reference Part",
                "description": "Derived/reference part (metadata unavailable)"
            }
    
    # Handle regular parts
    if part_id and part_id.upper() != "JFD":
        # For parts in part studios
        url = f"{ONSHAPE_BASE_URL}/parts/d/{document_id}/w/{workspace_id}/e/{element_id}/partid/{part_id}"
    else:
        # For assemblies or part studios without specific part ID
        url = f"{ONSHAPE_BASE_URL}/elements/d/{document_id}/w/{workspace_id}/e/{element_id}"
    
    headers = {
        "Accept": "application/json",
        "Authorization": get_auth_header()
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if part_id and part_id.upper() != "JFD":
            return {
                "name": data.get("name", "Unnamed Part"),
                "description": data.get("description", "")
            }
        else:
            return {
                "name": data.get("name", "Unnamed Element"),
                "description": data.get("description", "")
            }
    except requests.exceptions.RequestException as error:
        print(f"Error fetching part info: {error}")
        return {
            "name": "Unknown",
            "description": ""
        }


async def get_parts_in_partstudio(document_id: str, workspace_id: str, element_id: str) -> list:
    """Get all parts in a part studio"""
    url = f"{ONSHAPE_BASE_URL}/parts/d/{document_id}/w/{workspace_id}/e/{element_id}"
    headers = {
        "Accept": "application/json",
        "Authorization": get_auth_header()
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data if isinstance(data, list) else []
    except requests.exceptions.RequestException as error:
        print(f"Error fetching parts in partstudio: {error}")
        return []


async def get_assemblies_in_document(document_id: str, workspace_id: str) -> list:
    """Get all assemblies in a document"""
    url = f"{ONSHAPE_BASE_URL}/assemblies/d/{document_id}/w/{workspace_id}"
    headers = {
        "Accept": "application/json",
        "Authorization": get_auth_header()
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data if isinstance(data, list) else []
    except requests.exceptions.RequestException as error:
        print(f"Error fetching assemblies: {error}")
        return []


def compose_part_number(subsystem_number: str, project_code: str, part_uid: int, part_type: str) -> str:
    """Compose part number based on convention"""
    type_map = {
        'Part': 'PRT',
        'Assembly': 'ASM',
        'Drawing': 'DRW',
        'Derived': 'DRV',  # Add support for derived/JFD parts
        'Reference': 'REF',  # Alternative for derived parts
        'default': 'PRT'
    }
    
    type_code = type_map.get(part_type, type_map['default'])
    
    if project_code == 'NFR':
        return f"NFR-{type_code}-{str(part_uid).zfill(5)}"
    
    return f"{project_code}-{str(subsystem_number).zfill(2)}-{type_code}-{str(part_uid).zfill(5)}"

creds_path = 'credentials.json' if os.path.exists('credentials.json') else '/secrets/credentials.json'
gc = gspread.service_account(filename=creds_path)
sh = gc.open_by_key('1uTOmapNyBX1aN_QvnkIVoj-CXfeBm_LdSEAp7a-GiNk')

def get_next_free_part_uid() -> int:
    """Get the next available part UID from the Google Sheet"""
    try:
        worksheet = sh.worksheet('Master')
        uids = worksheet.col_values(1)[1:]  # Skip header row
        
        if not uids:
            return 0  # Start from 0 for first part
            
        # Filter out empty cells and convert to integers
        uid_ints = []
        for uid in uids:
            if uid.strip() and uid.strip().isdigit():
                uid_ints.append(int(uid.strip()))
        
        if not uid_ints:
            return 1000
            
        return max(uid_ints) + 1
        
    except Exception as e:
        print(f"Error getting next part UID: {e}")
        return 1000


def check_existing_part(document_id: str, element_id: str, part_id: Optional[str] = None) -> Optional[Dict]:
    """Check if part already exists in Google Sheets"""
    try:
        worksheet = sh.worksheet('Master')
        all_records = worksheet.get_all_records()
        
        for record in all_records:
            # Check if this part already exists
            if (record.get('documentId') == document_id and 
                record.get('elementId') == element_id):
                
                # Handle JFD parts comparison
                if part_id:
                    if part_id.upper() == "JFD":
                        # For JFD parts, match if existing record also has JFD
                        if record.get('partId', '').upper() == "JFD":
                            return record
                    else:
                        # Regular part ID matching
                        if record.get('partId') == part_id:
                            return record
                else:
                    # No part ID specified, should match empty part ID
                    if not record.get('partId') or record.get('partId') == '':
                        return record
        
        return None
        
    except Exception as e:
        print(f"Error checking existing part: {e}")
        return None


def append_part(uid: int, type: str, part_number: str, project_code: str, subsystem_number: int, name: str, description: str, documentId: str, companyId: str, workspaceId: str, elementId: str, partId: str):
    """Append a new part entry to the Google Sheet"""
    try:
        worksheet = sh.worksheet('Master')
        new_row = [uid, type, part_number, project_code, subsystem_number, name, description, documentId, companyId, workspaceId, elementId, partId or '']
        worksheet.append_row(new_row)
        return True
    except Exception as e:
        print(f"Error appending to Google Sheet: {e}")
        return False

app = FastAPI()

@app.post("/generatePartNumber")
async def generate_part_number(request: Request):
    """Generate part numbers for Onshape parts/assemblies"""
    try:
        data = await request.json()
        results = []
        
        # Handle both single record and array of records
        records = data if isinstance(data, list) else [data]
        
        for record in records:
            document_id = record.get('documentId')
            element_id = record.get('elementId')
            workspace_id = record.get('workSpaceId')  # Note: matches Node.js naming
            part_id = record.get('partId')
            element_type = record.get('elementType')
            categories = record.get('categories', [])
            company_id = record.get('companyId', '')
            
            print(f"Processing record: documentId={document_id}, elementId={element_id}, partId={part_id}")
            
            # Special handling for JFD parts
            if part_id and part_id.upper() == "JFD":
                print(f"Detected JFD (derived/reference) part: {part_id}")
            
            # Validate required fields
            if not all([document_id, element_id, workspace_id]):
                print(f"Missing required fields for record")
                continue
            
            # Check if part already exists
            existing_part = check_existing_part(document_id, element_id, part_id)
            if existing_part:
                print(f"Part already exists: {existing_part.get('part_number', 'Unknown')}")
                results.append({
                    "id": existing_part.get('uid'),
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
            
            if not subsystem_number or not project_code:
                print(f"Missing required document properties: subsystemNumber={subsystem_number}, projectCode={project_code}")
                continue
            
            # Get part information (handles JFD parts appropriately)
            part_info = await get_part_info(document_id, workspace_id, element_id, part_id)
            
            # Determine part type from categories or part_id
            part_type = 'Part'  # default
            
            # Special handling for JFD parts
            if part_id and part_id.upper() == "JFD":
                part_type = 'Derived'  # or 'Reference' - you can choose the naming convention
            elif categories and len(categories) > 0:
                part_type = categories[0].get('name', 'Part')
            else:
                # Try to determine type from element type
                if element_type == 0:
                    part_type = 'Part'
                elif element_type == 1:
                    part_type = 'Assembly'
                else:
                    part_type = 'Part'
            
            # Get next available part UID
            part_uid = get_next_free_part_uid()
            if not part_uid:
                print('Failed to generate part UID')
                continue
            
            # Compose part number (may need to add 'DRV' for derived parts)
            part_number = compose_part_number(subsystem_number, project_code, part_uid, part_type)
            
            # Add to Google Sheets
            success = append_part(
                part_uid,
                part_type,
                part_number,
                project_code,
                int(subsystem_number),
                part_info['name'],
                part_info['description'],
                document_id,
                company_id,
                workspace_id,
                element_id,
                part_id or ''  # Store JFD as-is
            )
            
            if success:
                results.append({
                    "id": part_uid,
                    "documentId": document_id,
                    "elementId": element_id,
                    "workspaceId": workspace_id,
                    "elementType": element_type,
                    "partId": part_id,
                    "partNumber": part_number
                })
                print(f"Successfully created part number: {part_number} for {'JFD reference' if part_id and part_id.upper() == 'JFD' else 'regular'} part")
        
        return results
        
    except Exception as error:
        print(f'Error processing request: {error}')
        return []

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)