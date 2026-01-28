# 🧠 Omni Core Modules

**Location:** `omni/core/`  
**Purpose:** Core intelligence and orchestration layer for the Federation Tricorder  
**Version:** 0.6.1  
**Status:** Living Architecture

---

## 📋 Module Registry

### 🗺️ Cartography & Mapping

#### `cartographer.py`
- **Type:** Ecosystem Intelligence Agent
- **Purpose:** Analyzes complex project ecosystems and generates comprehensive maps, guides, and visualizations
- **Key Classes:** `EcosystemCartographer`, `ProjectNode`, `EcosystemMap`
- **Capabilities:**
  - Project discovery and relationship analysis
  - Architectural pattern recognition
  - Technology stack analysis
  - Health metrics calculation
  - Comprehensive guide generation
  - Network visualization (requires matplotlib, networkx)
- **Dependencies:** networkx, matplotlib, seaborn (optional)
- **Output:** Ecosystem guides, relationship graphs, health reports

#### `tree.py`
- **Type:** Directory Visualization
- **Purpose:** Generates clean directory trees for documentation
- **Capabilities:**
  - Smart filtering (ignores node_modules, __pycache__, etc.)
  - Configurable depth limits
  - Documentation-ready output
- **Output:** Formatted directory tree strings

---

### 📜 Registry & Identity Management

#### `registry.py`
- **Type:** Registry Parser (Legacy V1)
- **Purpose:** Parses project registry files
- **Status:** Maintained for backward compatibility
- **Migration Path:** Use `registry_v2.py` for new implementations

#### `registry_v2.py`
- **Type:** Registry Parser V2
- **Purpose:** Parses Registry V2 format with Identity+Facets frontmatter schema
- **Key Features:**
  - Frontmatter YAML parsing
  - Identity extraction (UUIDs, names, roles)
  - Facet parsing (domains, specializations, twin bonds)
  - Full metadata support
- **Schema:** SERAPHINA Registry V2 (Identity+Facets)

#### `registry_events.py`
- **Type:** Event Registry Generator
- **Purpose:** Generates `EVENT_REGISTRY.yaml` from scan results
- **Capabilities:**
  - Aggregates event emissions from codebase
  - Validates Crown Bus event schemas
  - Generates canonical event documentation
- **Output:** `EVENT_REGISTRY.yaml`

#### `provenance.py`
- **Type:** UUID Provenance Index (UPI)
- **Purpose:** Tracks UUID usage across filesystem vs Registry truth
- **Key Features:**
  - Canonical UUID verification
  - Orphan detection (UUIDs not in registry)
  - Ghost detection (Registry UUIDs not in filesystem)
  - Test junk filtering
- **Output:** UUID provenance reports

#### `fetcher.py`
- **Type:** Database Synchronization
- **Purpose:** Fetches canonical UUIDs from CMP/CMS PostgreSQL database
- **Capabilities:**
  - Database connection management
  - UUID extraction from agents/projects tables
  - Registry synchronization
- **Dependencies:** Database connection configured

---

### 🔍 Analysis & Compliance

#### `gate.py`
- **Type:** Compliance Enforcement
- **Purpose:** CI/CD gate checks for Federation standards
- **Capabilities:**
  - Identity enforcement (no new orphan UUIDs)
  - Constitutional compliance verification
  - Build failure on violations
- **Use Case:** Pre-commit hooks, CI/CD pipelines

#### `requirements.py`
- **Type:** Dependency Management
- **Purpose:** Federation-wide Python dependency analysis
- **Capabilities:**
  - Recursive requirement scanning
  - Deduplication and merging
  - Version locking to current install
  - `requirements.federation.txt` generation
- **Commands:**
  - `omni audit deps` - Scan and generate
  - `omni audit lock` - Lock to current versions

---

### 📊 Reporting & Rendering

#### `renderer.py`
- **Type:** Registry Renderer
- **Purpose:** Regenerates human-readable Markdown tables in `PROJECT_REGISTRY_MASTER.md`
- **Capabilities:**
  - Parses canonical frontmatter
  - Generates formatted tables
  - Preserves registry integrity
- **Safety:** Read-only by default (requires explicit render command)

#### `reporting.py`
- **Type:** Report Generation
- **Purpose:** Generates structured reports from scan results
- **Capabilities:**
  - JSON report formatting
  - Summary statistics
  - Health metrics
  - Artifact persistence
- **Output:** `artifacts/omni/` directory

---

### 🛠️ Utilities & Infrastructure

#### `config.py`
- **Type:** Configuration Loader
- **Purpose:** Loads and parses `omni.yml` configuration
- **Schema:**
  ```yaml
  scan:
    exclude: [...]
    patterns:
      generic_events: [...]
  ```
- **Defaults:** Built-in fallbacks if no config exists

