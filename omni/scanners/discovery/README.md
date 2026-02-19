# 🔎 Discovery Scanners

**Category**: `discovery`
**Scanners**: 8
**Dependencies**: None (stdlib only)

> *Component cataloging scanners — these instruments traverse your codebase to discover projects, CLI commands, MCP servers, archives, and other structural landmarks. They answer the question: "What exists here?"*

---

## Scanner Inventory

| Scanner                  | File                      | Description                                                                                                        |
| :----------------------- | :------------------------ | :----------------------------------------------------------------------------------------------------------------- |
| **project**              | `project.py`              | Builds `PROJECT_REGISTRY_V1.yaml` from sources                                                                     |
| **cli**                  | `cli.py`                  | Scans for CLI commands (`@command` decorators)                                                                     |
| **cores**                | `cores.py`                | Discovers core files in projects                                                                                   |
| **canon**                | `canon.py`                | CodeCraft canon scanner                                                                                            |
| **census**               | `census.py`               | File census by dimensional slicing (extensions, sizes, workspaces)                                                 |
| **mcp_server_discovery** | `mcp_server_discovery.py` | Discovers MCP servers across all workspaces via `@server` decorators and `Server()` instantiation                  |
| **archive_scanner**      | `archive_scanner.py`      | General-purpose archive scanner (.zip, .tar.gz, .tar.bz2, .tar.xz) — detects .git, node_modules, security concerns |
| **cli_edge_scanner**     | `cli_edge_scanner.py`     | CLI edge case detection                                                                                            |

## Usage

```bash
# Discover all projects
omni scan . --scanner project

# Find CLI commands
omni scan . --scanner cli

# Census your workspace
omni scan . --scanner census

# Discover MCP servers
omni scan . --scanner mcp_server_discovery
```

## Contract
All scanners follow `C-TOOLS-OMNI-SCANNER-001` — read-only, safe failure, `scan(target: Path) → dict`.

---

*← Back to [Scanner Architecture Guide](../README.md)*
