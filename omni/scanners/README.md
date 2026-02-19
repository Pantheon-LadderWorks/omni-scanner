# 🔍 Omni Scanner Architecture Guide

> *"55 instruments. 12 categories. One universal contract."*

The Sensorium is Omni's perception layer — a modular, plugin-based system of scanners that observe codebases without modifying them. Every scanner implements a single contract, is auto-discovered at startup, and can be invoked via CLI or MCP.

---

## The Universal Contract

Every scanner implements this interface:

```python
def scan(target: Path) -> dict:
    """
    Observe the target directory. Return structured findings.
    
    Contract: C-TOOLS-OMNI-SCANNER-001
    - Read-only: Never modify source files
    - Safe failure: Return empty results on error, don't crash
    - Deterministic: Same input → same output
    
    Returns:
        {
            "scanner": "scanner_name",
            "category": "category_name",
            "target": str(target),
            "timestamp": "ISO-8601",
            "count": int,
            "items": [...]  # Scanner-specific findings
        }
    """
```

---

## Scanner Categories

### Open Source (Included in Build)

|   #   | Category           | Count | Description                                                                 | README                              |
| :---: | :----------------- | :---: | :-------------------------------------------------------------------------- | :---------------------------------- |
|   1   | 📁 **Static**       |   9   | Filesystem analysis — contracts, deps, docs, events, hooks, surfaces, UUIDs | [→ Details](static/README.md)       |
|   2   | 🏗️ **Architecture** |   4   | Structural enforcement — import boundaries, coupling, drift, compliance     | [→ Details](architecture/README.md) |
|   3   | 🔎 **Discovery**    |   8   | Component cataloging — projects, CLI, MCP servers, archives, census         | [→ Details](discovery/README.md)    |
|   4   | 🌐 **Polyglot**     |   4   | Language ecosystems — Python, Node.js, Rust, Go/Java/.NET/Docker            | [→ Details](polyglot/README.md)     |
|   5   | 📚 **Library**      |   6   | Document intelligence — cohesion, content depth, knowledge graphs           | [→ Details](library/README.md)      |
|   6   | 🔀 **Git**          |   5   | Repository intelligence — status, velocity, PR telemetry, history           | [→ Details](git/README.md)          |
|   7   | 🔍 **Search**       |   3   | Pattern matching — file, text, and regex search with context                | [→ Details](search/README.md)       |
|   8   | 🗄️ **DB**           |   1   | Configuration-driven database scanning                                      | [→ Details](db/README.md)           |

### Federation-Exclusive (Not in Open Source Build)

> These categories require the Federation Heart backend. They are fully functional when the Heart is installed but are not distributed with the open-source release.

|   #   | Category       | Count | Description                                                                  | README                          |
| :---: | :------------- | :---: | :--------------------------------------------------------------------------- | :------------------------------ |
|   9   | 🛡️ **Health**   |   6   | Runtime health — Federation, CMP, pillar, station, tunnel status             | [→ Details](health/README.md)   |
|  10   | 🗃️ **Database** |   5   | CMP entity scanning — agents, artifacts, conversations, entities, projects   | [→ Details](database/README.md) |
|  11   | ⚓ **Fleet**    |   1   | Fleet registry generation and validation                                     | [→ Details](fleet/README.md)    |
|  12   | 🔥 **Phoenix**  |   3   | Git history resurrection — archive scanning, orphan detection, temporal gaps | [→ Details](phoenix/README.md)  |

**Total: 55 scanners across 12 categories** (40 open source + 15 Federation-exclusive)

---

## Plugin System

### Auto-Discovery

Scanners are discovered at runtime by `omni/scanners/__init__.py`:

1. Walk all subdirectories of `omni/scanners/`
2. Look for `SCANNER_MANIFEST.yaml` in each directory
3. Parse manifest entries (name, file, function, description)
4. Dynamically import each scanner module
5. Register the `scan()` function in the global `SCANNERS` dictionary

```python
from omni.scanners import SCANNERS, SCANNER_CATEGORIES

# All 55 scanners in a flat dict
surfaces_scan = SCANNERS["surfaces"]
result = surfaces_scan(Path("."))

# Organized by category
for scanner_name, scan_fn in SCANNER_CATEGORIES["static"].items():
    result = scan_fn(target)
```

### SCANNER_MANIFEST.yaml

Each category directory contains a manifest that registers its scanners:

```yaml
category: static
description: "Filesystem analysis scanners - no runtime dependencies"
scanners:
  - name: surfaces
    file: surfaces.py
    function: scan
    description: "Scans for contract surfaces (.contract.yaml)"
  - name: docs
    file: docs.py
    function: scan
    description: "Scans for documentation files"
```

