"""
Cross-reference: compliance x registry + GAP ANALYSIS.

Shows:
1. Per-project compliance (who's clean, mixed, violating)
2. GAP: Registered projects with local_paths that have ZERO heart imports
"""
import json, yaml, subprocess
from pathlib import Path
from collections import defaultdict

infra = Path(r"C:\Users\kryst\Infrastructure")

# ── Load registry ──
with open(infra / "governance/registry/projects/PROJECT_REGISTRY_V1.yaml") as f:
    registry = yaml.safe_load(f)

# Build project path map: rel_path -> project dict
projects_with_paths = []
path_to_project = {}
for proj in registry["projects"]:
    local_paths = proj.get("local_paths", [])
    if not local_paths:
        continue
    for lp in local_paths:
        p = Path(lp)
        try:
            rel = str(p.relative_to(infra)).replace("\\", "/")
        except ValueError:
            rel = str(p).replace("\\", "/")
        path_to_project[rel] = proj["name"]
    projects_with_paths.append({
        "name": proj["name"],
        "github_url": proj.get("github_url"),
        "local_paths": local_paths,
        "classification": proj.get("classification", "unknown"),
    })

# ── Scan for heart imports per project ──
# Use ripgrep to find ALL federation_heart imports across Infrastructure
print("Scanning for federation_heart imports across all projects...")
print()

try:
    result = subprocess.run(
        ["rg", "-l", "--no-ignore", "-g", "*.py", "from federation_heart", str(infra)],
        capture_output=True, encoding="utf-8", errors="replace", timeout=30
    )
    all_heart_files = set()
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            try:
                rel = str(Path(line.strip()).relative_to(infra)).replace("\\", "/")
                all_heart_files.add(rel)
            except ValueError:
                pass
except Exception as e:
    print(f"Warning: ripgrep failed ({e}), falling back to known lists only")
    all_heart_files = set()


def match_project(filepath):
    """Match filepath to project using longest-prefix match."""
    best = None
    best_len = 0
    for proj_path, proj_name in path_to_project.items():
        normed = proj_path.lower()
        if filepath.lower().startswith(normed + "/") or filepath.lower() == normed:
            if len(normed) > best_len:
                best = proj_name
                best_len = len(normed)
    return best


# ── Map heart-importing files to projects ──
projects_with_heart = set()
projects_heart_count = defaultdict(int)

for f in all_heart_files:
    proj = match_project(f)
    if proj:
        projects_with_heart.add(proj)
        projects_heart_count[proj] += 1

# ── SECTION 1: Projects that import Heart ──
print("=" * 75)
print("SECTION 1: PROJECTS WITH HEART IMPORTS (who touches the Heart)")
print("=" * 75)
print(f"{'Project':<42} {'Files':>6}  Classification")
print("-" * 75)

for proj_name in sorted(projects_with_heart):
    proj_data = next((p for p in projects_with_paths if p["name"] == proj_name), None)
    cls = proj_data["classification"] if proj_data else "?"
    count = projects_heart_count[proj_name]
    print(f"  {proj_name:<40} {count:>5}  {cls}")

print(f"\nTotal: {len(projects_with_heart)} projects import federation_heart")

# ── SECTION 2: GAP - Projects that DON'T import Heart at all ──
print()
print("=" * 75)
print("SECTION 2: GAP ANALYSIS - Registered projects with NO Heart imports")
print("=" * 75)
print(f"{'Project':<42} {'Type':<14} GitHub URL")
print("-" * 75)

gap_projects = []
for proj in sorted(projects_with_paths, key=lambda p: p["name"]):
    if proj["name"] not in projects_with_heart:
        # Skip federation_heart itself - it IS the heart
        if "federation_heart" in str(proj.get("local_paths", [])):
            continue
        gap_projects.append(proj)
        gh = proj.get("github_url") or "no-github"
        # Shorten github url
        if gh.startswith("https://github.com/"):
            gh = gh.replace("https://github.com/", "gh:")
        cls = proj["classification"]
        print(f"  {proj['name']:<40} {cls:<14} {gh}")

print(f"\nTotal GAP: {len(gap_projects)} registered projects have ZERO Heart imports")
print(f"Total WITH Heart: {len(projects_with_heart)} projects")
print(f"Total with local_paths: {len(projects_with_paths)} projects")
pct = int(len(projects_with_heart) / len(projects_with_paths) * 100) if projects_with_paths else 0
print(f"\nHeart Integration: {pct}% of linked projects touch the Heart")
