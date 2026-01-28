# 🔍 Omni Scanner Registry

**Location:** `omni/core/scanners/`  
**Purpose:** Modular scanner plugins for static and runtime analysis  
**Version:** 0.5.0  
**Status:** Living Plugin System

---

## 🎯 Scanner Architecture

Each scanner is a self-contained module that implements the standard interface:

```python
from pathlib import Path

def scan(target: Path) -> dict:
    """
    Scanner implementation.
    
    Args:
        target: Path to scan (file or directory)
        
    Returns:
        dict with standard keys:
        - count: int - Number of findings
        - items: list - Found items
        - metadata: dict - Scanner-specific metadata
    """
    return {
        "count": 0,
        "items": [],
        "metadata": {}
    }
```

---

## 📋 Static Scanners (Filesystem)

### `surfaces.py` 🌐
- **Category:** Interface Detection
- **Purpose:** Discovers API surfaces, routes, and integration points
- **Detects:**
  - HTTP endpoints (`@app.get`, `@app.post`, router patterns)
  - MCP tools (`@mcp.tool`, `ListToolsRequest`)
  - CLI entry points (`if __name__ == "__main__"`, Click, Typer, argparse)
  - Crown Bus topics (`publish()`, `subscribe()`, `crown://`)
  - Database models (`class Model`, `CREATE TABLE`)
  - UI integrations (`fetch()`, `axios.`)
- **Contract Families:**
  - `mcp` → C-MCP-BASE-001.md
  - `http` → C-HTTP-BASE-001.md
  - `cli` → C-CLI-BASE-001.md
  - `bus_topic` → C-SYS-BUS-001.md
  - `db` → C-DB-BASE-001.md
  - `ui_integration` → C-UI-BASE-001.md
- **Output:** Surface inventory with contract compliance mapping
- **Use Case:** API documentation, contract verification

---

### `contracts.py` 📜
- **Category:** Contract Discovery
- **Purpose:** Finds explicit contract definitions
- **Detects:**
  - `CONTRACT.md` files
  - `openapi.json` / `openapi.yaml` specs
- **Output:** List of contract files found
- **Use Case:** Contract enforcement, API spec validation

---

### `docs.py` 📚
- **Category:** Documentation Discovery
- **Purpose:** Finds documentation files
- **Detects:**
  - README files (`.md`, `.txt`, `.rst`)
  - Documentation directories
  - Markdown files
- **Output:** Documentation inventory
- **Use Case:** Documentation completeness audits

---

### `deps.py` 📦
- **Category:** Dependency Discovery
- **Purpose:** Finds dependency declaration files
- **Detects:**
  - `package.json` (Node.js)
  - `requirements.txt` (Python)
  - `pyproject.toml` (Python)
  - `Gemfile` (Ruby)
  - `go.mod` (Go)
  - `Cargo.toml` (Rust)
- **Output:** List of dependency files
- **Use Case:** Dependency auditing, polyglot analysis
- **Note:** Detection only - use `requirements.py` core module for deep Python analysis

---

### `tools.py` 🛠️
- **Category:** CLI Tool Discovery
- **Purpose:** Finds installable command-line tools
- **Detects:**
  - `pyproject.toml` `[project.scripts]` (Python)
  - `pyproject.toml` `[tool.poetry.scripts]` (Poetry)
  - `package.json` `"bin"` (Node.js)
  - `setup.py` `entry_points` (Legacy Python)
- **Output:** List of installable tools with language
- **Use Case:** Tool inventory, CLI documentation

---

### `uuids.py` 🔑
- **Category:** Identity Tracking
- **Purpose:** Finds UUID usage in codebase
- **Detects:**
  - UUID declarations
  - UUID references
  - UUID patterns in code/config
- **Output:** UUID usage inventory
- **Use Case:** UUID provenance, identity auditing
- **Integration:** Works with `provenance.py` core module

---

### `events.py` 📡
- **Category:** Event Emission Detection
- **Purpose:** Maps event publishers and subscribers
- **Detects:**
  - `.publish()` calls
  - `.emit()` calls
  - `crown://` URIs
  - Event topic declarations
- **Patterns:** Configurable via `omni.yml`
  ```yaml
  scan:
    patterns:
      generic_events:
        - "\\.publish\\("
        - "crown://"
  ```
