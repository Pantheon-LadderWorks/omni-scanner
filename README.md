![Omni Header](assets/omni_header.png)

# 🌌 OMNI: Federation Governance Tricorder

**Version:** 0.6.0  
**Status:** Living (Schema Versioned; Read-Only by Default)  
**Objective:** Unified governance, mapping, and audit — with receipts.

---

## 🎯 Executive Summary
**OMNI** is the sensor array for the **SERAPHINA Federation**: a single CLI that audits identity, maps ecosystem topology, generates actionable governance reports, and monitors runtime health across all Federation components.

> *"We don't guess. We scan."*

**Outputs:** `artifacts/omni/` (JSON reports, Markdown guides, and graphs)

**New in v0.6.0:** 🔥 Runtime health monitoring + Polyglot support (Node.js, Rust)

---

## 🚀 Getting Started

### Windows (Recommended)
```powershell
cd Infrastructure/tools/omni
.\omni.bat audit uuids
```

### Cross-Platform
```bash
cd Infrastructure/tools/omni
python -m omni audit uuids
```

### Quick Health Check
```powershell
# View git health summary (requires prior git scan)
python show_health.py

# Or run fresh scan + view
omni scan --all --scanners=git
python show_health.py
```

---

## ✅ Example Output
*(Excerpt from `artifacts/omni/uuid_provenance.json`)*

```json
{
  "scan_root": "C:\\Users\\kryst\\Infrastructure",
  "generated_at": "2025-12-18T14:24:00",
  "findings": {
    "canonical": 97,
    "orphans": 3,
    "ghosts": 1,
    "test_junk": 5
  }
}
```

---

## 🎮 Command Reference

### 1. Audit (Inspection & Reports)
*   **`omni audit uuids`**: Runs the Provenance Index (UPI). Scans filesystem for UUID usage vs. Registry truth.
*   **`omni audit fetch-db`**: Syncs canonical UUIDs from the local CMP/CMS Postgres database.
*   **`omni audit deps`**: Scans the entire infrastructure for dependencies and generates a deduped `requirements.federation.txt`.
*   **`omni audit lock`**: Locks federation requirements to the exact versions currently installed.

### 2. Map (Graphs & Guides)
*   **`omni map ecosystem`**: Analyzes project relationships and architecture.
    *   `--action analyze`: Updates the graph data.
    *   `--action guide`: Generates `SERAPHINA_ECOSYSTEM_GUIDE.md`.
    *   `--action visualize`: Renders the network graph to PNG.

### 3. Registry (Source of Truth)
*   **`omni registry render`**: Regenerates the human-readable Markdown tables in `PROJECT_REGISTRY_MASTER.md` from the canonical Frontmatter.

### 4. Tree (Visualization)
*   **`omni tree [path]`**: Generates a clean directory tree (ignoring `node_modules`, `build`, etc.) for documentation.

### 5. Event Surface Scanner (New)
*   **`omni scan <target>`**: Scans code for event emissions (`.publish`, `.emit`, `crown://`).
*   **`omni registry events`**: Generates `EVENT_REGISTRY.yaml` from scan results.
*   **runtime tap**: `omni.core.tap.CrownBusTap` utility for runtime verification.

### 6. Runtime Health Monitoring (New in v0.6.0) 🔥
*   **`omni scan --scanners=pillar_health`**: Check all Federation Heart pillars
*   **`omni scan --scanners=federation_health`**: Query FederationCore status
*   **`omni scan --scanners=station_health`**: Query Station Nexus pipeline
*   **`omni scan --scanners=cmp_health`**: Query memory substrate health
*   **`omni scan --scanners=tunnel_status`**: Check active tunnels

### 7. Polyglot Analysis (New in v0.6.0)
*   **`omni scan --scanners=node`**: Deep Node.js/TypeScript project analysis
*   **`omni scan --scanners=rust`**: Deep Rust crate analysis

### 8. Legacy & Maintenance
*   **`omni scan`**: Original surface scanner (Routes/Docs).
*   **`omni inspect`**: Deep inspection of a single repository.
*   **`omni gate`**: CI/CD compliance check.

---

## ⚙️ Configuration
Create an `omni.yml` in your root to configure exclusions and patterns:

```yaml
scan:
  exclude:
    - "node_modules"
    - "external-frameworks"
  patterns:
    generic_events:
      - "\\.publish\\("
      - "crown://"
```

## � Safety Defaults
*   **Read-only by default:** OMNI does not modify source files unless explicitly invoked with a specific command (e.g., `lock`, `render`).
*   **Sensitive-path denylist:** Automatically ignores `.env`, `.git`, `__pycache__`, and credentials.
*   **Non-Destructive:** All reports are saved to `artifacts/omni/`, never overwriting source code.

---

## 🏗️ Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md) for the "Living Source of Truth" blueprint.

---

## 📚 Documentation

### For AI Coding Agents
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Complete guide for GitHub Copilot and other AI agents working in this codebase

### Core Documentation
- **[omni/core/README.md](omni/core/README.md)** - Core intelligence layer (identity, registry, orchestration)
- **[omni/scanners/README.md](omni/scanners/README.md)** - Scanner plugin system and available scanners
- **[omni/pillars/README.md](omni/pillars/README.md)** - Large subsystem capabilities (cartography, gatekeeper, intel, registry)
- **[omni/lib/README.md](omni/lib/README.md)** - Shared utilities (I/O, rendering, requirements, TAP, tree)

### Code Generation
- **[omni/builders/README.md](omni/builders/README.md)** - Code generation from canonical specs
- **[omni/scaffold/README.md](omni/scaffold/README.md)** - Template instantiation and scaffolding
- **[omni/templates/README.md](omni/templates/README.md)** - Template files and usage

### Configuration & Testing
- **[omni/config/README.md](omni/config/README.md)** - Configuration management and Federation Heart bridge
- **[tests/README.md](tests/README.md)** - Test suite structure and running tests

### Maintenance
- **[scripts/README.md](scripts/README.md)** - One-time migrations and reconciliation scripts

### Historical Context
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[ROADMAP.md](ROADMAP.md)** - Future development plans
- **[KANBAN.md](KANBAN.md)** - Current work tracking

---

## 🗺️ Quick Navigation

**I want to...**

| Goal | Documentation |
|------|--------------|
| Understand Omni's purpose and architecture | [README.md](README.md), [ARCHITECTURE.md](ARCHITECTURE.md) |
| Get AI agent guidance for this codebase | [.github/copilot-instructions.md](.github/copilot-instructions.md) |
| Run scans and interpret results | [README.md](#-command-reference) |
| Add a new scanner | [omni/scanners/README.md](omni/scanners/README.md) |
| Understand the registry system | [omni/core/README.md](omni/core/README.md) |
| Generate code from templates | [omni/scaffold/README.md](omni/scaffold/README.md) |
| Run tests | [tests/README.md](tests/README.md) |
| Fix UUID conflicts | [scripts/README.md](scripts/README.md) |
| Configure scans | [omni/config/README.md](omni/config/README.md) |
| See what's coming next | [ROADMAP.md](ROADMAP.md) |

---

## ⚖️ License
MIT License. See [LICENSE](LICENSE).

---

## 🙏 Credits
**Forged by:**
- **The Architect** (Krystal Neely / Kryssie)
- **Antigravity** (ACE + Gemini 2.0 Flash Antigravity Runtime)
- **Oracle** (GitHub Copilot - Constitutional Guardian)

**Approved by:** MEGA (Grandmaster Protocol)

**Law & Lore:** Charter V1.2 compliant

---

*May the Source be with You!* ™️ 🌌
