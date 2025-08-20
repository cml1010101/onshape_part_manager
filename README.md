# onshape_part_manager
A way to easily manage part numbering and production on onshape

## Onshape Client

This repository now includes an Onshape API client that provides helper functions to:

- Get all parts in a document (from all part studios)
- Find all assemblies in a document  
- Get and edit metadata for parts and assemblies

### Setup

1. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

2. Set up your Onshape API credentials as environment variables:
```bash
export ONSHAPE_ACCESS_KEY="your_access_key_here"
export ONSHAPE_SECRET_KEY="your_secret_key_here"
```

You can get API keys from your Onshape account at: https://dev-portal.onshape.com/keys

### Usage

```python
from backend import OnshapeClient, Part, Assembly

# Create client (credentials from environment variables)
client = OnshapeClient(access_key="your_key", secret_key="your_secret")

# Get all parts from a document
document_id = "your_document_id"
parts = client.get_document_parts(document_id)

# Get all assemblies from a document  
assemblies = client.get_document_assemblies(document_id)

# Get document information
doc_info = client.get_document_info(document_id)

# Update part metadata
success = client.update_part_metadata(
    document_id, "w", element_id, part_id, 
    {"description": "Updated description"}
)

# Update assembly metadata
success = client.update_assembly_metadata(
    document_id, "w", element_id,
    {"drawing": "new_drawing.pdf"}
)
```

### Example Usage

See `backend/example_usage.py` for a complete example of how to use the client to fetch and display parts and assemblies from a document.

### API Methods

The `OnshapeClient` provides the following methods:

- `get_document_parts(document_id, workspace_id)` - Get all Part objects from all part studios
- `get_document_assemblies(document_id, workspace_id)` - Get all Assembly objects  
- `update_part_metadata(document_id, workspace_id, element_id, part_id, metadata)` - Update part metadata
- `update_assembly_metadata(document_id, workspace_id, element_id, metadata)` - Update assembly metadata
- `get_document_info(document_id)` - Get basic document information

All methods return data using the existing dataclasses defined in `backend/datatypes.py`.