#### `io.py`
- **Type:** Input/Output Utilities
- **Purpose:** Common file operations, path handling, safe file writes
- **Capabilities:**
  - Safe file writes with backups
  - Path resolution
  - JSON/YAML parsing
  - Encoding handling

#### `model.py`
- **Type:** Data Models
- **Purpose:** Shared data structures for scan results
- **Key Classes:**
  - `ScanResult` - Standard scan result format
    - `target`: str - Scan target path
    - `version`: str - Scanner version
    - `timestamp`: str - ISO8601 timestamp
    - `findings`: dict - Scanner-specific findings
    - `summary`: dict - Summary statistics

#### `tap.py`
- **Type:** Crown Bus Tap Utility
- **Purpose:** Runtime event verification and debugging
- **Capabilities:**
  - Event emission monitoring
  - Crown Bus topic validation
  - Runtime telemetry capture
- **Use Case:** Development debugging, event auditing

#### `brain.py` *(New in v0.6.1)*
- **Type:** AI Integration Utilities
- **Purpose:** Brain/orchestration helpers for AI integration
- **Use Case:** Agent coordination, model management

#### `librarian.py` *(New in v0.6.1)*
- **Type:** Documentation Librarian
- **Purpose:** Library scanning and documentation management
- **Use Case:** Documentation discovery, README indexing

#### `paths.py` *(New in v0.6.1)*
- **Type:** Path Resolution
- **Purpose:** Federation-aware path resolution and discovery
- **Capabilities:**
  - Infrastructure root detection
  - Station path resolution
  - Registry path management
- **Use Case:** Cross-project path handling

---

### 📁 Scanners Subsystem

#### `scanners/`
- **Type:** Plugin Registry
- **Purpose:** Modular scanner implementations
- **See:** `scanners/README.md` for detailed scanner documentation
- **Registry:** `scanners/__init__.py` exposes `SCANNERS` dict

---

## 🏗️ Architecture Patterns

### Module Responsibilities

**Cartography** (`cartographer.py`, `tree.py`)
- **What:** Understanding WHERE things are and HOW they relate
- **Writes:** Ecosystem guides, visualizations
- **Reads:** Filesystem, project files

**Registry** (`registry*.py`, `provenance.py`, `fetcher.py`)
- **What:** Understanding WHO things are (identity management)
- **Writes:** Provenance reports, event registries
- **Reads:** Registry files, database, filesystem

**Compliance** (`gate.py`, `requirements.py`)
- **What:** Enforcing WHAT the rules are
- **Writes:** Compliance reports, requirement locks
- **Reads:** Registry, filesystem, Python environment

**Rendering** (`renderer.py`, `reporting.py`)
- **What:** Transforming data into readable formats
- **Writes:** Markdown tables, JSON reports
- **Reads:** Registry, scan results

**Infrastructure** (`config.py`, `io.py`, `model.py`, `tap.py`)
- **What:** Supporting HOW everything works
- **Provides:** Shared utilities, data models, configuration

---

## 🔄 Data Flow

```
Filesystem Reality
       ↓
   Scanners (scanners/)
       ↓
   Core Modules
       ↓
Registry Truth (governance/)
       ↓
   Reports (artifacts/omni/)
```

### Key Principle
> **The Registry is God.** Core modules reconcile filesystem reality with registry truth.

---

## 🚀 Integration Points

### Federation Heart Integration
Core modules should use `federation_heart.clients.cartography` for:
- `get_infrastructure_root()` - Canonical paths
- `RegistryClient` - Registry navigation

### Scanner Integration
All scanners return consistent format via `model.ScanResult`:
```python
from omni.core.model import ScanResult

def scan(target: Path) -> dict:
    return {
        "count": 0,
        "items": [],
        "metadata": {}
    }
```

---

## 📚 External Dependencies

**Required:**
- Python 3.8+
- pathlib (stdlib)
- json, yaml (stdlib)

**Optional:**
- networkx, matplotlib, seaborn (for cartographer visualization)
- psycopg2 (for database fetcher)

---

## 🎯 Usage Patterns

### From CLI
```bash
omni audit uuids    # Uses provenance.py
omni map ecosystem  # Uses cartographer.py
omni tree .         # Uses tree.py
omni gate           # Uses gate.py
```

### From Code
```python
from omni.core import registry_v2, provenance, cartographer

# Parse registry
projects = registry_v2.parse_registry_v2()

# Run provenance check
provenance.run_uuid_audit()

# Map ecosystem
carto = cartographer.EcosystemCartographer()
ecosystem_map = carto.analyze_ecosystem()
```

---

*Last Updated: January 28, 2026 (v0.6.1 + Package Refactor)*  
*Maintained by: The Federation*  
*Constitutional Authority: Charter V1.2*
