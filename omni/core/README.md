# 🧠 Omni Core Kernel

**Location:** `omni/core/`  
**Purpose:** Core intelligence and orchestration layer for the Federation Tricorder  
**Version:** 0.7.0 (Federation Instrument Pattern)  
**Status:** Canonical Kernel

---

## 📋 The Kernel Registry

The Core has been slimmed down to the absolute essentials. These modules form the **Conductor** of the Federation Instrument.

### 🧬 Identity & Truth

#### `identity_engine.py` (**The One Ring**)
- **Type:** Identity Resolution Engine
- **Purpose:** The Single Source of Truth for Project Identity.
- **Responsibilities:**
  - Defines the canonical `NAMESPACE_CMP` (The One Ring).
  - Computes deterministic UUIDv5s from project keys.
  - Enforces conflict resolution policies (Policy C: Freeze & Adjudicate).
  - Resolves "Ghost" vs "Living" project states.
- **Key Models:** `ProjectIdentity`, `RepoInventoryItem`

#### `registry_builder.py` (**The Truth Maker**)
- **Type:** Registry Construction
- **Purpose:** Derives `PROJECT_REGISTRY_V1.yaml` from authoritative sources.
- **Responsibilities:**
  - Ingests GitHub Inventory (`repo_inventory.json`).
  - Scans local filesystem (via `scanners/git`).
  - Applies Governance Overrides (`LOCAL_OVERRIDES_V1.yaml`).
  - Merges Legacy Oracle data.
  - Produces the High-Fidelity Registry.

#### `registry.py`
- **Type:** Registry Parser
- **Purpose:** operational interface for reading registries.
- **Capabilities:**
  - Parses `PROJECT_REGISTRY_V1.yaml` (New Standard).
  - Parses legacy markdown registries (Backward Compatibility).
  - Provides `parse_master_registry_md` for legacy translation.

---

### 🎹 Orchestration & Systems

#### `system.py` (**The Instrument**)
- **Type:** OmniInstrument Orchestrator
- **Purpose:** The main entry point that boots the system.
- **Responsibilities:**
  - Initializes Pillars (lazy-loaded).
  - Dispatches commands to the appropriate subsystem.
  - Manages the lifecycle of a scan operation.
  - Orchestrates the "Scan → Analyze → Report" loop.

#### `config.py` (**The Bridge**)
- **Type:** Configuration Shim
- **Purpose:** Bridges Omni to the Federation Heart.
- **Responsibilities:**
  - Lazy-loads `constitution` and `cartography` pillars from `federation_heart`.
  - Provides standalone fallbacks if the Heart is missing.
  - Loads `omni.yml` configuration checks.

#### `paths.py` (**Tier 1 Anchor**)
- **Type:** Path Resolution
- **Purpose:** Foundational identifying of "Where Things Are".
- **Capabilities:**
  - Locates Infrastructure Root.
  - Locates Workspace and Deployment roots.
  - Locates Tier 1 Manifests (`CONTRACT_REGISTRY`, `LOCAL_OVERRIDES`).
  - **Note:** Does NOT depend on dynamic manifests (avoids circular dependency).

---

### 🛡️ Shared Logic

#### `model.py`
- **Type:** Data Models
- **Purpose:** The universal language of scan results.
- **Key Classes:**
  - `ScanResult`: The standard contract for all scanners.
  - `ScanFinding`: Structured finding format.

#### `gate.py`
- **Type:** Policy Enforcement
- **Purpose:** The Gatekeeper's logic enforcement.
- **Capabilities:**
  - Validates scan results against Constitutional policies.
  - Enforces "No New Orphans" rule.
  - Checks for critical compliance violations.

---

## 🏛️ Architecture & Migration (v0.7.0)

In the **Federation Instrument Pattern** (v0.7.0), the Core was refactored to separate **Orchestration** (Core) from **Capability** (Pillars/Lib).

### 🚛 Migrated Capabilities

Capabilities that were previously in Core have moved to specialized homes:

| Capability | Old Location | New Location |
|yy----------|--------------|--------------|
| **Intelligence** | `brain.py`, `librarian.py` | `omni/pillars/intel.py` |
| **Cartography** | `cartographer.py`, `fetcher.py` | `omni/pillars/cartography.py` |
| **Gatekeeping** | `provenance.py` | `omni/pillars/gatekeeper.py` |
| **Rendering** | `renderer.py`, `tree.py` | `omni/lib/renderer.py`, `omni/lib/tree.py` |
| **Reporting** | `reporting.py` | `omni/lib/reporting.py` |
| **Requirements** | `requirements.py` | `omni/lib/requirements.py` |
| **I/O Ops** | `io.py` | `omni/lib/io.py` |

### 🐝 Scanners Subsystem

Scanners are no longer a flat list in `core/scanners/`. They are now a **Domain-Driven Plugin System** in `omni/scanners/`.

**Categories:**
*   `static/` - Filesystem analysis (Docs, Contracts, Deps)
*   `polyglot/` - Language ecosystems (Node, Rust)
*   `health/` - Runtime health checks (Federation, Station)
*   `discovery/` - Structure discovery (Cores, CLI)
*   `git/` - Git repositories
*   `fleet/` - Fleet registry generation

Each category is dynamically loaded via `SCANNER_MANIFEST.yaml`.

---

## 🔄 Data Flow

```
Filesystem Reality
       ↓
   Scanners (omni/scanners/)
       ↓
   Core Kernel (omni/core/)
       ↓
Registry Truth (governance/)
       ↓
   Reports (omni/artifacts/)
```

### Key Principle
> **The Registry is God.** The Core Kernel reconciles filesystem reality with registry truth using the `registry_builder`.

---

*Last Updated: February 2, 2026 (v0.7.0)*  
*Maintained by: The Federation*  
*Constitutional Authority: Charter V1.2*