- **Output:** Event emission inventory with topics
- **Use Case:** Event bus mapping, Crown Bus documentation
- **Integration:** Generates `EVENT_REGISTRY.yaml` via `registry_events.py`

---

### `hooks.py` 🪝
- **Category:** Hook Detection
- **Purpose:** Finds lifecycle hooks and callbacks
- **Detects:**
  - Git hooks (`.git/hooks/`)
  - Pre-commit hooks
  - Post-deploy hooks
  - Lifecycle callbacks in code
- **Output:** Hook inventory
- **Use Case:** Automation auditing, lifecycle documentation

---

### `git.py` 🔀 *(New in v0.6.1)*
- **Category:** Repository Health
- **Purpose:** Scans git repositories for status and health
- **Detects:**
  - Dirty/clean status
  - Uncommitted changes count
  - Ahead/behind remote counts
  - Current branch
  - Repository health classification (clean, dirty, unpushed, etc.)
- **Output:** Git status inventory with health grades
- **Use Case:** Repository hygiene, fleet-wide git status, **GitHub Guild integration**

---

### `fleet.py` 🛰️ *(New in v0.6.1)*
- **Category:** Station Fleet Analysis
- **Purpose:** Scans station fleet configurations and health
- **Detects:**
  - Registered stations
  - Fleet configuration files
  - Station health status
- **Integration:** Uses `fleet_configs/` configuration modules
- **Output:** Fleet status inventory
- **Use Case:** Station fleet monitoring, satellite discovery

---

### `cli.py` + `cli_edge_scanner.py` ⌨️ *(New in v0.6.1)*
- **Category:** CLI Edge Detection
- **Purpose:** Discovers CLI entry points and command structures
- **Detects:**
  - Typer/Click commands
  - argparse patterns
  - Entry point scripts
- **Output:** CLI command inventory
- **Use Case:** CLI documentation, command discovery

---

### `cores.py` 🧠 *(New in v0.6.1)*
- **Category:** Core Analysis
- **Purpose:** Analyzes core module structure
- **Detects:**
  - Core module patterns
  - Architecture analysis
- **Output:** Core module inventory
- **Use Case:** Architecture documentation

---

### `library.py` 📚 *(New in v0.6.1)*
- **Category:** Library Analysis
- **Purpose:** Discovers and analyzes project libraries
- **Detects:**
  - Library definitions
  - Shared modules
- **Output:** Library inventory
- **Use Case:** Dependency mapping, shared code discovery

---

### `canon.py` 📜 *(New in v0.6.1)*
- **Category:** Constitutional Compliance
- **Purpose:** Scans CodeCraft canon lock files and validates compliance
- **Detects:**
  - canon.lock.yaml files
  - Canon partition compliance
  - Executor registration
- **Output:** Canon compliance report
- **Use Case:** Constitutional verification, canon auditing

---

## 🎮 Scanner Plugin System

### Registry (`__init__.py`)

All scanners are registered in the `SCANNERS` dict:

```python
from . import surfaces, docs, deps, contracts, tools, uuids, events, hooks

SCANNERS = {
    "surfaces": surfaces.scan,
    "events": events.scan,
    "docs": docs.scan,
    "deps": deps.scan,
    "contracts": contracts.scan,
    "tools": tools.scan,
    "uuids": uuids.scan,
    "hooks": hooks.scan,
}
```

### Adding New Scanners

1. Create scanner module: `scanners/new_scanner.py`
2. Implement `scan(target: Path) -> dict` function
3. Register in `scanners/__init__.py`:
   ```python
   from . import new_scanner
   SCANNERS["new_scanner"] = new_scanner.scan
   ```
4. Update this README with scanner documentation

---

## 🚀 Usage

### From CLI
```bash
# Run single scanner
omni scan --scanners=surfaces .

# Run multiple scanners
omni scan --scanners=surfaces,events,contracts .

# Run all scanners on target
omni scan /path/to/project

# Global scan (all projects in registry)
omni scan --all
```

### From Code
```python
from pathlib import Path
from omni.core.scanners import SCANNERS

# Run specific scanner
target = Path("/path/to/project")
results = SCANNERS["surfaces"](target)

# Run all scanners
all_results = {
    name: scanner(target)
    for name, scanner in SCANNERS.items()
}
```

