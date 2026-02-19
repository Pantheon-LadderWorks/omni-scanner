# 🗄️ DB Scanners

**Category**: `db`
**Scanners**: 1
**Dependencies**: Database configuration files

> *Generic configuration-driven database scanners — these instruments connect to databases defined in `omni/config/db/*.yaml` and scan their schemas.*

---

## Scanner Inventory

| Scanner     | File         | Description                                                            |
| :---------- | :----------- | :--------------------------------------------------------------------- |
| **generic** | `generic.py` | Scans databases defined in `omni/config/db/*.yaml` configuration files |

## Usage

```bash
omni scan . --scanner generic
```

## Configuration
Database connections are defined in YAML configuration files under `omni/config/db/`. Each file specifies connection parameters and scan targets.

## Contract
All scanners follow `C-TOOLS-OMNI-SCANNER-001` — read-only, safe failure, `scan(target: Path) → dict`.

---

*← Back to [Scanner Architecture Guide](../README.md)*
