"""
Phoenix Archive Scanner - Git Repository Discovery in Archives

Contract: C-TOOLS-OMNI-SCANNER-001
Category: Phoenix (Git Resurrection)

PIGGYBACKS on: omni.scanners.discovery.archive_scanner (general archive analysis)
ADDS: Git-specific repository metadata extraction

Scans archives for .git repositories and extracts resurrection metadata:
- Repository name (from .git/config remote.origin.url)
- Commit count estimates
- Branch information
- Last commit date
- Remote URL

Usage:
    omni scan --scanners=archive Downloads/  # General archive analysis
    omni scan phoenix --scanners=git-archive Downloads/  # Git-specific resurrection data
"""

import zipfile
import configparser
import io
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from omni.core.paths import get_infrastructure_root

# Piggyback on general archive scanner
try:
    from omni.scanners.discovery.archive_scanner import analyze_archive as general_analyze_archive
    HAS_GENERAL_SCANNER = True
except ImportError:
    HAS_GENERAL_SCANNER = False


def _extract_git_config(zip_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract .git/config from a zip file.
    
    Args:
        zip_path: Path to .zip file
        
    Returns:
        Dict with repo metadata or None if not a git archive
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()
            
            # Find .git/config
            config_files = [f for f in files if f.endswith('.git/config') or f.endswith('.git\\config')]
            
            if not config_files:
                return None
            
            # Read config
            config_content = zf.read(config_files[0]).decode('utf-8', errors='replace')
            
            # Parse git config
            config = configparser.ConfigParser()
            try:
                config.read_string(config_content)
            except Exception as e:
                # VS Code vscode-merge-base duplication errors
                return {
                    "error": f"Config parse error: {str(e)}",
                    "config_file": config_files[0]
                }
            
            # Extract metadata
            metadata = {
                "has_git": True,
                "config_file": config_files[0],
                "branches": [],
                "tags": [],
                "remotes": {}
            }
            
            # Get remote URL
            if config.has_section('remote "origin"'):
                try:
                    metadata["remote_url"] = config.get('remote "origin"', 'url')
                    
                    # Extract repo name from URL
                    url = metadata["remote_url"]
                    match = re.search(r'/([^/]+?)(\.git)?$', url)
                    if match:
                        metadata["repo_name"] = match.group(1)
                except:
                    pass
            
            # Get HEAD
            head_files = [f for f in files if f.endswith('.git/HEAD') or f.endswith('.git\\HEAD')]
            if head_files:
                head_content = zf.read(head_files[0]).decode('utf-8', errors='replace').strip()
                if head_content.startswith('ref:'):
                    metadata["head_branch"] = head_content.split('/')[-1]
            
            # Count branches (refs/heads/)
            branch_files = [f for f in files if 'refs/heads/' in f or 'refs\\heads\\' in f]
            metadata["branch_count"] = len(branch_files)
            if branch_files:
                metadata["branches"] = [f.split('/')[-1] for f in branch_files]
            
            # Count tags (refs/tags/)
            tag_files = [f for f in files if 'refs/tags/' in f or 'refs\\tags\\' in f]
            metadata["tag_count"] = len(tag_files)
            
            # Estimate commits (rough: count objects/pack files)
            pack_files = [f for f in files if '.git/objects/pack/' in f and f.endswith('.pack')]
            if pack_files:
                # Rough estimate: pack file count × 50 commits per pack
                metadata["estimated_commits"] = len(pack_files) * 50
            else:
                # Count loose objects
                object_files = [f for f in files if '.git/objects/' in f and len(Path(f).name) == 2]
                metadata["estimated_commits"] = len(object_files)
            
            return metadata
            
    except zipfile.BadZipFile:
        return None
    except Exception as e:
        return {"error": f"Extraction failed: {str(e)}"}


def scan(target: Path, **kwargs) -> Dict[str, Any]:
    """
    Scan directory for .zip archives containing git repositories.
    
    Contract: C-TOOLS-OMNI-SCANNER-001 compliant
    
    Args:
        target: Path to scan (directory or .zip file)
        **kwargs: Optional scanner parameters
            - recursive: bool - Scan subdirectories
            - pattern: str - Glob pattern for archives (default: "*.zip")
    
    Returns:
        Dict with:
            count: Number of git archives found
            items: List of archive metadata
            metadata: Scanner info
            summary: Statistics
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "phoenix.archive",
            "version": "1.0.0",
            "description": "Git archive discovery and metadata extraction (PIGGYBACKS on discovery.archive_scanner)",
            "target": str(target),
            "timestamp": datetime.now().isoformat(),
            "piggybacks_on": "discovery.archive_scanner" if HAS_GENERAL_SCANNER else None,
            "method": "piggyback" if HAS_GENERAL_SCANNER else "manual_fallback"
        },
        "summary": {
            "total_archives_scanned": 0,
            "git_archives_found": 0,
            "parse_errors": 0,
            "not_git_archives": 0
        }
    }
    
    # PIGGYBACK PATTERN: Use general scanner for .git detection if available
    if HAS_GENERAL_SCANNER:
        try:
            general_result = general_analyze_archive(target, **kwargs)
            
            # Filter for archives containing .git folders
            for archive_info in general_result.get('items', []):
                results["summary"]["total_archives_scanned"] += 1
                
                special_folders = archive_info.get('metadata', {}).get('special_folders', {})
                if special_folders.get('.git', {}).get('present', False):
                    # Found .git! Extract git-specific metadata
                    archive_path = Path(archive_info['path'])
                    git_metadata = _extract_git_config(archive_path)
                    
                    if git_metadata:
                        git_metadata['archive_path'] = str(archive_path)
                        git_metadata['archive_size'] = archive_info.get('size_bytes', 0)
                        git_metadata['discovered_by'] = 'general_scanner_piggyback'
                        results["items"].append(git_metadata)
                        results["summary"]["git_archives_found"] += 1
                    else:
                        results["summary"]["parse_errors"] += 1
                else:
                    results["summary"]["not_git_archives"] += 1
            
            results["count"] = len(results["items"])
            return results
            
        except Exception as e:
            # Fallback to manual scan if general scanner fails
            results["metadata"]["piggyback_error"] = str(e)
            # Continue to manual fallback below
    
    # MANUAL FALLBACK: Original implementation (when general scanner unavailable)
    
    # Handle single .zip file
    if target.is_file() and target.suffix == '.zip':
        archives = [target]
    else:
        # Scan directory for .zip files
        pattern = kwargs.get('pattern', '*.zip')
        recursive = kwargs.get('recursive', False)
        
        if recursive:
            archives = list(target.rglob(pattern))
        else:
            archives = list(target.glob(pattern))
    
    # Scan each archive
    for archive_path in archives:
        results["summary"]["total_archives_scanned"] += 1
        
        metadata = _extract_git_config(archive_path)
        
        if metadata is None:
            # Not a git archive
            results["summary"]["not_git_archives"] += 1
            continue
        
        if "error" in metadata:
            # Parse error
            results["summary"]["parse_errors"] += 1
            
        archive_info = {
            "zip_file": archive_path.name,
            "zip_path": str(archive_path),
            "size_bytes": archive_path.stat().st_size,
            "modified_date": datetime.fromtimestamp(archive_path.stat().st_mtime).isoformat(),
            **metadata
        }
        
        results["items"].append(archive_info)
        results["summary"]["git_archives_found"] += 1
        results["count"] += 1
    
    return results
