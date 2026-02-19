# 🏗️ Architecture Scanners

**Category**: `architecture`
**Scanners**: 4
**Dependencies**: None (stdlib only)

> *Structural enforcement scanners — these instruments guard the boundaries of your architecture, detecting import violations, coupling pathologies, and drift between map and territory.*

---

## Scanner Inventory

| Scanner        | File            | Description                                                                     |
| :------------- | :-------------- | :------------------------------------------------------------------------------ |
| **compliance** | `compliance.py` | Enforces structural standards — validates required files per architectural area |
| **coupling**   | `coupling.py`   | Builds dependency graphs to detect cycles and god modules                       |
| **drift**      | `drift.py`      | Compares Registry (map) vs. Filesystem (territory) to detect ghosts and rogues  |
| **imports**    | `imports.py`    | Scans for import boundary violations — pillar bypass, cross-area imports        |

## Key Concepts

### Drift Detection
The `drift` scanner compares what the project registry says should exist against what actually exists on disk:
- **Ghosts**: Registered but not found on disk
- **Rogues**: Found on disk but not registered

### Coupling Analysis
The `coupling` scanner builds a dependency graph from imports and detects:
- **Cycles**: Circular dependencies between modules
- **God Modules**: Modules with excessive fan-in or fan-out

## Usage

```bash
omni scan . --scanner drift
omni scan . --scanner imports
omni scan . --scanner coupling
omni scan . --scanner compliance
```

## Contract
All scanners follow `C-TOOLS-OMNI-SCANNER-001` — read-only, safe failure, `scan(target: Path) → dict`.

---

*← Back to [Scanner Architecture Guide](../README.md)*
