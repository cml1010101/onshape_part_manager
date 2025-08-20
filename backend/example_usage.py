"""
Example usage of the Onshape client.

This module demonstrates how to use the OnshapeClient to interact with
Onshape documents and retrieve parts, assemblies, and metadata.
"""

import os
from .onshape_client import OnshapeClient
from .datatypes import Part, Assembly


def create_client() -> OnshapeClient:
    """
    Create an Onshape client with credentials from environment variables.
    
    Set the following environment variables:
    - ONSHAPE_ACCESS_KEY: Your Onshape API access key
    - ONSHAPE_SECRET_KEY: Your Onshape API secret key
    
    Returns:
        Configured OnshapeClient instance
    """
    access_key = os.getenv('ONSHAPE_ACCESS_KEY')
    secret_key = os.getenv('ONSHAPE_SECRET_KEY')
    
    if not access_key or not secret_key:
        print("Warning: Onshape API credentials not found in environment variables.")
        print("Set ONSHAPE_ACCESS_KEY and ONSHAPE_SECRET_KEY to use the client.")
    
    return OnshapeClient(access_key=access_key, secret_key=secret_key)


def get_all_document_data(document_id: str, workspace_id: str = "w"):
    """
    Get all parts and assemblies from a document.
    
    Args:
        document_id: The Onshape document ID
        workspace_id: The workspace ID (default: "w" for main workspace)
        
    Returns:
        Tuple of (parts_list, assemblies_list)
    """
    client = create_client()
    
    print(f"Fetching data from document: {document_id}")
    
    # Get document info
    doc_info = client.get_document_info(document_id)
    print(f"Document name: {doc_info.get('name', 'Unknown')}")
    
    # Get all parts
    print("Fetching parts...")
    parts = client.get_document_parts(document_id, workspace_id)
    print(f"Found {len(parts)} parts")
    
    # Get all assemblies
    print("Fetching assemblies...")
    assemblies = client.get_document_assemblies(document_id, workspace_id)
    print(f"Found {len(assemblies)} assemblies")
    
    return parts, assemblies


def print_parts_summary(parts: list[Part]):
    """Print a summary of parts."""
    print("\n=== PARTS SUMMARY ===")
    for part in parts:
        print(f"ID: {part._id}")
        print(f"Name: {part.name}")
        print(f"Description: {part.description}")
        print(f"Material: {part.material}")
        print("-" * 40)


def print_assemblies_summary(assemblies: list[Assembly]):
    """Print a summary of assemblies."""
    print("\n=== ASSEMBLIES SUMMARY ===")
    for assembly in assemblies:
        print(f"ID: {assembly._id}")
        print(f"Name: {assembly.name}")
        print(f"Description: {assembly.description}")
        print("-" * 40)


if __name__ == "__main__":
    # Example usage
    # Replace with your actual document ID
    EXAMPLE_DOCUMENT_ID = "your-document-id-here"
    
    if EXAMPLE_DOCUMENT_ID != "your-document-id-here":
        parts, assemblies = get_all_document_data(EXAMPLE_DOCUMENT_ID)
        print_parts_summary(parts)
        print_assemblies_summary(assemblies)
    else:
        print("Please set EXAMPLE_DOCUMENT_ID to a real Onshape document ID to test.")
        print("Also ensure ONSHAPE_ACCESS_KEY and ONSHAPE_SECRET_KEY are set.")