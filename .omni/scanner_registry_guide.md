# Omni Scanner Registry Guide

## Capabilities
- **10 Scanner Categories**, **43 Scanners**, **14 CLI Commands**
- Introspection via `omni_introspect` (show_drift, verbose flags)
- Dynamic discovery via `OmniIntrospector` class

## Categories

| Category | Count | Purpose |
|----------|-------|---------|
| **database** | 5 | CMP entity scanning (agents, artifacts, conversations, entities, projects) |
| **discovery** | 8 | Structure discovery: archives, canon, census, CLI, cores, MCP servers, projects |
| **fleet** | 1 | Fleet registry generation |
| **git** | 3 | Commit history, repo status, velocity metrics |
| **health** | 5 | Runtime health: CMP, Federation, pillars, stations, tunnels |
| **library** | 6 | Cognitive/deep analysis: cohesion, content, empty folders, graphs, library census, rituals |
| **phoenix** | 3 | Git resurrection: archive scanning, orphan detection, temporal gap analysis |
| **polyglot** | 3 | Language ecosystems: Node.js, packages, Rust |
| **search** | 1 | Pattern/regex search with context |
| **static** | 8 | Filesystem analysis: contracts, deps, docs, events, hooks, surfaces, tools, UUIDs |

## Known Drift (Feb 2026)
- **discovery**: `archive_scanner`/`census`/`cli_edge_scanner` undocumented in manifest
- **git**: `commit_history` vs manifest's `commit-history` (naming mismatch)
- **phoenix**: All 3 scanners use underscores but manifest uses hyphens
- **polyglot**: `node_scanner` vs `node`, `package_scanner` vs `packages`

## Key Insight
Drift is largely **naming convention mismatches** (underscores vs hyphens in manifests vs filenames). Not missing functionality — cosmetic issue in manifests.
