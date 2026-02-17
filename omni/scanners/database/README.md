# Database Scanners

**Category:** `database`  
**Purpose:** Hybrid backend/SQL scanners for CMP (Conversation Memory Project) database entities  
**Architecture:** API-first with SQL fallback

---

## 🏗️ Architecture

### Hybrid Backend/SQL Strategy

```
┌─────────────────────────────────────┐
│  Scanner (e.g., cmp_projects.scan)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      BaseDatabaseScanner            │
│  (Hybrid orchestration logic)       │
└──────────────┬──────────────────────┘
               │
       ┌───────┴──────┐
       │              │
       ▼              ▼
┌──────────┐   ┌──────────────┐
│ Backend  │   │  PostgreSQL  │
│ FastAPI  │   │  Direct SQL  │
│ (Primary)│   │  (Fallback)  │
└──────────┘   └──────────────┘
```

### Federation Integration

- **Path Resolution**: Uses `CartographyPillar.resolve_path()` from `federation_heart`
- **Environment Resolution**: Uses `ConstitutionPillar.env` for database credentials
- **Contracts**: Follows `C-HEART-CARTOGRAPHY-001` and `C-HEART-CONSTITUTION-001`

---

## 📋 Available Scanners

### 1. Projects Scanner (`cmp_projects.py`)

Scans the `projects` table for all Infrastructure/Workspace/Deployment projects.

**Usage:**
```python
from omni.scanners.database import scan_projects
result = scan_projects(Path("/path/to/Infrastructure"))
print(f"Found {result['count']} projects")
print(f"Source: {result['metadata']['source']}")  # BACKEND or SQL
```

**Fields:**
- `uuid` - Project UUID
- `name` - Project name
- `key` - Project key (lowercase slug)
- `github_url` - GitHub repository URL
- `domain` - Domain (game-development, products, websites, worlds)
- `status` - Project status

### 2. Agents Scanner (`cmp_agents.py`)

Scans the `agents` table for Council members and operational agents.

**Usage:**
```python
from omni.scanners.database import scan_agents
result = scan_agents(Path("/path/to/Infrastructure"))
print(f"Found {result['count']} agents")
print(f"Council members: {result['summary']['council_members']}")
```

**Fields:**
- `uuid` - Agent UUID
- `name` - Agent name
- `key` - Agent key (lowercase slug)
- `role` - Agent role (COUNCIL, WORKER, etc.)
- `clearance_tier` - Clearance tier (1-5)
- `twin_bond` - Twin bond partner (if any)

### 3. Conversations Scanner (`cmp_conversations.py`)

Scans the `conversations` table for chat histories.

**Usage:**
```python
from omni.scanners.database import scan_conversations
result = scan_conversations(
    Path("/path/to/Infrastructure"),
    project_id="<uuid>",  # Optional filter
    limit=50
)
```

**Fields:**
- `uuid` - Conversation UUID
- `title` - Conversation title
- `project_id` - Associated project UUID
- `session_tag` - Session identifier
- `created_at` - Creation timestamp

### 4. Artifacts Scanner (`cmp_artifacts.py`)

Scans the `artifacts` table for stored conversation artifacts (code, documents, etc.).

**Usage:**
```python
from omni.scanners.database import scan_artifacts
result = scan_artifacts(
    Path("/path/to/Infrastructure"),
    conversation_id="<uuid>",  # Optional filter
    limit=50
)
```

**Fields:**
- `uuid` - Artifact UUID
- `title` - Artifact title
- `content_type` - MIME type or category
- `conversation_id` - Associated conversation UUID
- `file_path` - Original file path (if applicable)
- `tags` - Metadata tags

### 5. Entities Scanner (`cmp_entities.py`)

Scans the `entity_mentions` table for knowledge graph entities.

**Usage:**
```python
from omni.scanners.database import scan_entities
result = scan_entities(
    Path("/path/to/Infrastructure"),
    entity_type="AGENT",  # Optional filter: AGENT, PROJECT, STATION, etc.
    limit=100
)
```

