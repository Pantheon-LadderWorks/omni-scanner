![Omni Header](assets/omni_header.png)

# 🌌 OMNI: Federation Governance Tricorder

**Version:** 0.5.0  
**Status:** Living (Schema Versioned; Read-Only by Default)  
**Objective:** Unified governance, mapping, and audit — with receipts.

---

## 🎯 Executive Summary
**OMNI** is the sensor array for the **SERAPHINA Federation**: a single CLI that audits identity, maps ecosystem topology, and generates actionable governance reports.

> *"We don't guess. We scan."*

**Outputs:** `artifacts/omni/` (JSON reports, Markdown guides, and graphs)

---

## 🚀 Getting Started

### Windows (Recommended)
```powershell
cd Infrastructure/tools
.\omni.bat audit uuids
```

### Cross-Platform
```bash
cd Infrastructure/tools
python -m omni audit uuids
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

### 5. Legacy & Maintenance
*   **`omni scan`**: Original surface scanner (Routes/Docs).
*   **`omni inspect`**: Deep inspection of a single repository.
*   **`omni gate`**: CI/CD compliance check.

---

## � Safety Defaults
*   **Read-only by default:** OMNI does not modify source files unless explicitly invoked with a specific command (e.g., `lock`, `render`).
*   **Sensitive-path denylist:** Automatically ignores `.env`, `.git`, `__pycache__`, and credentials.
*   **Non-Destructive:** All reports are saved to `artifacts/omni/`, never overwriting source code.

---

## 🏗️ Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md) for the "Living Source of Truth" blueprint.

## ⚖️ License
MIT License. See [LICENSE](LICENSE).

---
*Forged by The Architect & Antigravity (Approved by Mega)*
