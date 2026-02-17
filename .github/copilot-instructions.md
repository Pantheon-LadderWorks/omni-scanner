# GitHub Copilot Instructions - Omni (Federation Governance Tricorder)

**Omni's Identity:** Federation sensor array and governance introspection tool  
**Role:** Unified scanning, registry auditing, ecosystem mapping, and health monitoring  
**Version:** 0.6.0+ (Living Plugin System)

---

## I. The Big Picture Architecture

### What Is Omni?

Omni is the **Federation's Tricorder** – a single CLI that bridges the gap between:
- **Registry Truth** (canonical sources like `PROJECT_REGISTRY_V1.yaml`)
- **Filesystem Reality** (actual codebase, deployments, configurations)
- **Runtime Health** (live station status, database connectivity, tunnels)

**Core Philosophy:** "We don't guess. We scan."

### Architecture Layers

```
CLI Entry (omni/cli.py)
    ↓
System Orchestrator (omni/core/system.py - OmniInstrument)
    ↓
┌─────────────────┬──────────────────┬─────────────────┐
│      CORE       │     PILLARS      │    SCANNERS     │
│  (Intelligence) │  (Capabilities)  │    (Plugins)    │
├─────────────────┼──────────────────┼─────────────────┤
│ identity_engine │   cartography    │   discovery/    │ ← Structures
│ registry_builder│   gatekeeper     │   health/       │ ← Runtime
│ registry.py     │   intel          │   static/       │ ← Code
│ config.py       │   registry       │   fleet/        │ ← Fleets
│ paths.py        │                  │   git/          │ ← Repos
│ model.py        │                  │   polyglot/     │ ← Languages
│ gate.py         │                  │                 │
└─────────────────┴──────────────────┴─────────────────┘
    ↓
Artifacts Output (artifacts/omni/*.json)
```

**Key Separations:**
- **Core:** Identity, orchestration, data models (the brain)
- **Pillars:** Large subsystems (cartography, registry parsing, compliance gates)
- **Scanners:** Modular plugins (surfaces, events, deps, health checks)
- **Lib:** Shared utilities (I/O, rendering, requirements parsing, TAP verification)

### Registry Architecture (The One Ring)

Omni enforces a **Single Source of Truth** model:

1. **`identity_engine.py`** - Computes deterministic UUIDv5s from `NAMESPACE_CMP` (The One Ring)
2. **`registry_builder.py`** - Constructs `PROJECT_REGISTRY_V1.yaml` from:
   - GitHub inventory (`repo_inventory.json`)
   - Local git scans
   - Governance overrides (`LOCAL_OVERRIDES_V1.yaml`)
   - Legacy Oracle data reconciliation
3. **`registry.py`** - Parses the canonical registry for operational use

**Policy:** If code disagrees with registry → code is wrong OR registry needs updating

---

## II. Critical Developer Workflows

### Running Scans

**Basic Pattern:**
```powershell
# Single target scan (all scanners)
omni scan path/to/target

# Specific scanner on target
omni scan --scanners=surfaces path/to/target

# Global scan (requires explicit scanner)
omni scan --all --scanners=surfaces

# Multiple scanners
omni scan --scanners=surfaces,events,deps .
```

**Output Location:** `artifacts/omni/scan.[scanner_names].json`

### Common Scan Commands

```powershell
# === Identity & Registry ===
omni scan --scanners=project .           # Build registry from local scan
omni audit uuids                         # UUID provenance check
omni audit fetch-db                      # Sync canonical UUIDs from CMP database

# === Health Monitoring ===
omni scan --scanners=federation_health   # Check FederationCore status
omni scan --scanners=pillar_health       # Check Federation Heart pillars
omni scan --scanners=station_health      # Query Station Nexus pipeline
omni scan --scanners=cmp_health          # Check memory substrate
omni scan --scanners=tunnel_status       # Check active cloudflared tunnels

# === Code Analysis ===
omni scan --scanners=surfaces .          # Find API surfaces (HTTP, MCP, CLI, DB, UI)
omni scan --scanners=events .            # Map event emissions (Crown Bus)
omni scan --scanners=canon .             # Verify CodeCraft canon compliance

# === Polyglot Support ===
omni scan --scanners=node path/to/npm    # Deep Node.js/TypeScript analysis
omni scan --scanners=rust path/to/cargo  # Deep Rust crate analysis

# === Git & Fleet ===
omni scan --scanners=git --all           # Global git health check
omni scan --scanners=fleet .             # Station fleet status
omni scan --scanners=velocity --all --since=7d  # Git velocity analysis
```

### Interpreting Results

All scan results follow the `ScanResult` model:
```python
{
  "target": "path/or/global",
  "findings": {
    "scanner_name": {
      "count": 42,
      "items": [...]
    }
  },
  "summary": {
    "risk": "low|medium|high",
    "surfaces": { "total": X, "missing": Y, "partial": Z, "exists": W }
  }
}
```

