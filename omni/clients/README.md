# Omni Clients

**Client interfaces for external services to interact with Omni registry orchestration.**

## Architecture

Omni provides high-level client wrappers that orchestrate Omni scanners for specific workflows:

```
External Service (Genesis, etc.)
        ↓
   Client Layer (GenesisClient, etc.)
        ↓
   Omni Scanner Orchestrator
        ↓
   Individual Scanners (cmp_projects, project, git, etc.)
        ↓
   Registry Files (canonical_projects_uuids.json, PROJECT_REGISTRY_V1.yaml, etc.)
```

## GenesisClient

**Purpose**: Provides Genesis-specific registry propagation workflows.

### Key Methods

#### `propagate_project(project_name, dry_run=False)`
Propagate a single project from CMP to all registries.

**Workflow:**
1. Scan CMP for project
2. Update `canonical_projects_uuids.json`
3. Update `PROJECT_REGISTRY_V1.yaml`
4. Update `repo_inventory.json` (if has GitHub)

**Use when:** Genesis canonizes a single project

```python
from omni.clients import GenesisClient

client = GenesisClient()
result = client.propagate_project("genesis")
print(result['registries_updated'])  # ['canonical_projects_uuids.json', ...]
```

#### `propagate_batch(project_names, dry_run=False)`
Propagate multiple projects (single rebuild - more efficient).

**Use when:** Genesis batch-canonizes multiple projects

```python
client = GenesisClient()
result = client.propagate_batch(["project1", "project2", "project3"])
```

#### `rebuild_all_registries(dry_run=False)`
Full registry rebuild from CMP (expensive - use sparingly).

**Use when:** Major registry corruption or migration

#### `verify_propagation(project_uuid)`
Verify project UUID appears in all expected registries.

**Returns:**
```python
{
    "verified": True/False,
    "uuid": "7c1c44ca-b22c-4169-bdde-1793ccfbbb09",
    "checks": {
        "in_canonical_uuids": True,
        "in_project_registry": True,
        "in_repo_inventory": True,
    },
    "missing_from": []  # Empty if all verified
}
```

## Integration Pattern

**Genesis side (`tools/genesis/genesis/integrations/omni_client.py`):**
```python
from omni.clients import GenesisClient

# Genesis never calls Omni scanners directly
# Genesis calls OmniClient → OmniClient wraps GenesisClient → GenesisClient orchestrates scanners

class OmniClient:
    def __init__(self):
        self.genesis_client = GenesisClient()
    
    def rebuild_registries(self, project_name=None):
        return self.genesis_client.propagate_project(project_name)
```

## Design Principles

1. **Separation of Concerns**
   - Omni owns HOW to rebuild registries
   - Genesis knows WHEN to rebuild registries
   - GenesisClient bridges the two

2. **Never Direct Registry Manipulation**
   - Genesis NEVER writes to registry files directly
   - Genesis calls GenesisClient
   - GenesisClient orchestrates Omni scanners
   - Scanners write registry files

3. **CMP is Source of Truth**
   - All registry builds read from CMP database
   - Registries are outputs, not sources
   - Genesis → CMP (UPSERT) → Omni scanners → Registries

4. **Efficient Operations**
   - Single project: `propagate_project()` (targeted)
   - Multiple projects: `propagate_batch()` (single rebuild)
   - Full rebuild: `rebuild_all_registries()` (rare - expensive)

## Future Clients

Other services that need registry coordination can follow this pattern:

- **MigrationClient**: Bulk project migrations
- **ArchiveClient**: Project retirement workflows
- **ValidationClient**: Registry integrity checks

Each client encapsulates service-specific registry workflows while using common Omni scanners underneath.
