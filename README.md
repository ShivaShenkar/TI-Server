# TI Connectivity Toolbox Backend

This project is the local backend service that powers the TI Connectivity Toolbox experience end-to-end.
It exposes REST APIs for the frontend to browse available apps, fetch app details by id, install and uninstall specific versions, launch installed apps, check run status, and stop the backend process when needed.

The backend is responsible for coordinating multiple data sources and states:

- Remote registry data (`apps.json`) from GitHub raw content
- Release/version metadata from GitHub Releases API
- Per-version app manifests from each app repository
- Local installation state under the Connectivity-Toolbox directory on disk
- In-memory caches for fetched app/release state and running processes

Architecturally, the codebase is organized into controllers, services, repositories, and models so HTTP concerns, business orchestration, and low-level filesystem/network operations stay separated.
In normal operation, the service refreshes remote data, resolves the latest or requested release, validates manifests and OS compatibility, updates local cache/files when installs happen, and returns frontend-ready payloads (`AppModel`) with status information such as installed version and update availability.

The backend also includes operational behavior needed for desktop integration, including CORS support for the local UI, explicit HTTP status code mapping for action results, local app process execution via `subprocess`, and a shutdown endpoint designed to terminate only the backend server process.

## Architecture

Three-layer structure:

| Layer | Directory | Responsibility |
|---|---|---|
| Presentation | `app/controllers/` | HTTP endpoints and response mapping |
| Service | `app/services/` | Business flow orchestration |
| Data | `app/repositories/` | Filesystem + GitHub API access |

Shared data contracts are in `app/models/`.

## Runtime and Stack

- Python + Flask + Flask-RESTful
- CORS enabled (`flask-cors`)
- GitHub raw content + GitHub releases API as upstream data sources
- Local filesystem used for downloaded apps and cached db

## Current Endpoints

Configured in `server.py`.

| Method | Endpoint | Controller | Purpose |
|---|---|---|---|
| GET | `/` | Flask route | Health hello response |
| GET | `/api/fetch-data` | `FetchController` | Fetch all apps for landing page |
| GET | `/api/fetch-data/<app_id>` | `FetchByIdController` | Fetch one app with versions |
| GET | `/api/install-app/<app_id>/<version>` | `InstallController` | Install specific version |
| GET | `/api/update-app/<app_id>/<version>` | `UpdateController` | Update/install specific version |
| GET | `/api/uninstall-app/<app_id>` | `UninstallController` | Uninstall app |
| DELETE | `/api/uninstall-app/<app_id>` | `UninstallController` | Uninstall app |
| GET | `/api/run-app/<app_id>` | `RunController` | Launch installed app |
| GET | `/api/run-status/<app_id>` | `RunStatusController` | Check running status |
| GET | `/api/shutdown` | `ShutdownController` | Shut down backend process |
| POST | `/api/shutdown` | `ShutdownController` | Shut down backend process |

## Response and Status Code Behavior

Most action endpoints return tuple-style `(json_body, http_code)` and include a `success` flag.

Typical codes used today:

- `200` successful action
- `400` invalid request/business precondition (for example app not found in expected cache path)
- `404` not found (missing app/version/release details)
- `409` conflict (already running)
- `500` internal execution error (for example process launch failure or filesystem failure)

`fetch` endpoints currently return data objects directly and `code` based on service result.

## Data Flow

1. Read remote app registry (`REMOTE_DB_URL`) into in-memory `AppDb`.
2. Save registry snapshot locally to `db/apps.json`.
3. For each app id, query GitHub releases and manifests.
4. Merge with local installed metadata from `<drive>/Connectivity-Toolbox/apps`.
5. Return normalized `AppModel` objects to frontend.

## Models

### `AppModel`

Returned to client by fetch endpoints.

```python
@dataclass
class AppModel:
    id: str
    name: str
    description: str
    versions: List[str] | None
    status: Literal["not installed", "update available", "up to date"]
    installedVersion: Optional[str] = None
    iconPath: Optional[str] = None
```

