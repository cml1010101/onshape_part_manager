# Onshape Part Manager

A FastAPI microservice that automatically generates standardized part numbers for Onshape CAD documents and tracks them in Google Sheets. It is designed to be called from an Onshape [release management workflow](https://cad.onshape.com/help/Content/releasemanagement.htm) or any integration that can POST JSON to an HTTP endpoint.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Google Sheets Service Account](#google-sheets-service-account)
  - [Google Sheet Structure](#google-sheet-structure)
  - [Onshape Document Properties](#onshape-document-properties)
- [Running the Service](#running-the-service)
  - [Local Development](#local-development)
  - [Docker](#docker)
- [API Reference](#api-reference)
  - [GET /health](#get-health)
  - [POST /generatePartNumber](#post-generatepartnumber)
- [Part Number Format](#part-number-format)
- [Architecture & How It Works](#architecture--how-it-works)
  - [Request Flow](#request-flow)
  - [Code Structure](#code-structure)
  - [Key Functions](#key-functions)
- [How to Modify](#how-to-modify)
  - [Changing the Part Number Format](#changing-the-part-number-format)
  - [Changing the Google Sheet](#changing-the-google-sheet)
  - [Adding New Element Types](#adding-new-element-types)
  - [Changing the Port](#changing-the-port)

---

## Overview

When a part, assembly, or drawing is released in Onshape, this service:

1. Checks whether that item already has a part number (deduplication).
2. Reads `Project Code` and `Subsystem Number` metadata from the Onshape document.
3. Fetches the item's name and description from the Onshape Metadata API.
4. Assigns the next available sequential UID, filling in gaps if any exist.
5. Composes a human-readable part number following the team's naming convention.
6. Appends a row to the **Master** worksheet in a Google Sheet for tracking.
7. Returns the generated part number to the caller.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | Or use the provided Docker image |
| Onshape API key & secret | Generate in *Onshape Account Settings → API Keys* |
| Google Cloud service account | Needs **Editor** access to the target spreadsheet |
| Google Sheet | See [Google Sheet Structure](#google-sheet-structure) |

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ONSHAPE_API_KEY` | Yes | Onshape API access key |
| `ONSHAPE_API_SECRET` | Yes | Onshape API secret |

Set these before starting the server:

```bash
export ONSHAPE_API_KEY="your-api-key"
export ONSHAPE_API_SECRET="your-api-secret"
```

Or place them in a `.env` file (excluded from git by `.gitignore`).

### Google Sheets Service Account

Authentication to Google Sheets is handled via a **service account JSON key file**.

1. Create a service account in [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts).
2. Grant the service account **Editor** role on the target spreadsheet (share the sheet with the service account email).
3. Download the JSON key and save it as one of:
   - `credentials.json` in the project root (local development), **or**
   - `/secrets/credentials.json` (Docker/production — mount it as a volume or secret).

The application checks for `credentials.json` in the working directory first, then falls back to `/secrets/credentials.json`.

### Google Sheet Structure

The service writes to a worksheet named **Master** inside the spreadsheet identified by the key in `app.py` (`sh = gc.open_by_key(...)`).

The sheet must have the following columns **in this exact order** (row 1 is the header row and is skipped when reading):

| Column | Header | Description |
|---|---|---|
| A | `part_uid` | Auto-assigned sequential integer UID |
| B | `url` | Direct link to the element in Onshape |
| C | `part_type` | `Part`, `Assembly`, or `Drawing` |
| D | `part_number` | Generated part number string |
| E | `project_code` | Project code from document properties |
| F | `subsystem_id` | Subsystem number from document properties |
| G | `part_name` | Name from Onshape metadata |
| H | `part_description` | Description from Onshape metadata |
| I | `company_id` | Company ID from the request |
| J | `documentId` | Onshape document ID |
| K | `workspaceId` | Onshape workspace ID |
| L | `elementId` | Onshape element ID |
| M | `partId` | Onshape part ID (empty for assemblies/drawings) |

To point the service at a **different** spreadsheet, update the key string in `app.py`:

```python
sh = gc.open_by_key('YOUR_SPREADSHEET_KEY_HERE')
```

### Onshape Document Properties

Each Onshape document must have two custom properties configured before part numbers can be generated:

| Property Name | Example Value | Description |
|---|---|---|
| `Project Code` | `NFR`, `ABC` | Short project identifier |
| `Subsystem Number` | `01`, `07` | Two-digit subsystem identifier |

These are set in **Onshape → Document Properties** and are fetched via the Metadata API at request time. If either property is missing, the record is skipped and no part number is returned for it.

---

## Running the Service

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/NorthernForce/onshape_part_manager.git
cd onshape_part_manager

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export ONSHAPE_API_KEY="your-api-key"
export ONSHAPE_API_SECRET="your-api-secret"

# 5. Place credentials.json in the project root

# 6. Start the server
python3 app.py
```

The service starts on `http://localhost:8080`. Visit `http://localhost:8080/health` to confirm it is running.

### Docker

```bash
# Build the image
docker build -t onshape-part-manager .

# Run the container
docker run -p 8080:8080 \
  -e ONSHAPE_API_KEY="your-api-key" \
  -e ONSHAPE_API_SECRET="your-api-secret" \
  -v /absolute/path/to/credentials.json:/secrets/credentials.json \
  onshape-part-manager
```

The container exposes port **8080**. Adjust `-p` to map to a different host port if needed.

---

## API Reference

### GET /health

Returns a simple status string to confirm the service is alive.

**Response**

```
200 OK
"Doin' fine, how 'bout you?"
```

---

### POST /generatePartNumber

Accepts a JSON array of part records, generates part numbers for each, and returns the successful results.

**Request Body**

```json
[
  {
    "id": "unique-record-id",
    "documentId": "abc123",
    "elementId": "def456",
    "workSpaceId": "ghi789",
    "companyId": "jkl012",
    "partId": "mno345",
    "elementType": 0,
    "categories": [
      { "name": "Part" }
    ]
  }
]
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Caller-assigned identifier echoed back in the response |
| `documentId` | string | Yes | Onshape document ID |
| `elementId` | string | Yes | Onshape element (tab) ID |
| `workSpaceId` | string | Yes | Onshape workspace ID |
| `companyId` | string | Yes | Onshape company ID |
| `partId` | string | No | Part ID within a Part Studio; omit for assemblies and drawings |
| `elementType` | integer | No | `0` = Part Studio, `1` = Assembly, `2` = Drawing (used when `categories` is empty) |
| `categories` | array | No | Array of category objects; the `name` of the first entry sets the part type |

**Response**

```json
[
  {
    "id": "unique-record-id",
    "documentId": "abc123",
    "elementId": "def456",
    "workspaceId": "ghi789",
    "elementType": 0,
    "partId": "mno345",
    "partNumber": "ABC-07-PRT-00001"
  }
]
```

Records are omitted from the response if:
- Required document properties (`Project Code`, `Subsystem Number`) are missing.
- Writing to Google Sheets fails.

Records for parts that **already exist** in Google Sheets are included in the response with their previously assigned part number and are not written again.

---

## Part Number Format

Part numbers follow one of two formats depending on the project code.

**Standard projects:**

```
{PROJECT_CODE}-{SUBSYSTEM_NUMBER}-{TYPE_CODE}-{UID}
```

Example: `ABC-07-PRT-00042`

**NFR (internal) projects:**

```
NFR-{TYPE_CODE}-{UID}
```

Example: `NFR-ASM-00001`

| Placeholder | Description |
|---|---|
| `PROJECT_CODE` | Value of the `Project Code` document property |
| `SUBSYSTEM_NUMBER` | Value of the `Subsystem Number` property, zero-padded to 2 digits |
| `TYPE_CODE` | `PRT` (Part), `ASM` (Assembly), or `DWG` (Drawing) |
| `UID` | Sequential integer, zero-padded to 5 digits; gaps in existing UIDs are filled first |

---

## Architecture & How It Works

```
Onshape / caller
      │
      │  POST /generatePartNumber (JSON array)
      ▼
┌─────────────────────────────────┐
│          FastAPI (app.py)        │
│                                  │
│  1. Deduplicate via Sheets query │
│  2. Fetch doc properties         │◄──► Onshape Metadata API
│  3. Fetch part name/description  │
│  4. Pick next free UID           │◄──► Google Sheets (Master)
│  5. Compose part number          │
│  6. Append row to Sheets         │──► Google Sheets (Master)
│  7. Return results               │
└─────────────────────────────────┘
      │
      │  JSON array of {id, partNumber, ...}
      ▼
   Caller
```

### Request Flow

1. **Receive** – The `/generatePartNumber` endpoint receives a JSON array; each element represents one item to number.
2. **Deduplicate** – `check_existing_part()` reads all rows from the Master sheet and looks for a matching `documentId` + `elementId` + `partId`. If found, the existing part number is returned immediately for that record.
3. **Fetch document properties** – `get_document_property()` calls the Onshape Metadata API (`/metadata/d/{documentId}`) to retrieve `Project Code` and `Subsystem Number`.
4. **Fetch part metadata** – `get_part_info()` calls the Onshape Metadata API for the specific element (or part within a Part Studio) to retrieve its `Name` and `Description`.
5. **Assign UID** – `get_next_free_part_uid()` reads column A of the Master sheet, finds the lowest positive integer not already used, and returns it.
6. **Compose number** – `compose_part_number()` assembles the final string using the project code, subsystem number, type code, and UID.
7. **Persist** – `add_part_to_google_sheets()` appends a new row to the Master sheet.
8. **Return** – Successfully numbered records are collected and returned as a JSON array.

### Code Structure

```
app.py          Single-file application containing all logic
requirements.txt Python package dependencies
Dockerfile      Container build instructions
.gitignore      Excludes .venv, .env, and credentials.json
```

### Key Functions

| Function | Location | Purpose |
|---|---|---|
| `get_auth_header()` | `app.py:14` | Builds the `Basic` auth header for Onshape API calls |
| `get_document_property()` | `app.py:21` | Fetches one named property from a document's metadata |
| `get_part_info()` | `app.py:48` | Returns name and description of a part or assembly element |
| `compose_part_number()` | `app.py:95` | Builds the part number string from its components |
| `check_existing_part()` | `app.py:117` | Queries Google Sheets to detect duplicates |
| `get_next_free_part_uid()` | `app.py:136` | Finds the lowest unused integer UID |
| `add_part_to_google_sheets()` | `app.py:167` | Appends a new row to the Master worksheet |
| `compose_part_url()` | `app.py:179` | Builds the Onshape web URL for an element |

---

## How to Modify

### Changing the Part Number Format

Edit `compose_part_number()` in `app.py`. The function receives `subsystem_number`, `project_code`, `part_uid`, and `part_type` and returns a string.

```python
def compose_part_number(subsystem_number: str, project_code: str, part_uid: int, part_type: str) -> str:
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
```

To add a new type abbreviation, extend `type_map`. To change zero-padding width, adjust the `zfill()` argument.

### Changing the Google Sheet

1. Update the spreadsheet key in `app.py`:
   ```python
   sh = gc.open_by_key('YOUR_NEW_SPREADSHEET_KEY')
   ```
2. If you rename the worksheet, update the string argument passed to `sh.worksheet()` in every function that calls it (`check_existing_part`, `get_next_free_part_uid`, `add_part_to_google_sheets`).
3. If you add or reorder columns, update the `new_row` list in `add_part_to_google_sheets()` and the column indices used in `get_next_free_part_uid()` and `check_existing_part()`.

### Adding New Element Types

Onshape `elementType` values beyond 0, 1, and 2 can be handled by extending the `if/elif` block inside `/generatePartNumber`:

```python
elif element_type == 3:
    part_type = 'Cable'
```

Then add the corresponding abbreviation to `type_map` in `compose_part_number()`:

```python
'Cable': 'CBL',
```

### Changing the Port

The server listens on port **8080** by default. To use a different port, change the `uvicorn.run` call at the bottom of `app.py`:

```python
uvicorn.run(app, host="0.0.0.0", port=YOUR_PORT)
```

Also update the `EXPOSE` line in the `Dockerfile` to match.