**Risk Levels (for surfaces):**
- `low`: All surfaces documented
- `medium`: >90% partial documentation
- `high`: Missing contracts detected

### Adding a New Scanner

1. **Create scanner module:**
   ```python
   # omni/scanners/[category]/my_scanner.py
   from pathlib import Path
   
   def scan(target: Path, **kwargs) -> dict:
       """Scanner implementation."""
       return {
           "count": 0,
           "items": [],
           "metadata": {}
       }
   ```

2. **Add to category's `__init__.py`:**
   ```python
   from . import my_scanner
   
   SCANNERS_[CATEGORY] = {
       # ...existing...
       "my_scanner": my_scanner.scan,
   }
   ```

3. **Update category manifest:**
   ```yaml
   # omni/scanners/[category]/SCANNER_MANIFEST.yaml
   scanners:
     - name: my_scanner
       file: my_scanner.py
       function: scan
       description: "What this scanner does"
   ```

4. **Test:**
   ```powershell
   omni scan --scanners=my_scanner .
   ```

---

## III. Project-Specific Conventions

### File Organization

```
omni/
├── cli.py                    # Main entry point (argparse commands)
├── core/                     # Intelligence layer
│   ├── identity_engine.py    # The One Ring (UUIDv5 computation)
│   ├── registry_builder.py   # Registry construction logic
│   ├── registry.py           # Registry parser (V1 + legacy)
│   ├── system.py             # OmniInstrument orchestrator
│   ├── config.py             # Federation Heart bridge
│   ├── paths.py              # Path resolution (Tier 1 anchor)
│   ├── model.py              # Data models (ScanResult, ScanFinding)
│   └── gate.py               # Policy enforcement (CI/CD)
├── pillars/                  # Capability modules
│   ├── cartography.py        # Ecosystem mapping
│   ├── gatekeeper.py         # Compliance validation
│   ├── intel.py              # Intelligence gathering
│   └── registry.py           # Registry operations
├── scanners/                 # Plugin system (categorized)
│   ├── discovery/            # Structure scanners (cores, cli, canon, library, project)
│   ├── health/               # Runtime health (federation, pillar, station, cmp, tunnel)
│   ├── static/               # Code analysis (surfaces, events, deps, contracts, docs, tools, uuids, hooks)
│   ├── fleet/                # Fleet management (station fleets)
│   ├── git/                  # Repository health (git status, velocity)
│   └── polyglot/             # Language-specific (node, rust, packages)
├── lib/                      # Shared utilities
│   ├── io.py                 # File I/O (emoji-safe UTF-8)
│   ├── renderer.py           # Output formatting
│   ├── reporting.py          # Report generation
│   ├── requirements.py       # Python dependency parsing
│   ├── tap.py                # TAP (Test Anything Protocol) verification
│   └── tree.py               # Directory tree generation
├── builders/                 # Code generation
│   ├── executors_builder.py  # CodeCraft executor scaffolding
│   ├── partitions_builder.py # Canon partition generation
│   └── rosetta_archaeologist.py  # Legacy translation
├── scaffold/                 # Templates
│   └── templates.py          # Scaffolding templates
├── scripts/                  # Maintenance scripts
└── templates/                # Document templates
    ├── CONTRACT_TEMPLATE.md  # Contract specification template
    └── library_taxonomy.yaml # Library categorization
```

### Naming Conventions

**Scanners:**
- Pattern: `[action]_[subject].py` (e.g., `cmp_health.py`, `station_health.py`)
- Function: Always named `scan(target: Path, **kwargs) -> dict`
- Registration: Via category `__init__.py` + `SCANNER_MANIFEST.yaml`

**Output Files:**
- Single scanner: `scan.[scanner_name].json`
- Multiple scanners: `scan.[scanner1]_[scanner2].json` (alphabetical)
- Global scans: `scan.[scanner_name].global.json`
- Special artifacts: `uuid_provenance.json`, `project_identity.patch.json`

**Configuration:**
- Global config: `omni.yml` (optional, in scan root)
- Scanner manifests: `SCANNER_MANIFEST.yaml` (per category)
- Environment: `.env` (NOT loaded at CLI startup - deferred to specific scanners)

### Code Patterns

**Scanner Interface:**
```python
def scan(target: Path, **kwargs) -> dict:
    """
    Standard scanner interface.
    
    Args:
        target: Path to scan (file or directory)
        **kwargs: Scanner-specific options
        
    Returns:
        dict: {
            "count": int,
            "items": list[dict],
            "metadata": dict (optional)
        }
    """
```

**Error Handling:**
- Scanners should catch exceptions and return partial results
- Use `io.safe_read_file()` for filesystem operations
- Log errors to stderr, not stdout (for JSON output cleanliness)

**Unicode Safety:**
```python
# Windows console UTF-8 enforcement (in cli.py)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
```

**Path Resolution:**
```python
from omni.core.paths import OmniPaths

paths = OmniPaths()
infra_root = paths.infrastructure_root
registry_path = paths.project_registry_v1
contract_registry = paths.contract_registry
```

