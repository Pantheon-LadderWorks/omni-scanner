"""
Archive Scanner - General Archive Discovery and Analysis

Contract: C-TOOLS-OMNI-SCANNER-001
Category: Discovery

Scans .zip, .tar.gz, .7z, .rar archives for:
- File inventory (types, counts, sizes)
- Directory structure
- Special folders (.git, node_modules, __pycache__, etc.)
- Compression ratios
- Archive metadata (created date, modified date, size)
- Security concerns (executables, scripts, .env files)

Usage:
    omni scan --scanners=archive .
    omni scan --scanners=archive "Downloads/" --recursive
    omni scan --scanners=archive "D:/Archives/" --pattern="*.zip,*.tar.gz"
"""

import zipfile
import tarfile
import stat
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import Counter

from omni.core.paths import should_skip_path


ARCHIVE_EXTENSIONS = {
    '.zip': 'zipfile',
    '.tar': 'tarfile',
    '.tar.gz': 'tarfile',
    '.tgz': 'tarfile',
    '.tar.bz2': 'tarfile',
    '.tbz2': 'tarfile',
    '.tar.xz': 'tarfile',
    '.txz': 'tarfile',
}

SPECIAL_FOLDERS = {
    '.git': 'version_control',
    '.svn': 'version_control',
    '.hg': 'version_control',
    'node_modules': 'dependency',
    '__pycache__': 'cache',
    '.pytest_cache': 'cache',
    '.mypy_cache': 'cache',
    'venv': 'environment',
    '.venv': 'environment',
    'env': 'environment',
    '.env': 'config',
    '.secrets': 'security',
    'dist': 'build',
    'build': 'build',
    'target': 'build',
    '.next': 'build',
}

SECURITY_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.bat', '.sh', '.ps1', '.py', '.js', 
    '.env', '.pem', '.key', '.crt', '.p12', '.pfx'
}


