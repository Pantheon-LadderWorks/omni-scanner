# Omni Changelog

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