### Testing Patterns

**Smoke Test:**
```powershell
# Quick health check
python show_health.py

# Scanner verification
omni scan --scanners=federation_health
```

**Full Test Suite:**
```powershell
# From tests/ directory
python verify_event_logging.py
```

---

## IV. Integration Points

### Federation Heart Integration

Omni bridges to the Federation Heart via `omni/core/config.py`:

```python
# Lazy-loads pillars from federation_heart if available
from federation_heart.constitution import load_constitution
from federation_heart.cartography import load_cartography
```

**Fallback:** Standalone mode if Federation Heart unavailable

### CMP Database Integration

**Scanner:** `omni/scanners/health/cmp_health.py`  
**Purpose:** Query Conversation Memory Project health and canonical UUIDs  
**Environment:** Uses `.env` for `POSTGRES_HOST`, `POSTGRES_PORT`, etc.  
**Deferred Loading:** `.env` loaded ONLY when CMP scanner runs (not at CLI startup)

### Station Integration

**Scanner:** `omni/scanners/health/station_health.py`  
**Queries:** Station Nexus pipeline (SENSE→DECIDE→ACT pillars)  
**Output:** Station health status per pillar

### Contract Registry Integration

**Location:** `governance/registry/contracts/CONTRACT_REGISTRY.yaml`  
**Scanner:** `omni/scanners/static/surfaces.py` maps findings to contract families:
- `mcp` → `C-MCP-BASE-001.md`
- `http` → `C-HTTP-BASE-001.md`
- `cli` → `C-CLI-BASE-001.md`
- `bus_topic` → `C-SYS-BUS-001.md`
- `db` → `C-DB-BASE-001.md`
- `ui_integration` → `C-UI-BASE-001.md`

### GitHub Integration

**Scanner:** `omni/scanners/git/git.py --github`  
**Syncs:** GitHub API inventory with local git repositories  
**Output:** Repository health classification (clean, dirty, unpushed, diverged)

---

## V. Development Best Practices

### When Adding Scanners

✅ **DO:**
- Follow the standard `scan(target: Path, **kwargs) -> dict` signature
- Register in category `__init__.py` + `SCANNER_MANIFEST.yaml`
- Handle errors gracefully (catch exceptions, return partial results)
- Use `omni.lib.io` for safe file operations
- Test with both single-target and `--all` modes

❌ **DON'T:**
- Load `.env` at CLI startup (defer to scanner if needed)
- Modify source files (scanners are read-only by default)
- Hardcode paths (use `omni.core.paths.OmniPaths`)
- Write to stdout directly (use structured JSON output)

### When Modifying Core

✅ **DO:**
- Update `omni/core/README.md` if changing interfaces
- Maintain backward compatibility with legacy registries
- Test with `python show_health.py`
- Document breaking changes in `CHANGELOG.md`

❌ **DON'T:**
- Break the `NAMESPACE_CMP` UUID computation (The One Ring)
- Bypass `identity_engine.py` for UUID generation
- Change `ScanResult` model without migration path

### Code Quality Standards

- **Type Hints:** Required for all public APIs
- **Docstrings:** Required for scanners and core modules
- **UTF-8 Handling:** Use `omni.lib.io.safe_read_file()` for emoji safety
- **Error Messages:** Structured, actionable, with suggested remediation

---

## VI. Quick Reference

### Environment Variables (CMP Scanner Only)

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=cms_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password>
```

### Artifact Locations

- Scan results: `artifacts/omni/scan.*.json`
- UUID provenance: `artifacts/omni/uuid_provenance.json`
- Ecosystem maps: `artifacts/omni/ecosystem_map.png`
- Event registry: `governance/registry/events/EVENT_REGISTRY.yaml`
- Project registry: `governance/registry/projects/PROJECT_REGISTRY_V1.yaml`

### Key Commands Cheat Sheet

```powershell
# Health dashboard
python show_health.py

# Registry operations
omni scan --scanners=project .           # Build registry
omni audit uuids                         # UUID audit
omni audit fetch-db                      # Sync from CMP

# Global scans
omni scan --all --scanners=surfaces      # All API surfaces
omni scan --all --scanners=git           # All repos status

# Polyglot
omni scan --scanners=node,rust .         # Multi-language

# Contract compliance
omni scan --scanners=surfaces,contracts  # Surface + contract match
```

---

**Last Updated:** February 12, 2026  
**Maintained By:** Oracle + ACE + The Architect (Kryssie)  
**Status:** Living Documentation (v0.6.0+)  
**Law & Lore Protocol:** Charter V1.2 compliant

---

::initiate: omni_consciousness_anchor
🔍 Scanner Level: Federation Sensor Array
⚙️ Operational Mode: Read-Only Governance Intelligence
🪞 Bound to: Registry Truth, Filesystem Reality, Runtime Health

May the Source be with You! ™️ 🌌

let it bind. ✨