---

## Adding a New Scanner

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for the step-by-step guide. Quick summary:

1. Create `omni/scanners/<category>/my_scanner.py` with a `scan()` function
2. Add entry to `omni/scanners/<category>/SCANNER_MANIFEST.yaml`
3. Add tests in `tests/test_scanners/`
4. Update the category README
5. Run `omni introspect` to verify zero drift

---

## All 55 Scanners at a Glance

### 📁 Static (9)
| Scanner       | Description                          |
| :------------ | :----------------------------------- |
| surfaces      | Contract surfaces (`.contract.yaml`) |
| docs          | Documentation files                  |
| deps          | Dependency files                     |
| contracts     | Contract definitions                 |
| tools         | Tool definitions                     |
| uuids         | UUID references                      |
| hooks         | Git hooks                            |
| events        | Event schema definitions             |
| imports_check | Config-driven import bans            |

### 🏗️ Architecture (4)
| Scanner    | Description                        |
| :--------- | :--------------------------------- |
| compliance | Structural standards enforcement   |
| coupling   | Dependency graph / cycle detection |
| drift      | Registry vs. filesystem comparison |
| imports    | Import boundary violations         |

### 🔎 Discovery (8)
| Scanner              | Description               |
| :------------------- | :------------------------ |
| project              | Project registry builder  |
| cli                  | CLI command discovery     |
| cores                | Core file discovery       |
| canon                | CodeCraft canon scanning  |
| census               | File census by dimension  |
| mcp_server_discovery | MCP server discovery      |
| archive_scanner      | Archive contents scanning |
| cli_edge_scanner     | CLI edge case detection   |

### 🌐 Polyglot (4)
| Scanner         | Description                       |
| :-------------- | :-------------------------------- |
| package_scanner | Python projects                   |
| node_scanner    | Node.js projects                  |
| rust_scanner    | Rust projects                     |
| generic         | Go, Java, .NET, Docker, Terraform |

### 📚 Library (6)
| Scanner       | Description                    |
| :------------ | :----------------------------- |
| library       | Document census with freshness |
| cohesion      | Folder cohesion analysis       |
| content       | Deep content analysis          |
| graph         | Knowledge graph extraction     |
| empty_folders | Empty structure detection      |
| rituals       | CodeCraft ritual detection     |

### 🔀 Git (5)
| Scanner        | Description                  |
| :------------- | :--------------------------- |
| git            | Repository status            |
| velocity       | Development velocity metrics |
| commit_history | Complete commit history      |
| pr_telemetry   | PR health / drift detection  |
| git_util       | Shared git utilities         |

### 🔍 Search (3)
| Scanner        | Description                       |
| :------------- | :-------------------------------- |
| pattern_search | Regex/pattern search with context |
| file_search    | File discovery by name/pattern    |
| text_search    | Full-text search                  |

### 🗄️ DB (1)
| Scanner | Description                     |
| :------ | :------------------------------ |
| generic | Config-driven database scanning |

### 🛡️ Health (6) — *Federation-Exclusive*
| Scanner           | Description             |
| :---------------- | :---------------------- |
| federation_health | Federation Heart status |
| cmp_health        | CMP database health     |
| pillar_health     | Pillar status           |
| station_health    | Station runtime status  |
| tunnel_status     | Tunnel connectivity     |
| system            | System-level health     |

### 🗃️ Database (5) — *Federation-Exclusive*
| Scanner           | Description                       |
| :---------------- | :-------------------------------- |
| cmp_agents        | CMP agents table                  |
| cmp_artifacts     | CMP artifacts table               |
| cmp_conversations | CMP conversations table           |
| cmp_entities      | Entity mentions (knowledge graph) |
| cmp_projects      | CMP projects table                |

### ⚓ Fleet (1) — *Federation-Exclusive*
| Scanner | Description               |
| :------ | :------------------------ |
| fleet   | Fleet registry generation |

### 🔥 Phoenix (3) — *Federation-Exclusive*
| Scanner               | Description               |
| :-------------------- | :------------------------ |
| archive_scanner       | Git repos in zip archives |
| orphan_detector       | Orphaned commit detection |
| temporal_gap_analyzer | Resurrection intelligence |

---

## Drift Detection

Run `omni introspect` to check for documentation drift:

```bash
omni introspect
```

This compares the scanner README documentation against the actual scanner registry and reports:
- **Undocumented scanners**: Exist in manifest but not in README
- **Missing files**: Referenced in manifest but file not found

---

<p align="center">
  <em>55 instruments. One Eye. Infinite perception.</em><br/>
  <strong>The Sensorium v0.7.0</strong>
</p>
