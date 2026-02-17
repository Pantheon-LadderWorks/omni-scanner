"""
Census Scanner (Discovery Category)
====================================
File census by dimensional slicing - The Lens (ACE's Level 2 abstraction).

"You don't need SQL's GROUP BY when you can just rotate the view." - ACE
Authority: "The Lens - rotate perspective without changing the data"
Contract: C-OMNI-DISCOVERY-CENSUS-001

CAPABILITIES:
1. Single Dimension - Count files by one property (extension, size, workspace)
2. Cross-Tabulation - Count by two dimensions (extension x workspace)
3. Smart Bucketing - Automatic categorization (sizes, dates)

DIMENSIONS:
- extension: .py, .md, .yaml, .json, etc.
- size_bucket: tiny (<1KB), small (1-100KB), medium (100KB-1MB), large (>1MB), huge (>10MB)
- workspace: Infrastructure, Workspace, Deployment, Projects (detected from path)
- date_bucket: this_week, this_month, this_quarter, this_year, older

USAGE:
    # Single dimension
    omni scan --scanners=census .
    
    # Specific dimension
    result = scan(Path("."), dimension="extension")
    
    # Cross-tabulation (future)
    result = scan(Path("."), dimension="extension,workspace")
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

# Exclusions
EXCLUDED_DIRS = {
    '.git', 'node_modules', '__pycache__', 'venv', '.venv', 
    'dist', 'build', 'bin', 'obj', '.next', '.nuxt',
    'external-frameworks', '.gemini', '.pytest_cache',
    '.gradle', '.idea', 'site-packages'
}

# Size buckets (bytes)
SIZE_BUCKETS = [
    (1024, "tiny"),              # < 1KB
    (100 * 1024, "small"),       # 1KB - 100KB
    (1024 * 1024, "medium"),     # 100KB - 1MB
    (10 * 1024 * 1024, "large"), # 1MB - 10MB
    (float('inf'), "huge")       # > 10MB
]

# Workspace detection patterns
WORKSPACE_PATTERNS = {
    'Infrastructure': ['Infrastructure'],
    'Workspace': ['Workspace'],
    'Deployment': ['Deployment'],
    'Projects': ['Projects']
}

def get_extension(path: Path) -> str:
    """Get file extension (lowercase, with dot)."""
    ext = path.suffix.lower()
    return ext if ext else "(no-extension)"

def get_size_bucket(size: int) -> str:
    """Categorize file size into bucket."""
    for threshold, label in SIZE_BUCKETS:
        if size < threshold:
            return label
    return "huge"

def get_workspace(path: Path) -> str:
    """Detect which workspace a file belongs to."""
    path_str = str(path)
    for workspace, patterns in WORKSPACE_PATTERNS.items():
        if any(pattern in path_str for pattern in patterns):
            return workspace
    return "other"

def get_date_bucket(timestamp: float) -> str:
    """Categorize file age into bucket."""
    now = datetime.now()
    file_dt = datetime.fromtimestamp(timestamp)
    delta = now - file_dt
    
    if delta < timedelta(days=7):
        return "this_week"
    elif delta < timedelta(days=30):
        return "this_month"
    elif delta < timedelta(days=90):
        return "this_quarter"
    elif delta < timedelta(days=365):
        return "this_year"
    else:
        return "older"

def get_dimension_value(path: Path, dimension: str) -> str:
    """Extract dimension value from a file path."""
    if dimension == "extension":
        return get_extension(path)
    elif dimension == "size_bucket":
        return get_size_bucket(path.stat().st_size)
    elif dimension == "workspace":
        return get_workspace(path)
    elif dimension == "date_bucket":
        return get_date_bucket(path.stat().st_mtime)
    else:
        return "unknown"

def scan(target: Path, dimension: str = "extension", max_files: int = 100000) -> Dict:
    """
    Census files by dimensional slicing.
    
    Args:
        target: Root directory to scan
        dimension: Which property to count by (extension, size_bucket, workspace, date_bucket)
        max_files: Safety limit for large codebases
    
    Returns:
        {
            "dimension": str,
            "total_files": int,
            "total_size": int,
            "counts": {category: count},
            "top_10": [(category, count)],
            "files_scanned": int
        }
    """
    target_path = Path(target).resolve()
    root = target_path if target_path.is_dir() else target_path.parent
    
    print(f"📊 Census by {dimension}: {root}")
    
    counts = defaultdict(int)
    total_size = 0
    files_scanned = 0
    
    # Walk filesystem
    for item in root.rglob("*"):
        # Skip excluded directories
        if any(excluded in item.parts for excluded in EXCLUDED_DIRS):
            continue
        
        # Only count files
        if not item.is_file():
            continue
        
        # Safety limit
        if files_scanned >= max_files:
            print(f"⚠️  Hit safety limit ({max_files} files)")
            break
        
        try:
            # Get dimension value
            value = get_dimension_value(item, dimension)
            counts[value] += 1
            
            # Track total size
            total_size += item.stat().st_size
            files_scanned += 1
            
            # Progress indicator (every 1000 files)
            if files_scanned % 1000 == 0:
                print(f"  Scanned {files_scanned} files...", end="\r")
                
        except (OSError, PermissionError) as e:
            # Skip inaccessible files
            continue
    
    # Sort by count (descending)
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    top_10 = sorted_counts[:10]
    
    # Calculate summary stats
    unique_categories = len(counts)
    
    print(f"\n✅ Census complete:")
    print(f"   Dimension: {dimension}")
    print(f"   Files scanned: {files_scanned:,}")
    print(f"   Unique categories: {unique_categories}")
    print(f"   Total size: {total_size / (1024**3):.2f} GB")
    
    # Print top 10
    print(f"\n📋 Top 10 {dimension}:")
    for i, (category, count) in enumerate(top_10, 1):
        percentage = (count / files_scanned * 100) if files_scanned > 0 else 0
        print(f"   {i:2}. {category:20} : {count:6,} files ({percentage:5.1f}%)")
    
    return {
        "dimension": dimension,
        "total_files": files_scanned,
        "total_size": total_size,
        "unique_categories": unique_categories,
        "counts": dict(counts),
        "top_10": top_10,
        "size_gb": round(total_size / (1024**3), 2)
    }

def scan_multi_workspace(dimension: str = "extension") -> Dict:
    """
    Scan all 4 workspaces and aggregate results.
    
    This is the "empire census" - shows composition across all domains.
    """
    workspaces = [
        Path(r"C:\Users\kryst\Infrastructure"),
        Path(r"C:\Users\kryst\Workspace"),
        Path(r"C:\Users\kryst\Deployment"),
        Path(r"C:\Users\kryst\Projects")
    ]
    
    results = {}
    total_files = 0
    total_size = 0
    
    print(f"🌌 EMPIRE CENSUS - Scanning 4 workspaces by {dimension}")
    print("=" * 60)
    
    for workspace_path in workspaces:
        if not workspace_path.exists():
            print(f"⚠️  {workspace_path.name} not found, skipping...")
            continue
        
        result = scan(workspace_path, dimension=dimension)
        results[workspace_path.name] = result
        total_files += result["total_files"]
        total_size += result["total_size"]
        print()
    
    print("=" * 60)
    print(f"🎯 EMPIRE TOTALS:")
    print(f"   Total files: {total_files:,}")
    print(f"   Total size: {total_size / (1024**3):.2f} GB")
    print(f"   Workspaces: {len(results)}")
    
    return {
        "dimension": dimension,
        "workspaces": results,
        "empire_total_files": total_files,
        "empire_total_size": total_size,
        "empire_size_gb": round(total_size / (1024**3), 2)
    }
