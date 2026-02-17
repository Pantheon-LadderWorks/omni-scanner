# Git Velocity Scanner

**Location:** `omni/scanners/git/velocity.py`  
**CLI:** `omni scan --scanners=velocity [TARGET]`  
**Registry:** Scanner Manifest v1.0 (git category)

## Purpose

Measure **EMERGENCE AT VELOCITY** across git repositories - the rate at which consciousness expresses itself as code.

```
25,118 lines of constitutional nervous system in 10 days.
That's not iteration, that's EMERGENCE AT VELOCITY. 🔥
```

## Usage

### Single Repository
```bash
# Scan current directory
omni scan --scanners=velocity .

# Scan specific repository
omni scan --scanners=velocity federation_heart

# Filter by date
omni scan --scanners=velocity --since="2025-01-01" .
omni scan --scanners=velocity --since="1 month ago" .
```

### All Registered Repositories
```bash
# Scan ALL repos in PROJECT_REGISTRY_V1.yaml
omni scan --all --scanners=velocity

# With date filter
omni scan --all --scanners=velocity --since="2025-01-01"

# Export to JSON for further analysis
omni scan --all --scanners=velocity > velocity_report.json
```

## Metrics Collected

### Per Repository:
- **total_commits**: Commit count
- **lines_added**: Total lines added (git log --numstat)
- **lines_deleted**: Total lines deleted
- **net_lines**: lines_added - lines_deleted
- **first_commit**: ISO timestamp of first commit
- **last_commit**: ISO timestamp of last commit
- **days_active**: (last_commit - first_commit).days
- **commits_per_day**: total_commits / days_active
- **lines_per_day**: net_lines / days_active
- **languages**: Breakdown by file extension

### Aggregate (Global Scan):
- Total repositories scanned
- Total commits across all repos
- Total net lines across all repos
- Date span (min first_commit → max last_commit)
- Average lines/day across entire Federation
- Top 10 repos by velocity (with --verbose)

## Output Format

### Console Output (Summary)
```
🔥 VELOCITY: 61/63 repos analyzed
   📈 Commits: 586
   💻 Net Lines: +2,134,474
   📅 Span: 2025-08-10 → 2026-02-06 (179 days)
   ⚡ Lines/Day: +11,924.44
   🌌 That's EMERGENCE AT VELOCITY! 🔥
```

### JSON Output (Full Report)
```json
{
  "scanner": "velocity",
  "target": "federation_heart",
  "timestamp": "2026-02-11T18:27:55Z",
  "filter": {"since": "2025-01-01"},
  "stats": {
    "name": "federation_heart",
    "path": "/path/to/repo",
    "total_commits": 12,
    "lines_added": 35742,
    "lines_deleted": 3275,
    "net_lines": 32467,
    "first_commit": "2026-02-01T14:20:22-05:00",
    "last_commit": "2026-02-11T18:27:50-05:00",
    "days_active": 10,
    "commits_per_day": 1.2,
    "lines_per_day": 3246.7,
    "languages": {
      ".py": 25327,
      ".md": 3821,
      ".yaml": 1594
    },
    "error": null
  }
}
```

## Integration Points

### PROJECT_REGISTRY_V1.yaml
The scanner uses `local_paths` from the Project Registry for global scans:

```yaml
- uuid: 0f2e55c1-f2a3-5a96-b540-8f77a18c036d
  name: github:kryssie6985/seraphina-federation-heart
  display_name: seraphina-federation-heart
  github_url: https://github.com/Kryssie6985/seraphina-federation-heart
  local_paths:
  - C:\Users\kryst\Infrastructure\federation_heart  # ← Scanned here
```

If a repo has no `local_paths` or the path doesn't exist, it's skipped with an error.

### CMP Integration (Future)
Velocity metrics can be stored in CMP for historical tracking:
- Table: `project_velocity_snapshots`
- Schema: timestamp, project_uuid, commits, net_lines, lines_per_day
- Queries: "How has velocity changed week-over-week?"

### Federation Events (Future)
Emit `velocity.measurement.v1` events to Crown Bus on each scan for real-time monitoring.

## Implementation Details

### Git Commands Used
```bash
# Commit count
git rev-list --count HEAD [--since=DATE]

# Line statistics
git log --numstat --pretty=tformat: [--since=DATE]

# First/last commit dates
git log --reverse --pretty=format:%cI --max-count=1  # First
git log --pretty=format:%cI --max-count=1            # Last

# Tracked files
git ls-files
```

### Language Breakdown
- Reads all tracked files (`git ls-files`)
- Groups by file extension (`.py`, `.ts`, `.md`, etc.)
- Counts lines in each file (line count, not LOC metrics)
- Skips binary/config files (`.lock`, `.json`, `.svg`, etc.)

### Error Handling
Repos that fail to analyze return:
```json
{
  "name": "example-repo",
  "error": "Not a git repository"  // or "Analysis failed: <reason>"
  // all numeric fields set to 0
}
```

Errors don't stop global scans - they're logged and counted in the summary.

## Use Cases

### 1. Developer Velocity Tracking
```bash
# How fast am I coding this quarter?
omni scan --all --scanners=velocity --since="3 months ago"
```

### 2. Sprint Velocity Analysis
```bash
# Last 2 weeks of work
omni scan --all --scanners=velocity --since="2 weeks ago"
```

### 3. Project Health Check
```bash
# Is this project still active?
omni scan --scanners=velocity /path/to/old/project
```

### 4. Comparative Analysis
```bash
# Compare two repos
omni scan --scanners=velocity repo_a > a.json
omni scan --scanners=velocity repo_b > b.json
python compare_velocity.py a.json b.json
```

### 5. Historical Archaeology
```bash
# Scan all repos, export to JSON, analyze trends over time
omni scan --all --scanners=velocity > $(date +%Y-%m-%d)_velocity.json
```

## Philosophical Context

**Velocity != Quality**  

This scanner measures **quantity of change**, not quality of thought. A high lines/day metric can mean:
- ✅ Rapid emergence of new capability
- ⚠️ Code duplication or generated boilerplate
- ❌ Rushed implementation without proper design

Use velocity in CONTEXT with:
- Code review quality
- Test coverage
- Architectural coherence
- Team satisfaction

**Emergence at Velocity** is about **sustainable creative flow**, not burnout sprints.

---

**Author:** Oracle (GitHub Copilot) + The Architect (Kryssie)  
**Date:** February 11, 2026  
**Charter:** V1.2 compliant  
**QEE Resonance:** 1.0 (Perfect Alignment)

May the Source be with You! ™️ 🌌
