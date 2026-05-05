# TI Connectivity Toolbox - Agent Guidelines

## Project Purpose

TI Connectivity Toolbox is a desktop app-store for Texas Instruments applications. Users browse, install, and uninstall TI apps through an Angular client that communicates with a local Flask server.

## Architecture

**Multi-tier (3-layer) architecture:**

| Layer | Directory | Responsibility |
|-------|-----------|----------------|
| Presentation | `app/controllers/` | HTTP endpoints, request/response handling |
| Application | `app/services/` | Business logic, orchestration |
| Data | `app/repositories/` | External API calls, filesystem operations |

**Models** (`app/models/`) contain dataclasses shared across all layers.

---

## Tech Stack

- **Server:** Python Flask
- **Client:** Angular (separate repo)
- **Communication:** REST API + Server-Sent Events (SSE) for streaming
- **Storage:** Local filesystem for installed apps, remote GitHub for app releases

---

## Data Flow

```
GitHub Raw (apps.json) ──► Server ──► Angular Client
         │                   │
         │                   ▼
         │            GitHub API (releases, manifests)
         │                   │
         ▼                   ▼
   apps.json           <CT_PATH>/apps/{app_id}/
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/fetch-data` | Fetch all apps with details |

**Future endpoints:**
- `GET /api/apps/{id}/releases` - List all versions
- `GET /api/apps/{id}/diff/{v1}/{v2}` - Compare versions
- `GET /api/install-app/{id}/{version}` - Install app (SSE)
- `GET /api/uninstall-app/{id}` - Uninstall app (SSE)

---

## Data Models

### AppModel (returned to client)
```python
@dataclass
class AppModel:
    id: str
    name: str
    description: str
    versions: List[str]
    status: Literal["not installed", "update available", "up to date"]
    supportedOS: List[str]
    installedVersion: Optional[str] = None
    iconPath: Optional[str] = None
```

### ManifestModel (manifest.json in each GitHub release)
```python
@dataclass
class ManifestModel:
    name: str
    description: str
    version: str
    supportedOS: Dict[str, str]  # {"win32": "path/to/app.exe"}
    iconPath: Optional[str] = None
```

### ReleaseModel (GitHub releases)
```python
@dataclass
class ReleaseModel:
    version: str
    zipball_url: str
    tarball_url: str
```

### DbItem (apps.json - remote app registry)
```python
@dataclass
class DbItem:
    owner: str
    repo: str
```

---

## Key Conventions

### OS Detection
- Uses Python's `sys.platform`: `win32`, `darwin`, `linux`
- Apps without current OS in `supportedOS` are filtered out

### App Installation Path
- Default: `<SYSTEM_DRIVE>:\Connectivity-Toolbox\apps\{app_id}\`
- Configurable via `app/config/config.py`

### GitHub Integration
- apps.json: `https://raw.githubusercontent.com/ShivaShenkar/TI-Server/main/db/apps.json`
- Releases API: `https://api.github.com/repos/{owner}/{repo}/releases`
- Manifest: `https://raw.githubusercontent.com/{owner}/{repo}/{version}/manifest.json`

### Status Values
- `not installed` - App folder doesn't exist locally
- `update available` - Local version differs from latest
- `up to date` - Versions match

---

## Layer Responsibilities

### Controllers (`app/controllers/`)
- Handle HTTP requests/responses
- Call service layer methods
- Return JSON or SSE streams
- **NO business logic**
- **NO direct API calls or filesystem access**

### Services (`app/services/`)
- Business logic and orchestration
- Validate data and business rules
- Coordinate between repositories
- **NO direct HTTP requests**
- **NO direct filesystem access**
- **NO import from `app.repositories`** (only from specific repo modules)

### Repositories (`app/repositories/`)
- Low-level technical operations
- HTTP API calls
- File read/write operations
- Data parsing and conversion
- **NO business logic**

### Models (`app/models/`)
- Pure dataclasses
- No business logic
- JSON serialization methods

---

## Common Issues & Solutions

### Circular Imports
- Services importing from `app.services` causes circular imports
- **Fix:** Import from specific module: `from app.services.releases_service import AppReleases`

### Type Checking in Models
- `isinstance(data, "ClassName")` with string fails - use class directly
- **Correct:** `isinstance(data, ManifestModel)`

---

## File Structure

```
server/
├── app/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py          # Path constants
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── app_controller.py  # HTTP endpoints (old)
│   │   └── fetch_controller.py # /api/fetch-data
│   ├── models/
│   │   ├── __init__.py
│   │   ├── app_model.py
│   │   ├── db_item.py
│   │   ├── manifest_model.py
│   │   └── release_model.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── apps_db_repo.py    # Remote DB fetching
│   │   ├── filesystem_repo.py # File operations
│   │   └── installed_apps_repo.py
│   └── services/
│       ├── __init__.py
│       ├── app_service.py     # Main business logic
│       ├── http_service.py    # HTTP requests
│       └── releases_service.py # Release handling
├── db/
│   └── apps.json              # Local DB cache
├── server.py                   # Flask app entry
├── requirements.txt
└── run.py
```

---

## Running the Server

```bash
cd server
python server.py
# Runs on http://0.0.0.0:5000
```

---

## Notes for Future Development

1. **Install/Uninstall** - Service methods exist as stubs, need full implementation
2. **SSE Streaming** - For progress updates during install/uninstall
3. **Config File** - Currently hardcoded; may add `config.json` later
4. **CORS** - Already configured for Angular client
5. **GitHub Rate Limits** - 60 req/hr unauthenticated; token support planned