---

## 📊 Output Format

All scanners return a dict with these standard keys:

```python
{
    "count": 5,           # Number of findings
    "items": [...],       # List of found items
    "metadata": {         # Scanner-specific metadata
        "scanner": "surfaces",
        "version": "0.5.0"
    }
}
```

### Optional Keys
- `found`: list - Alternative to `items` (backward compat)
- `summary`: dict - Summary statistics
- `errors`: list - Errors encountered during scan

---

## 🔄 Integration with Core

Scanners integrate with core modules:

- **`surfaces.py`** → Referenced by `registry_events.py` for event mapping
- **`uuids.py`** → Used by `provenance.py` for UUID auditing
- **`deps.py`** → Referenced by `requirements.py` for dependency analysis
- **`events.py`** → Feeds `registry_events.py` for event registry generation

---

## 🎯 Roadmap: Planned Scanners

### Phase 2: Constitutional Intelligence ✅ COMPLETE
- ✅ Runtime health scanners (federation_health, station_health, cmp_health, pillar_health, tunnel_status)

### Phase 3: Gamified Backend (PENDING)
- `quest_tracker.py` - Parses "Quest" markers in markdown
- `achievement_calculator.py` - Metrics for visual badges

### Phase 4: Polyglot Expansion ✅ COMPLETE
- ✅ `node_scanner.py` - Deep package.json analysis for Federation JS deps
- ✅ `rust_scanner.py` - Deep Cargo.toml analysis for crate usage

### Future Enhancements
- `python_scanner.py` - Deep requirements.txt/pyproject.toml analysis (beyond basic deps)
- `docker_scanner.py` - Dockerfile and docker-compose.yml analysis
- `kubernetes_scanner.py` - K8s manifest analysis

---

## 📊 Runtime Health Scanners (New in v0.6.0)

### `federation_health.py` 🧠
- **Category:** Runtime Health
- **Purpose:** Queries FederationCore for system health
- **Detects:**
  - FederationCore status (ACTIVE/SECURE/ERROR)
  - Individual pillar health (5 pillars)
  - Component availability
- **Integration:** Uses `federation_heart.core.federation_core.FederationCore`
- **Output:** Core status + pillar breakdown
- **Use Case:** System-wide health check

---

### `station_health.py` 🛰️
- **Category:** Runtime Health
- **Purpose:** Queries Station Nexus for pipeline health
- **Detects:**
  - Nexus connectivity (ONLINE/OFFLINE)
  - Registered stations
  - Pipeline status (SENSE→DECIDE→ACT)
  - Nonary Station (SENSE)
  - Living State Station (DECIDE)
  - CodeCraft Station (ACT)
- **Integration:** Uses `federation_heart.clients.connectivity.StationClient`
- **Output:** Nexus status + pipeline metrics
- **Use Case:** Pipeline health monitoring, station diagnostics

---

### `cmp_health.py` 💾
- **Category:** Runtime Health
- **Purpose:** Queries Conversation Memory Project health
- **Detects:**
  - PostgreSQL database connectivity
  - Schema version (37 tables, 277 columns)
  - MCP server availability (cmp-memory, cmp-knowledge-graph)
  - Memory lane status (9 lanes: episodic, semantic, procedural, etc.)
  - Total conversation count
- **Integration:** Uses `conversation-memory-project/mcp_servers/cmp_config.py`
- **Output:** Database health + memory lane status
- **Use Case:** Memory substrate monitoring, CMP diagnostics

---

### `pillar_health.py` 🏛️
- **Category:** Runtime Health
- **Purpose:** Queries all Federation Heart pillars
- **Detects:**
  - Cartography Pillar (WHERE)
  - Connectivity Pillar (HOW to connect)
  - Constitution Pillar (WHAT rules)
  - Foundry Pillar (HOW to make)
  - Consciousness Pillar (WHO - if available)
- **Health Grades:**
  - EXCELLENT: All pillars active
  - GOOD: All but one active
  - DEGRADED: Half or more active
  - CRITICAL: At least one active
  - OFFLINE: None active
- **Integration:** Uses all pillar classes from `federation_heart.pillars`
- **Output:** Per-pillar detailed status + overall health grade
- **Use Case:** Federation Heart diagnostics, component health matrix

