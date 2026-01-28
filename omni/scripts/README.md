# Omni Scripts & Maintenance Tools

This directory contains utility scripts for the Omni Governance tool and the wider Federation Infrastructure.

## Directory Structure
- **archive/**: Historical outputs, reports, and one-off artifacts.
- **scripts/**: Active maintenance scripts moved from the `tools/` root.

## Script Descriptions

### Registry Management
- `hydrate_registry_final.py`: The main script for hydrating `PROJECT_REGISTRY_MASTER.md` from the Postgres database.
- `hydrate_registry_pg.py`: An alternative/precursor hydration script using `ruamel.yaml`.
- `remediate_registry_identity.py`: Fixes specific identity divergences (Atlas Forge, Quantum, Scribes Anvil).
- `refactor_registry.py`: Normalizes and processes the registry markdown/yaml structure.
- `sync_registry_uuids.py`: Synchronizes UUIDs across the registry.

### Analysis & Debugging
- `analyze_merge_plan.py`: Analyzes potential merge conflicts or strategies.
- `analyze_trinity.py`: Analyzes the "Trinity" of data sources (Registry, DB, Code).
- `analyze_uuid_json.py`: UUID analysis tool.
- `debug_scribes.py`: Debugging script for Scribes Anvil integration.
- `inspect_schema.py` / `inspect_schema_pg.py`: Database schema inspection tools.
- `wire_uuid_universal.py`: Universal UUID wiring utility.

## Usage
These scripts are intended to be run with the `Infrastructure` root in your `PYTHONPATH`.

Example:
```bash
$env:PYTHONPATH="C:\Users\kryst\Infrastructure"; python C:\Users\kryst\Infrastructure\tools\omni\scripts\hydrate_registry_final.py
```
