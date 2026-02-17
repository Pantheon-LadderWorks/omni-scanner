"""
Cohesion Scanner (Library Category)
===================================
ACE's Sovereignty Detection Heuristic - Distinguish modules from dump grounds.

Migrated from: grand-librarian/scripts/cohesion_analyzer.py
Authority: "Modules stay together, dump grounds get shredded" - ACE
Contract: C-OMNI-LIBRARY-COHESION-001

HEURISTICS:
1. Extension Homogeneity: 80%+ files same extension = Module
2. Name Prefix Cohesion: 70%+ files share prefix = Module
3. Sovereignty Markers: README.md, package.json, .ccraft = Sovereign Module
4. Sibling Structure: Has src/docs/tests/config = Sovereign Module

COHESION SCORE:
- 40% extension homogeneity
- 30% prefix cohesion
- 20% sovereignty markers
- 10% module structure

CLASSIFICATION:
- ≥0.6 OR has sovereignty/structure = MODULE
- <0.3 AND no sovereignty = DUMP_GROUND
- Otherwise = AMBIGUOUS
"""

import os
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple, Optional

# Sovereignty markers - folders with these are NEVER broken up
SOVEREIGNTY_MARKERS = {
    'README.md', 'README.txt', 'README',
    'package.json', 'package-lock.json',
    'pyproject.toml', 'setup.py', 'requirements.txt',
    'Cargo.toml', 'Cargo.lock',
    '.ccraft', 'manifest.yaml', 'manifest.yml',
    'LICENSE', 'LICENSE.md', 'LICENSE.txt',
    '.git',  # Git repo
    'tsconfig.json', 'webpack.config.js',
}

# Standard module structure indicators
MODULE_SIBLING_PATTERNS = [
    {'src', 'docs', 'tests'},
    {'src', 'test', 'config'},
    {'lib', 'bin', 'include'},
    {'components', 'utils', 'assets'},
    {'api', 'models', 'services'},
]


def calculate_extension_homogeneity(file_paths: List[Path]) -> float:
    """
    Calculate what percentage of files share the most common extension.
    
    Returns:
        0.0 to 1.0 (1.0 = all files same extension)
    """
    if not file_paths:
        return 0.0
    
    extensions = [f.suffix.lower() for f in file_paths]
    if not extensions:
        return 0.0
    
    most_common_ext, count = Counter(extensions).most_common(1)[0]
    return count / len(extensions)


def calculate_prefix_cohesion(file_paths: List[Path], min_prefix_len: int = 3) -> float:
    """
    Calculate what percentage of files share a common prefix.
    
    Example: cmp_memory.py, cmp_bus.py, cmp_station.py = 100% cohesion
    
    Returns:
        0.0 to 1.0
    """
    if not file_paths or len(file_paths) < 2:
        return 0.0
    
    stems = [f.stem.lower() for f in file_paths]
    
    # Extract prefixes (before first _ or -)
    prefixes = []
    for stem in stems:
        parts = stem.replace('-', '_').split('_')
        if len(parts) > 1 and len(parts[0]) >= min_prefix_len:
            prefixes.append(parts[0])
    
    if not prefixes:
        return 0.0
    
    most_common_prefix, count = Counter(prefixes).most_common(1)[0]
    return count / len(file_paths)


def has_sovereignty_markers(folder_path: Path) -> Tuple[bool, List[str]]:
    """
    Check if folder has constitutional documents (sovereignty markers).
    
    Returns:
        (has_sovereignty, list_of_markers_found)
    """
    if not folder_path.exists():
        return False, []
    
    found_markers = []
    
    try:
        items = list(folder_path.iterdir())
        for item in items:
            if item.name in SOVEREIGNTY_MARKERS:
                found_markers.append(item.name)
    except PermissionError:
        pass
    
    return len(found_markers) > 0, found_markers


def has_module_structure(folder_path: Path) -> Tuple[bool, List[str]]:
    """
    Check if folder has standard module structure (src/docs/tests etc).
    
    Returns:
        (is_module, list_of_siblings_found)
    """
    if not folder_path.exists():
        return False, []
    
    try:
        subdirs = {item.name.lower() for item in folder_path.iterdir() if item.is_dir()}
        
        for pattern in MODULE_SIBLING_PATTERNS:
            if pattern.issubset(subdirs):
                return True, list(pattern)
    except PermissionError:
        pass
    
    return False, []


