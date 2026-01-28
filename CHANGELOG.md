# Omni Changelog

## v0.6.0 - The Federation Nervous System
**Date**: January 2, 2026

### Added
- **Polyglot Scanners**:
    - `node_scanner.py` - Deep package.json analysis for JavaScript/TypeScript projects
    - `rust_scanner.py` - Deep Cargo.toml analysis for Rust crates
- **Runtime Health Scanners** (Federation Heart Integration):
    - `federation_health.py` - Queries FederationCore.status() for system health
    - `station_health.py` - Queries Station Nexus for pipeline status (SENSE→DECIDE→ACT)
    - `cmp_health.py` - Queries Conversation Memory Project for database and memory lane health
    - `pillar_health.py` - Queries all Federation Heart pillars for detailed status
    - `tunnel_status.py` - Queries active Cloudflare and ngrok tunnels
- **Documentation**:
    - `omni/core/README.md` - Complete documentation of all 15 core modules
    - `omni/core/scanners/README.md` - Complete documentation of all 15 scanners

### Changed
- Scanner registry now supports 15 total scanners (up from 8)
- Health scanners provide real-time runtime telemetry from Federation components

### Technical Details
- Total scanners: 15 (8 static + 2 polyglot + 5 runtime health)
- Integration with `federation_heart` for runtime queries
- Support for Node.js, Rust, and Python ecosystem analysis
- Real-time health monitoring for pillars, stations, and memory substrate

---

## v0.5.0 - The Unification
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

## v0.1.0 - Initial Release
- Basic `surface_scanner` functionality.
- `gate` command for compliance checks.
