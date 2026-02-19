# 📁 Static Scanners

**Category**: `static`
**Scanners**: 9
**Dependencies**: None (stdlib only)

> *Filesystem analysis scanners — no runtime dependencies required. These are the foundation instruments that map your codebase's structural anatomy.*

---

## Scanner Inventory

| Scanner           | File                 | Description                                                         |
| :---------------- | :------------------- | :------------------------------------------------------------------ |
| **surfaces**      | `surfaces.py`        | Scans for contract surfaces (`.contract.yaml` files)                |
| **docs**          | `docs.py`            | Scans for documentation files (README, ARCHITECTURE, etc.)          |
| **deps**          | `deps.py`            | Scans for dependency files (requirements.txt, pyproject.toml, etc.) |
| **contracts**     | `contracts.py`       | Scans for contract definitions                                      |
| **tools**         | `tools.py`           | Scans for tool definitions                                          |
| **uuids**         | `uuids.py`           | Scans for UUID references across the codebase                       |
| **hooks**         | `hooks.py`           | Scans for git hooks (.git/hooks/)                                   |
| **events**        | `events.py`          | Scans for event schema definitions (`.publish()`, `crown://`)       |
| **imports_check** | `generic_imports.py` | Config-driven import bans and restrictions                          |

## Usage

```bash
# Run all static scanners
omni scan . --category static

# Run a specific static scanner
omni scan . --scanner surfaces
omni scan . --scanner docs
```

## Contract
All scanners follow `C-TOOLS-OMNI-SCANNER-001` — read-only, safe failure, `scan(target: Path) → dict`.

---

*← Back to [Scanner Architecture Guide](../README.md)*
