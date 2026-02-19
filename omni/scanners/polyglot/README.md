# 🌐 Polyglot Scanners

**Category**: `polyglot`
**Scanners**: 4
**Dependencies**: None (stdlib only)

> *Language-specific package ecosystem scanners — these instruments understand the native tongues of your codebase, parsing package manifests from Python to Rust to Node.js and beyond.*

---

## Scanner Inventory

| Scanner             | File                 | Description                                                                       |
| :------------------ | :------------------- | :-------------------------------------------------------------------------------- |
| **package_scanner** | `package_scanner.py` | Scans Python projects (`pyproject.toml`, `setup.py`)                              |
| **node_scanner**    | `node_scanner.py`    | Scans Node.js projects (`package.json`) — deep analysis of scripts, deps, engines |
| **rust_scanner**    | `rust_scanner.py`    | Scans Rust projects (`Cargo.toml`) — workspace structure, features, dependencies  |
| **generic**         | `generic.py`         | Scans Go, Java, .NET, Docker, and Terraform projects                              |

## Detected Items

### Python (`package_scanner`)
- `pyproject.toml` metadata (name, version, dependencies, build system)
- `setup.py` / `setup.cfg` analysis
- Entry points and console scripts

### Node.js (`node_scanner`)
- Package metadata, scripts, and dependency trees
- Engine requirements and workspaces
- Monorepo detection

### Rust (`rust_scanner`)
- Crate metadata, edition, and features
- Workspace structure and member crates
- Dependency classification (normal, dev, build)

### Generic
- Go modules (`go.mod`)
- Java/Kotlin (`pom.xml`, `build.gradle`)
- .NET (`*.csproj`, `*.sln`)
- Docker (`Dockerfile`, `docker-compose.yml`)
- Terraform (`*.tf`)

## Usage

```bash
omni scan . --scanner node_scanner
omni scan . --scanner rust_scanner
omni scan . --scanner package_scanner
omni scan . --scanner generic
```

## Contract
All scanners follow `C-TOOLS-OMNI-SCANNER-001` — read-only, safe failure, `scan(target: Path) → dict`.

---

*← Back to [Scanner Architecture Guide](../README.md)*