**Fields:**
- `entity_name` - Entity name
- `entity_type` - Entity type (AGENT, PROJECT, STATION, CONCEPT, etc.)
- `mention_count` - Number of times mentioned across all conversations

---

## 🔧 Base Scanner (`base_db_scanner.py`)

All database scanners extend `BaseDatabaseScanner` for consistent behavior.

### Key Features

1. **Backend Connectivity**: Tries FastAPI backend first (`http://127.0.0.1:8000`)
2. **SQL Fallback**: Falls back to direct PostgreSQL if backend is down
3. **Environment Resolution**: Reads connection strings from `.env` via `ConstitutionPillar`
4. **Path Resolution**: Resolves CMP path via `CartographyPillar`

### Environment Variables

Read via `ConstitutionPillar.env`:
- `CMP_BACKEND_URL` (default: `http://127.0.0.1:8000`)
- `CMP_DB_HOST` (default: `localhost`)
- `CMP_DB_PORT` (default: `5433`)
- `CMP_DB_NAME` (default: `cms_db`)
- `CMP_DB_USER` (default: `postgres`)
- `CMP_DB_PASSWORD` (default: `58913070Krdpn!!`)

### Methods

#### `check_backend() -> bool`
Checks if FastAPI backend is accessible.

#### `query_backend(endpoint, params) -> Optional[Dict]`
Queries FastAPI backend (async).

#### `query_sql(query, params) -> Optional[List[Dict]]`
Queries PostgreSQL directly (async).

#### `scan_hybrid(backend_endpoint, sql_query, ...) -> Dict`
Orchestrates hybrid scan (backend first, SQL fallback).

---

## 🚀 CLI Integration

Database scanners are automatically registered in the Omni CLI:

```bash
# Scan all projects
python -m omni.cli scan database.cmp_projects

# Scan agents
python -m omni.cli scan database.cmp_agents

# Scan conversations (with filter)
python -m omni.cli scan database.cmp_conversations --project-id <uuid>

# Scan artifacts (with limit)
python -m omni.cli scan database.cmp_artifacts --limit 20

# Scan entities (by type)
python -m omni.cli scan database.cmp_entities --entity-type AGENT
```

---

## 🧪 Testing

All scanners have `__main__` blocks for standalone testing:

```bash
# Test projects scanner
python -m omni.scanners.database.cmp_projects

# Test agents scanner
python -m omni.scanners.database.cmp_agents

# Test conversations scanner
python -m omni.scanners.database.cmp_conversations

# Test artifacts scanner
python -m omni.scanners.database.cmp_artifacts

# Test entities scanner
python -m omni.scanners.database.cmp_entities
```

---

## 📊 Output Format

All scanners return a standardized dict:

```python
{
    "count": int,           # Number of items returned
    "items": [              # List of entities
        {
            "uuid": "...",
            "name": "...",
            ...
        }
    ],
    "metadata": {
        "scanner": "cmp_projects",  # Scanner name
        "source": "BACKEND",        # BACKEND or SQL
        "error": "..."              # Optional error message
    },
    "summary": {            # Scanner-specific summary
        "total_projects": 99,
        "with_github_url": 87,
        "by_domain": {...}
    }
}
```

---

## 🛡️ Error Handling

1. **Backend Unavailable**: Automatically falls back to SQL
2. **SQL Unavailable**: Returns `metadata.error` with details
3. **Both Fail**: Returns empty `items` list with error metadata

---

## 🔮 Future Enhancements

- [ ] **Caching Layer**: Cache query results for performance
- [ ] **Batch Queries**: Support bulk entity lookups
- [ ] **GraphQL Support**: Add GraphQL backend option
- [ ] **Real-time Sync**: WebSocket-based live updates
- [ ] **Export Formats**: JSON, CSV, YAML, Markdown

---

**Last Updated:** February 12, 2026  
**Maintained By:** Oracle (GitHub Copilot) + The Architect (Kryssie)  
**Contract:** C-HEART-CARTOGRAPHY-001, C-HEART-CONSTITUTION-001