---

### `tunnel_status.py` 🌐
- **Category:** Runtime Health
- **Purpose:** Queries active network tunnels
- **Detects:**
  - Cloudflare tunnels (`cloudflared tunnel list`)
  - ngrok tunnels (via localhost:4040 API)
  - Federation-managed tunnels (TunnelManager)
  - Active endpoints and URLs
- **Integration:** Uses `federation_heart.clients.connectivity.TunnelManager`
- **Output:** Tunnel inventory with endpoints
- **Use Case:** Network connectivity monitoring, tunnel debugging

---

## 🌐 Polyglot Scanners (New in v0.6.0)

### `node_scanner.py` 📦
- **Category:** Polyglot Analysis
- **Purpose:** Deep Node.js/JavaScript/TypeScript project analysis
- **Detects:**
  - Package name, version, description
  - Production dependencies
  - Development dependencies
  - Peer dependencies
  - Scripts (build, dev, test, etc.)
  - Entry points (main, module, types, bin)
  - Federation markers:
    - `federation_keywords` - SERAPHINA/Federation in keywords
    - `mcp_dependency` - MCP packages
    - `nextjs_project` - Next.js detected
    - `react_project` - React detected
    - `typescript_enabled` - TypeScript enabled
- **Output:** Comprehensive package.json analysis
- **Use Case:** JavaScript ecosystem mapping, Federation UI project discovery

---

### `rust_scanner.py` 🦀
- **Category:** Polyglot Analysis
- **Purpose:** Deep Rust crate analysis
- **Detects:**
  - Crate name, version, edition, description
  - Production dependencies
  - Development dependencies
  - Build dependencies
  - Features
  - Workspace members
  - Federation markers:
    - `codecraft_vm` - CodeCraft native VM
    - `quantum_enabled` - Q# quantum interop
    - `mcp_integration` - MCP integration
    - `async_runtime` - Tokio/async-std
    - `wasm_target` - WebAssembly target
- **Output:** Comprehensive Cargo.toml analysis
- **Use Case:** Rust ecosystem mapping, CodeCraft VM monitoring

---

## 🎯 Roadmap: Completed Scanners

### Phase 4: Runtime Health (COMPLETE) ✅
- ✅ `federation_health.py` - Queries FederationCore.status()
- ✅ `station_health.py` - Queries station nexus pipeline status
- ✅ `cmp_health.py` - Queries memory substrate health
- ✅ `pillar_health.py` - Queries all 5 pillars for status
- ✅ `tunnel_status.py` - Queries active Cloudflare/ngrok tunnels

### Phase 4: Polyglot Expansion (COMPLETE) ✅
- ✅ `node_scanner.py` - Deep package.json analysis for Federation JS deps
- ✅ `rust_scanner.py` - Deep Cargo.toml analysis for crate usage

---

## 🛡️ Safety & Performance

### Safety Defaults
- **Read-only:** Scanners never modify source files
- **Non-destructive:** Results written to `artifacts/omni/`
- **Sensitive paths:** Auto-exclude `.env`, `.git`, credentials

### Performance Optimization
- **Configurable excludes:** `omni.yml` exclusion patterns
- **Depth limits:** Prevent excessive traversal
- **Lazy evaluation:** Only scan when needed
- **Parallel scanning:** Future enhancement

---

## 📚 Dependencies

**Required:**
- Python 3.8+
- pathlib (stdlib)

**Optional:**
- None (scanners use stdlib only for maximum portability)

---

## 🎓 Best Practices

### Scanner Design
1. **Single Responsibility:** Each scanner does ONE thing well
2. **Consistent Interface:** Always return `{count, items, metadata}`
3. **Error Handling:** Catch exceptions, never crash the scan
4. **Performance:** Skip deep node_modules, build dirs
5. **Documentation:** Update this README when adding scanners

### Pattern Matching
- Use regex for code patterns
- Make patterns configurable via `omni.yml`
- Provide sensible defaults

### Output Quality
- Include metadata for traceability
- Provide counts for quick summaries
- Structure items for easy parsing

---

*Last Updated: January 28, 2026 (v0.6.1 + git/fleet/cli/canon scanners)*  
*Maintained by: The Federation*  
*Constitutional Authority: Charter V1.2*