def _analyze_zip(archive_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a .zip archive."""
    try:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            files = zf.namelist()
            
            metadata = {
                "type": "zip",
                "total_files": len(files),
                "files": files,
                "special_folders": {},
                "file_types": Counter(),
                "security_concerns": [],
                "compressed_size": archive_path.stat().st_size,
                "uncompressed_size": sum(zf.getinfo(f).file_size for f in files),
            }
            
            # Analyze file types
            for file in files:
                ext = Path(file).suffix.lower()
                metadata["file_types"][ext] += 1
                
                # Security check
                if ext in SECURITY_EXTENSIONS:
                    metadata["security_concerns"].append(file)
            
            # Detect special folders
            for file in files:
                parts = Path(file).parts
                for part in parts:
                    if part in SPECIAL_FOLDERS:
                        folder_type = SPECIAL_FOLDERS[part]
                        if folder_type not in metadata["special_folders"]:
                            metadata["special_folders"][folder_type] = []
                        metadata["special_folders"][folder_type].append(part)
            
            # Compression ratio
            if metadata["uncompressed_size"] > 0:
                metadata["compression_ratio"] = metadata["compressed_size"] / metadata["uncompressed_size"]
            
            return metadata
            
    except zipfile.BadZipFile:
        return {"error": "Invalid zip file"}
    except Exception as e:
        return {"error": f"Failed to analyze: {str(e)}"}


def _analyze_tar(archive_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a .tar.gz, .tar.bz2, or .tar.xz archive."""
    try:
        with tarfile.open(archive_path, 'r:*') as tf:
            members = tf.getmembers()
            files = [m.name for m in members if m.isfile()]
            
            metadata = {
                "type": "tar",
                "total_files": len(files),
                "files": files,
                "special_folders": {},
                "file_types": Counter(),
                "security_concerns": [],
                "compressed_size": archive_path.stat().st_size,
                "uncompressed_size": sum(m.size for m in members if m.isfile()),
            }
            
            # Analyze file types
            for file in files:
                ext = Path(file).suffix.lower()
                metadata["file_types"][ext] += 1
                
                # Security check
                if ext in SECURITY_EXTENSIONS:
                    metadata["security_concerns"].append(file)
            
            # Detect special folders
            for file in files:
                parts = Path(file).parts
                for part in parts:
                    if part in SPECIAL_FOLDERS:
                        folder_type = SPECIAL_FOLDERS[part]
                        if folder_type not in metadata["special_folders"]:
                            metadata["special_folders"][folder_type] = []
                        metadata["special_folders"][folder_type].append(part)
            
            # Compression ratio
            if metadata["uncompressed_size"] > 0:
                metadata["compression_ratio"] = metadata["compressed_size"] / metadata["uncompressed_size"]
            
            return metadata
            
    except tarfile.TarError:
        return {"error": "Invalid tar file"}
    except Exception as e:
        return {"error": f"Failed to analyze: {str(e)}"}


def analyze_archive(archive_path: Path) -> Dict[str, Any]:
    """
    Analyze any supported archive format.
    
    Args:
        archive_path: Path to archive file
        
    Returns:
        Dict with archive metadata
    """
    # Determine archive type
    suffixes = ''.join(archive_path.suffixes).lower()
    
    # Try exact match first (.tar.gz)
    archive_type = ARCHIVE_EXTENSIONS.get(suffixes)
    
    # Fallback to single extension (.zip)
    if not archive_type:
        archive_type = ARCHIVE_EXTENSIONS.get(archive_path.suffix.lower())
    
    if not archive_type:
        return {"error": f"Unsupported archive type: {archive_path.suffix}"}
    
    # Analyze based on type
    if archive_type == 'zipfile':
        metadata = _analyze_zip(archive_path)
    elif archive_type == 'tarfile':
        metadata = _analyze_tar(archive_path)
    else:
        return {"error": f"Unknown archive handler: {archive_type}"}
    
    if metadata is None:
        return {"error": "Analysis returned None"}
    
    # Add common metadata
    metadata.update({
        "archive_name": archive_path.name,
        "archive_path": str(archive_path),
        "archive_size_mb": round(archive_path.stat().st_size / (1024 * 1024), 2),
        "modified_date": datetime.fromtimestamp(archive_path.stat().st_mtime).isoformat(),
    })
    
    return metadata


def scan(target: Path, **kwargs) -> Dict[str, Any]:
    """
    Scan for archives and analyze their contents.
    
    Contract: C-TOOLS-OMNI-SCANNER-001 compliant
    
    Args:
        target: Path to scan (directory or single archive file)
        **kwargs: Scanner parameters
            - recursive: bool - Scan subdirectories
            - patterns: str - Comma-separated extensions (default: "*.zip,*.tar.gz")
            - include_hidden: bool - Include hidden archives
    
    Returns:
        Dict with:
            count: Number of archives found
            items: List of archive metadata
            metadata: Scanner info
            summary: Statistics
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "discovery.archive",
            "version": "1.0.0",
            "description": "General archive discovery and analysis",
            "target": str(target),
            "timestamp": datetime.now().isoformat()
        },
        "summary": {
            "total_archives": 0,
            "total_size_mb": 0.0,
            "by_type": Counter(),
            "special_folders_found": Counter(),
            "security_concerns_total": 0,
            "average_compression_ratio": 0.0,
        }
    }
    
    # Determine search patterns
    patterns_str = kwargs.get('patterns', '*.zip,*.tar.gz,*.tgz,*.tar.bz2')
    patterns = [p.strip() for p in patterns_str.split(',')]
    recursive = kwargs.get('recursive', False)
    include_hidden = kwargs.get('include_hidden', False)
    
    # Handle single archive file
    if target.is_file():
        archives = [target]
    else:
        # Search for archives
        archives = []
        for pattern in patterns:
            if recursive:
                found = list(target.rglob(pattern))
            else:
                found = list(target.glob(pattern))
            
            # Filter hidden if needed
            if not include_hidden:
                found = [f for f in found if not f.name.startswith('.')]
            
            archives.extend(found)
    
    # Remove duplicates
    archives = list(set(archives))
    
    # Analyze each archive
    compression_ratios = []
    
    for archive_path in archives:
        if should_skip_path(archive_path):
            continue
        
        metadata = analyze_archive(archive_path)
        
        results["items"].append(metadata)
        results["count"] += 1
        results["summary"]["total_archives"] += 1
        
        # Update statistics
        if "error" not in metadata:
            archive_type = metadata.get("type", "unknown")
            results["summary"]["by_type"][archive_type] += 1
            results["summary"]["total_size_mb"] += metadata.get("archive_size_mb", 0)
            
            # Special folders
            for folder_type, folders in metadata.get("special_folders", {}).items():
                results["summary"]["special_folders_found"][folder_type] += len(set(folders))
            
            # Security concerns
            results["summary"]["security_concerns_total"] += len(metadata.get("security_concerns", []))
            
            # Compression ratio
            if "compression_ratio" in metadata:
                compression_ratios.append(metadata["compression_ratio"])
    
    # Calculate average compression
    if compression_ratios:
        results["summary"]["average_compression_ratio"] = round(
            sum(compression_ratios) / len(compression_ratios), 3
        )
    
    return results