Notes:
- `fetch-data/<app_id>` now fills `versions` with all release tags from GitHub.
- `fetch-data` (landing page) still sets `versions=None` intentionally for lighter payload.

### `ManifestModel`

Parsed from each release `manifest.json`.

- Required: `name`, `description`, `version`, `supportedOS`
- Optional: `iconPath`
- `supportedOS` keys are filtered to supported values: `windows`, `linux`, `macos`

### `ReleaseURLs`

Stores release download URLs:
- `zipball_url`
- `tarball_url`

### `DbItem`

Registry item from remote `apps.json`:
- `owner`
- `repo`

## Important Service Behavior

### `Apps.fetch_landing_page()`
- Refreshes db from remote.
- Loads latest release per app.
- Loads latest manifest.
- Builds app list with status + installedVersion.

### `Apps.fetch_app_details(app_id)`
- Refreshes db.
- Loads all releases for the specific app.
- Loads latest manifest.
- Builds app payload including `versions` list.

### `Apps.install_app_version(app_id, version)`
- Ensures app/release exists.
- Downloads and extracts archive:
  - Windows: zip
  - Other OS: tar
- Updates installed version cache.

### `Apps.uninstall_app(app_id)`
- Removes local app directory.
- Removes installed version from cache.

### `Apps.run_app(app_id)`
- Validates installed manifest/executable path.
- Prevents duplicate run when already active.
- Starts process with `subprocess.Popen`.

### `Apps.is_app_running(app_id)`
- Checks tracked process state and cleans up closed processes.

## Repository Responsibilities

### `apps_db_repo.py`
- Fetches remote db from GitHub.
- Converts raw dict to typed `DbItem`s.
- Writes updated snapshot locally through filesystem repo.

### `releases_service.py`
- Fetches latest release and full releases list from GitHub API.
- Converts API payload to `ReleaseURLs` mapping.

### `filesystem_repo.py`
- Creates toolbox folders under system drive.
- Reads/writes local db and manifests.
- Installs zip/tar archives.
- Removes installed app directories.
- Includes path traversal checks during extraction.
- Uses `data_lock` for db file override write section.

### `installed_apps_repo.py`
- Tracks installed app versions (`app_id -> version`).
- Loads installed metadata from local manifests at startup.

## Configuration

In `app/config/config.py`:

- `DB_PATH` local db cache path
- `APPS_PATH` resolved via `get_ct_apps_folder()`
- `REMOTE_DB_URL` remote registry URL:
  - `https://raw.githubusercontent.com/ShivaShenkar/TI-Server/refs/heads/main/db/apps.json`

## Shutdown Behavior

`/api/shutdown` calls a delayed `os._exit(0)` via `threading.Timer`.

- Stops only Flask backend process.
- Does not automatically stop external apps launched by `/api/run-app`.
- `use_reloader=False` is required (already set) so shutdown is effective.

## Current Project Structure

```text
backend/
├── app/
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── fetch_controller.py
│   │   ├── fetch_by_id_controller.py
│   │   ├── install_controller.py
│   │   ├── run_controller.py
│   │   ├── shutdown_controller.py
│   │   ├── uninstall_controller.py
│   │   └── update_controller.py
│   ├── models/
│   │   ├── app_model.py
│   │   ├── db_item.py
│   │   ├── manifest_model.py
│   │   └── release_model.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── apps_db_repo.py
│   │   ├── filesystem_repo.py
│   │   └── installed_apps_repo.py
│   └── services/
│       ├── app_service.py
│       ├── http_service.py
│       └── releases_service.py
├── db/
│   └── apps.json
├── server.py
├── requirements.txt
└── README.md
```

## Running the Server

From backend root:

```bash
py server.py
```

Server runs on:
- `http://127.0.0.1:5000`
- `http://0.0.0.0:5000`

## Known Limitations / Next Improvements

- `fetch-data` (all apps) intentionally keeps `versions=None`; can be expanded if frontend needs full list there too.
- Error responses are controller-driven; adding centralized Flask error handlers would make failure JSON format more uniform.
- Concurrency around install/uninstall/run can be further hardened with broader locking if parallel requests are expected.
