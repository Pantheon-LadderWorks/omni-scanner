# Omni Changelog

## v0.7.0 — The Infinite Gaze (Documentation & Expansion)
**Date**: February 19, 2026

### 🌟 Highlights
- **55 Scanners**: From 21 to 55 — the Sensorium more than doubled.
- **12 Scanner Categories**: 7 new categories added (architecture, database, db, library, phoenix, search + expansions).
- **MCP Server**: All scanners exposed as AI-callable MCP tools.
- **Complete Documentation Overhaul**: Every README, architecture doc, and contributor guide rewritten.

### Added — New Scanner Categories
- **🏗️ Architecture** (4 scanners):
    - `compliance.py` — Structural standards enforcement (required files per area)
    - `coupling.py` — Dependency graph analysis, cycle detection, god modules
    - `drift.py` — Registry vs. filesystem comparison (ghost/rogue detection)
    - `imports.py` — Import boundary violation scanning (pillar bypass, cross-area)
- **📚 Library** (6 scanners):
    - `cohesion.py` — Folder cohesion analysis (module vs. dump ground)
    - `content.py` — Deep content analysis (frontmatter, keywords, shebangs)
    - `empty_folders.py` — Empty semantic structure detection
    - `graph.py` — Knowledge graph link extraction
    - `library.py` — Document census with freshness tracking
    - `rituals.py` — CodeCraft ritual and school signature detection
- **🔥 Phoenix** (3 scanners) *(Federation-exclusive)*:
    - `archive_scanner.py` — Git repository discovery in zip archives
    - `orphan_detector.py` — Orphaned commit detection between archive and repo
    - `temporal_gap_analyzer.py` — Comprehensive resurrection intelligence
- **🔍 Search** (3 scanners):
    - `file_search.py` — Fast file search by name/pattern
    - `pattern_search.py` — Regex pattern search with context lines
    - `text_search.py` — Text search across codebases
- **🗃️ Database** (5 scanners) *(Federation-exclusive)*:
    - `cmp_agents.py` — CMP agents table scanning
    - `cmp_artifacts.py` — CMP artifacts table scanning
    - `cmp_conversations.py` — CMP conversations table scanning
    - `cmp_entities.py` — Entity mentions / knowledge graph scanning
    - `cmp_projects.py` — CMP projects table scanning
- **🗄️ DB** (1 scanner):
    - `generic.py` — Configuration-driven database scanning

### Added — Scanner Expansions
- **Discovery** (3 new scanners):
    - `archive_scanner.py` — General-purpose archive scanning (.zip, .tar.gz)
    - `cli_edge_scanner.py` — CLI edge case detection
    - `mcp_server_discovery.py` — MCP server discovery across workspaces
- **Git** (3 new scanners):
    - `commit_history.py` — Complete commit history resurrection evidence
    - `pr_telemetry.py` — PR health and drift detection (The Telepath)
    - `velocity.py` — Git velocity measurement (EMERGENCE AT VELOCITY metrics)
- **Health** (4 new scanners) *(Federation-exclusive)*:
    - `cmp_health.py` — CMP database health checks
    - `pillar_health.py` — Federation pillar status monitoring
    - `system.py` — System-level health checks
    - `tunnel_status.py` — Tunnel connectivity verification
- **Static** (1 new scanner):
    - `generic_imports.py` — Config-driven import bans and restrictions
- **Fleet** (1 scanner) *(Federation-exclusive)*:
    - `fleet.py` — Fleet registry generation and validation

### Added — Infrastructure
- **MCP Server** (`mcp_server/`):
    - `omni_mcp_server.py` — Full MCP server wrapping all 55 scanners
    - `omni_dev_watcher.py` — Hot-reload watcher for scanner development
    - `config.py` — MCP server configuration
- **Identity Engine** (`omni/core/identity_engine.py`):
    - Pydantic models for identity exchange
    - Deterministic UUIDv5 minting from NAMESPACE_CMP
    - Policy C: Freeze & Adjudicate conflict resolution
- **Introspection**: `omni introspect` now reports documentation drift

### Changed
- **Documentation**: Complete rewrite of `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `ROADMAP.md`
- **Scanner README**: Expanded from 21 to 55 scanner documentation
- **Per-category READMEs**: Each scanner category now has its own README

---

## v0.6.0 — The Open Eye (Open Source Release)
**Date**: February 19, 2026

### 🌟 Highlights
- **Open Source Release**: Fully decoupled from Federation private infrastructure.
- **The Trinity Architecture**: Formalized the 3-Layer Protocol (Core, Senses, Hands).
- **Mythological Documentation**: Aligned all docs with Federation Lore (LOST v4).

### Added
- **Polyglot Scanners**:
    - `node_scanner.py` — Deep package.json analysis.
    - `rust_scanner.py` — Deep Cargo.toml analysis.
- **Runtime Health Scanners** (Federation Awareness):
    - `federation_health.py` — Queries FederationCore status.
    - `station_health.py` — Queries Station Nexus pipeline.
- **Contracts**:
    - Added 5 Crown Contracts (`C-TOOLS-OMNI-*`) defining the laws of the system.

### Changed
- **Architecture Refactor**: Split into Core (Shim), Scanners (Plugins), and Builders (Mutators).
- **Core**: Implemented "Heart-First, Fallback-Second" logic for standalone operation.
- **Documentation**: Complete rewrite of `README.md`, `ARCHITECTURE.md`, and `CONTRIBUTING.md`.

---

## v0.5.0 — The Unification
**Date**: December 2025

### Added
- **Unified CLI**: Consolidated disparate `tools/` scripts into `omni` command.
- **Audit Suite**:
    - `audit uuids` (Provenance Index)
    - `audit deps` (Requirement Scanning)
    - `audit lock` (Version Locking)
    - `audit fetch-db` (DB Sync)
- **Cartography**: Integrated `ecosystem_cartographer.py` as `omni map`.
- **Tree**: Integrated `kryst_tree_clean.py` as `omni tree`.
- **Registry V2**: Full support for Identity+Facets frontmatter schema.
- **Event Surface Scanner**:
    - `omni scan` for mapping `.publish(...)` and `crown://` events.
    - `omni registry events` for generating `EVENT_REGISTRY.yaml`.
    - `omni.core.tap.CrownBusTap` utility.
    - `omni.yml` configuration support.

### Changed
- Moved `audit_provenance.py` → `omni.core.provenance`.
- Moved `render_registry.py` → `omni.core.renderer`.
- Moved `fetch_canonical_uuids.py` → `omni.core.fetcher`.
- Moved `generate/dedupe/lock` scripts → `omni.core.requirements`.
- All tools now respect `artifacts/omni/` output directory.

### Removed
- Loose scripts in `Infrastructure/tools/` (Moved to `omni/archive/`).

---

## v0.1.0 — Initial Release
- Basic `surface_scanner` functionality.
- `gate` command for compliance checks.