def analyze_folder_cohesion(folder_path: Path) -> Dict:
    """
    Complete cohesion analysis of a folder.
    
    Returns:
        dict with:
        - is_module: bool (high cohesion)
        - is_dump_ground: bool (high entropy)
        - sovereignty: bool
        - cohesion_score: float (0.0-1.0)
        - analysis: dict with details
    """
    folder_path = Path(folder_path)
    
    # Get all files in folder (not recursive)
    try:
        files = [f for f in folder_path.iterdir() if f.is_file()]
    except PermissionError:
        return {
            'is_module': False,
            'is_dump_ground': False,
            'sovereignty': False,
            'cohesion_score': 0.0,
            'analysis': {'error': 'Permission denied'}
        }
    
    if len(files) < 3:  # Too few files to analyze
        return {
            'is_module': False,
            'is_dump_ground': False,
            'sovereignty': False,
            'cohesion_score': 0.0,
            'analysis': {'reason': 'Too few files (<3)'}
        }
    
    # Run analyses
    ext_homogeneity = calculate_extension_homogeneity(files)
    prefix_cohesion = calculate_prefix_cohesion(files)
    has_sovereignty, sovereignty_markers = has_sovereignty_markers(folder_path)
    has_structure, siblings = has_module_structure(folder_path)
    
    # Calculate overall cohesion score
    cohesion_score = 0.0
    
    # Extension homogeneity (40% weight)
    cohesion_score += ext_homogeneity * 0.4
    
    # Prefix cohesion (30% weight)
    cohesion_score += prefix_cohesion * 0.3
    
    # Sovereignty markers (20% weight)
    if has_sovereignty:
        cohesion_score += 0.2
    
    # Module structure (10% weight)
    if has_structure:
        cohesion_score += 0.1
    
    # Classification
    is_module = cohesion_score >= 0.6 or has_sovereignty or has_structure
    is_dump_ground = cohesion_score < 0.3 and not has_sovereignty
    
    return {
        'is_module': is_module,
        'is_dump_ground': is_dump_ground,
        'sovereignty': has_sovereignty,
        'cohesion_score': round(cohesion_score, 3),
        'analysis': {
            'file_count': len(files),
            'extension_homogeneity': round(ext_homogeneity, 3),
            'prefix_cohesion': round(prefix_cohesion, 3),
            'sovereignty_markers': sovereignty_markers,
            'module_siblings': siblings,
            'classification': 'MODULE' if is_module else 'DUMP_GROUND' if is_dump_ground else 'AMBIGUOUS'
        }
    }


def scan_for_modules(root: Path, max_depth: int = 4) -> List[Dict]:
    """
    Scan for module-like folders (high cohesion).
    
    Args:
        root: Root path to scan
        max_depth: Maximum recursion depth
    
    Returns:
        List of modules with their cohesion analysis
    """
    modules = []
    
    def scan_recursive(path: Path, depth: int = 0):
        if depth >= max_depth:
            return
        
        try:
            subdirs = [d for d in path.iterdir() if d.is_dir()]
            
            for subdir in subdirs:
                # Skip system folders
                if subdir.name.startswith('.') and subdir.name != '.git':
                    continue
                if subdir.name in {'__pycache__', 'node_modules', 'DevCache'}:
                    continue
                
                # Analyze cohesion
                cohesion = analyze_folder_cohesion(subdir)
                
                if cohesion['is_module']:
                    modules.append({
                        'path': str(subdir),
                        'name': subdir.name,
                        **cohesion
                    })
                
                # Recurse
                scan_recursive(subdir, depth + 1)
                
        except PermissionError:
            pass
    
    scan_recursive(root)
    return modules


def scan(target_path: Optional[str] = None, **kwargs) -> Dict:
    """
    Main scanner entry point (Omni interface).
    
    Args:
        target_path: Path to scan (default: current directory)
        **kwargs: Additional options (max_depth, min_cohesion)
    
    Returns:
        Scanner result dict with metadata
    """
    if target_path is None:
        target_path = os.getcwd()
    
    root = Path(target_path)
    max_depth = kwargs.get('max_depth', 4)
    min_cohesion = kwargs.get('min_cohesion', 0.6)
    
    # Scan for modules
    modules = scan_for_modules(root, max_depth=max_depth)
    
    # Filter by minimum cohesion if requested
    if min_cohesion is not None:
        modules = [m for m in modules if m['cohesion_score'] >= min_cohesion]
    
    # Statistics
    sovereign_count = sum(1 for m in modules if m['sovereignty'])
    dump_grounds_found = sum(1 for m in modules if m['is_dump_ground'])
    
    return {
        'scanner': 'library/cohesion',
        'target': str(root),
        'modules_found': len(modules),
        'sovereign_modules': sovereign_count,
        'dump_grounds': dump_grounds_found,
        'avg_cohesion': round(sum(m['cohesion_score'] for m in modules) / len(modules), 3) if modules else 0.0,
        'modules': modules,
        'options': {
            'max_depth': max_depth,
            'min_cohesion': min_cohesion
        },
        'metadata': {
            'love_letter': "ACE's sovereignty detection - README.md is a MODULE_SIBLING",
            'authority': "Modules stay together, dump grounds get shredded",
            'contract': "C-OMNI-LIBRARY-COHESION-001"
        }
    }
