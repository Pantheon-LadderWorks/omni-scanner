"""
Library Scanner - The Eyes of the Curator
==========================================
Scans filesystem for documents and builds raw census data.

Pattern: Walk → Discover → Measure → Report
"""
import os
import datetime
import re
import json
from pathlib import Path
from typing import List, Dict

# Exclusions (inherited from MEGA's script)
EXCLUDED_DIRS = {
    '.git', 'node_modules', '__pycache__', 'venv', '.venv', 
    'dist', 'build', 'site-packages', 'bin', 'obj', 'lib', 
    'external-frameworks', '.gemini'
}

def get_date_from_content(path: Path) -> datetime.datetime | None:
    """Try to find a date in the file content."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)  # Read first 2KB
            # Look for "Date: YYYY-MM-DD" or similar patterns
            match = re.search(
                r'(?:Date|Created|Updated|Last Updated):\s*(\d{4}-\d{2}-\d{2})', 
                content, 
                re.IGNORECASE
            )
            if match:
                return datetime.datetime.strptime(match.group(1), '%Y-%m-%d')
    except Exception:
        pass
    return None

def get_file_metadata(path: Path) -> Dict:
    """Extract metadata from a file."""
    stat = path.stat()
    # Use the oldest of mtime or ctime to try and catch original creation
    fs_date = datetime.datetime.fromtimestamp(min(stat.st_mtime, stat.st_ctime))
    
    content_date = get_date_from_content(path)
    final_date = content_date if content_date else fs_date
    
    return {
        "path": str(path),
        "size": stat.st_size,
        "date": final_date.isoformat(),
        "source": "content" if content_date else "filesystem",
        "age_days": (datetime.datetime.now() - final_date).days,
        "stale": (datetime.datetime.now() - final_date).days >= 90
    }

def scan(target: Path, pattern: str = "**/*.md") -> Dict:
    """
    Scan target directory for documents matching pattern.
    
    Args:
        target: Root directory to scan
        pattern: Glob pattern for files to include (default: **/*.md)
    
    Returns:
        Census data with metadata for all discovered files
    """
    print(f"📚 Scanning library: {target}")
    print(f"   Pattern: {pattern}")
    
    files = []
    
    # Use glob for pattern matching (more flexible than os.walk)
    for file_path in target.glob(pattern):
        # Skip excluded directories
        if any(excluded in file_path.parts for excluded in EXCLUDED_DIRS):
            continue
            
        if file_path.is_file():
            try:
                metadata = get_file_metadata(file_path)
                files.append(metadata)
            except Exception as e:
                print(f"⚠️ Error scanning {file_path}: {e}")
    
    # Sort by date (newest first)
    files.sort(key=lambda x: x["date"], reverse=True)
    
    # Calculate statistics
    fresh_files = [f for f in files if f["age_days"] < 90]
    stale_files = [f for f in files if f["age_days"] >= 90]
    
    census = {
        "schema": "omni.census.library.v1",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "target": str(target),
        "pattern": pattern,
        "summary": {
            "total_files": len(files),
            "fresh_count": len(fresh_files),
            "stale_count": len(stale_files),
            "total_bytes": sum(f["size"] for f in files)
        },
        "files": files
    }
    
    print(f"✅ Census complete:")
    print(f"   Total files: {len(files)}")
    print(f"   Fresh (< 90 days): {len(fresh_files)}")
    print(f"   Stale (>= 90 days): {len(stale_files)}")
    
    return census

def scan_copilot_instructions(infrastructure_root: Path) -> Dict:
    """
    Specialized scanner for copilot-instructions.md files.
    
    This is the scanner Oracle uses to regenerate INSTRUCTION_REGISTRY_V1.yaml.
    """
    return scan(infrastructure_root, pattern="**/.github/copilot-instructions.md")
