"""
Onshape API client for managing parts, assemblies, and metadata.

This module provides a client to interact with the Onshape REST API
to retrieve parts from documents, find assemblies, and manage metadata.
"""

import requests
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import base64
import hashlib
import hmac
import time
from datetime import datetime

from .datatypes import Part, Assembly


class OnshapeClient:
    """Client for interacting with the Onshape REST API."""
    
    def __init__(self, base_url: str = "https://cad.onshape.com", 
                 access_key: Optional[str] = None, 
                 secret_key: Optional[str] = None):
        """
        Initialize the Onshape client.
        
        Args:
            base_url: The base URL for the Onshape API
            access_key: Onshape API access key 
            secret_key: Onshape API secret key
        """
        self.base_url = base_url.rstrip('/')
        self.access_key = access_key
        self.secret_key = secret_key
        self.session = requests.Session()
        
    def _build_auth_header(self, method: str, path: str, query: str = "", 
                          content_type: str = "application/json") -> Dict[str, str]:
        """
        Build authentication header for Onshape API requests.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            query: Query string parameters
            content_type: Content type header
            
        Returns:
            Dictionary containing authorization header
        """
        if not self.access_key or not self.secret_key:
            return {}
            
        # Current time in ISO format
        date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Build the string to sign
        string_to_sign = f"{method}\n{content_type}\n{date}\n{path}"
        if query:
            string_to_sign += f"?{query}"
            
        # Create signature
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Build authorization header
        auth_header = f"On {self.access_key}:HmacSHA256:{signature}"
        
        return {
            'Authorization': auth_header,
            'Date': date,
            'Content-Type': content_type
        }
    
    def _make_request(self, method: str, endpoint: str, 
                     params: Optional[Dict[str, Any]] = None,
                     data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make an authenticated request to the Onshape API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            
        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        
        # Build query string
        query_string = ""
        if params:
            query_string = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        
        # Get auth headers
        headers = self._build_auth_header(method.upper(), endpoint, query_string)
        
        # Make request
        if method.upper() == 'GET':
            response = self.session.get(url, params=params, headers=headers)
        elif method.upper() == 'POST':
            response = self.session.post(url, params=params, json=data, headers=headers)
        elif method.upper() == 'PUT':
            response = self.session.put(url, params=params, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        response.raise_for_status()
        return response
    
    def get_document_parts(self, document_id: str, workspace_id: str = "w") -> List[Part]:
        """
        Get all parts from all part studios in a document.
        
        Args:
            document_id: The Onshape document ID
            workspace_id: The workspace ID (default: "w" for main workspace)
            
        Returns:
            List of Part objects found in the document
        """
        parts = []
        
        try:
            # Get all elements in the document
            endpoint = f"/api/v6/documents/{document_id}/{workspace_id}/elements"
            response = self._make_request('GET', endpoint)
            elements = response.json()
            
            # Filter part studios
            part_studios = [elem for elem in elements if elem.get('elementType') == 'PARTSTUDIO']
            
            # Get parts from each part studio
            for studio in part_studios:
                studio_id = studio['id']
                studio_parts = self._get_parts_from_studio(document_id, workspace_id, studio_id)
                parts.extend(studio_parts)
                
        except requests.RequestException as e:
            print(f"Error fetching document parts: {e}")
            
        return parts
    
    def _get_parts_from_studio(self, document_id: str, workspace_id: str, 
                              element_id: str) -> List[Part]:
        """
        Get parts from a specific part studio.
        
        Args:
            document_id: The Onshape document ID
            workspace_id: The workspace ID
            element_id: The part studio element ID
            
        Returns:
            List of Part objects from the part studio
        """
        parts = []
        
        try:
            # Get parts from part studio
            endpoint = f"/api/v6/partstudios/d/{document_id}/{workspace_id}/e/{element_id}/parts"
            response = self._make_request('GET', endpoint)
            parts_data = response.json()
            
            for part_data in parts_data:
                # Get metadata for the part
                metadata = self._get_part_metadata(document_id, workspace_id, 
                                                 element_id, part_data['partId'])
                
                part = Part(
                    _id=hash(part_data['partId']),  # Generate numeric ID from part ID
                    name=part_data.get('name', ''),
                    description=metadata.get('description', ''),
                    drawing=metadata.get('drawing', ''),
                    material=part_data.get('material', {}).get('name', ''),
                    stl_file=None  # STL file would need separate export
                )
                parts.append(part)
                
        except requests.RequestException as e:
            print(f"Error fetching parts from studio {element_id}: {e}")
            
        return parts
    
    def get_document_assemblies(self, document_id: str, workspace_id: str = "w") -> List[Assembly]:
        """
        Find all assemblies in a document.
        
        Args:
            document_id: The Onshape document ID
            workspace_id: The workspace ID (default: "w" for main workspace)
            
        Returns:
            List of Assembly objects found in the document
        """
        assemblies = []
        
        try:
            # Get all elements in the document
            endpoint = f"/api/v6/documents/{document_id}/{workspace_id}/elements"
            response = self._make_request('GET', endpoint)
            elements = response.json()
            
            # Filter assemblies
            assembly_elements = [elem for elem in elements if elem.get('elementType') == 'ASSEMBLY']
            
            for asm_elem in assembly_elements:
                metadata = self._get_assembly_metadata(document_id, workspace_id, asm_elem['id'])
                
                assembly = Assembly(
                    _id=hash(asm_elem['id']),  # Generate numeric ID from element ID
                    name=asm_elem.get('name', ''),
                    description=metadata.get('description', ''),
                    drawing=metadata.get('drawing', '')
                )
                assemblies.append(assembly)
                
        except requests.RequestException as e:
            print(f"Error fetching document assemblies: {e}")
            
        return assemblies
    
    def _get_part_metadata(self, document_id: str, workspace_id: str, 
                          element_id: str, part_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific part.
        
        Args:
            document_id: The Onshape document ID
            workspace_id: The workspace ID
            element_id: The element ID
            part_id: The part ID
            
        Returns:
            Dictionary containing part metadata
        """
        try:
            endpoint = f"/api/v6/metadata/d/{document_id}/{workspace_id}/e/{element_id}/p/{part_id}"
            response = self._make_request('GET', endpoint)
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching part metadata: {e}")
            return {}
    
    def _get_assembly_metadata(self, document_id: str, workspace_id: str, 
                              element_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific assembly.
        
        Args:
            document_id: The Onshape document ID
            workspace_id: The workspace ID
            element_id: The assembly element ID
            
        Returns:
            Dictionary containing assembly metadata
        """
        try:
            endpoint = f"/api/v6/metadata/d/{document_id}/{workspace_id}/e/{element_id}"
            response = self._make_request('GET', endpoint)
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching assembly metadata: {e}")
            return {}
    
    def update_part_metadata(self, document_id: str, workspace_id: str, 
                           element_id: str, part_id: str, 
                           metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a specific part.
        
        Args:
            document_id: The Onshape document ID
            workspace_id: The workspace ID
            element_id: The element ID
            part_id: The part ID
            metadata: Dictionary containing metadata to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            endpoint = f"/api/v6/metadata/d/{document_id}/{workspace_id}/e/{element_id}/p/{part_id}"
            response = self._make_request('POST', endpoint, data=metadata)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Error updating part metadata: {e}")
            return False
    
    def update_assembly_metadata(self, document_id: str, workspace_id: str, 
                               element_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a specific assembly.
        
        Args:
            document_id: The Onshape document ID
            workspace_id: The workspace ID
            element_id: The assembly element ID
            metadata: Dictionary containing metadata to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            endpoint = f"/api/v6/metadata/d/{document_id}/{workspace_id}/e/{element_id}"
            response = self._make_request('POST', endpoint, data=metadata)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Error updating assembly metadata: {e}")
            return False
    
    def get_document_info(self, document_id: str) -> Dict[str, Any]:
        """
        Get basic information about a document.
        
        Args:
            document_id: The Onshape document ID
            
        Returns:
            Dictionary containing document information
        """
        try:
            endpoint = f"/api/v6/documents/{document_id}"
            response = self._make_request('GET', endpoint)
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching document info: {e}")
            return {}