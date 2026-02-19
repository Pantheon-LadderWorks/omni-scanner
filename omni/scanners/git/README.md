# 🔀 Git Scanners

**Category**: `git`
**Scanners**: 5
**Dependencies**: `git` CLI (must be in PATH)

> *Repository intelligence scanners — these instruments reach into git's memory to extract velocity metrics, commit archaeology, PR telemetry, and the deep history of your codebase.*

---

## Scanner Inventory

| Scanner            | File                | Description                                                                                 |
| :----------------- | :------------------ | :------------------------------------------------------------------------------------------ |
| **git**            | `git.py`            | Git status and repository scanner — branch, remotes, uncommitted changes                    |
| **velocity**       | `velocity.py`       | Git velocity measurement — EMERGENCE AT VELOCITY metrics (commits/day, active contributors) |
| **commit_history** | `commit_history.py` | Complete commit history — phoenix resurrection evidence                                     |
| **pr_telemetry**   | `pr_telemetry.py`   | PR Telemetry Scanner (The Telepath) — health and drift detection                            |
| **git_util**       | `git_util.py`       | Git utility functions shared across git scanners                                            |

## Key Concepts

### Velocity Metrics
The `velocity` scanner measures development momentum:
- Commits per time period
- Active contributor count
- File churn rate

### PR Telemetry (The Telepath)
The `pr_telemetry` scanner analyzes pull request patterns for health signals:
- PR frequency and merge rate
- Review turnaround time
- Drift detection between branches

### Commit History Archaeology
The `commit_history` scanner provides full commit history analysis, useful for:
- Phoenix resurrection (recovering lost work from git history)
- Author contribution mapping
- Activity timeline reconstruction

## Usage

```bash
omni scan . --scanner git
omni scan . --scanner velocity
omni scan . --scanner commit_history
omni scan . --scanner pr_telemetry
```

Also see: [Velocity Scanner Deep Dive](VELOCITY_README.md)

## Contract
All scanners follow `C-TOOLS-OMNI-SCANNER-001` — read-only, safe failure, `scan(target: Path) → dict`.

---

*← Back to [Scanner Architecture Guide](../README.md)*
