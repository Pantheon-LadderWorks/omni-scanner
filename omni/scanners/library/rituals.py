"""
Rituals Scanner (Library Category)
==================================
CodeCraft ritual detection and School classification.

"Your taxonomy has high-value categories for CodeCraft and Lore. These are unique to your system." - ACE
Authority: "The Arcane Eye - detect ritual signatures" - ACE
Contract: C-OMNI-LIBRARY-RITUALS-001

CAPABILITIES:
1. Ritual Block Detection - Identify ::RITUAL:: blocks in all CodeCraft file types
2. School Classification - Tag by Arcane School (piggybacking on canon scanner)
3. Cantrip Extraction - Find ::invoke:, ::bind:, ::summon: patterns
4. Multi-Format Support - .ccraft (source), .ritual (compressed), .cclog/.txt (logs)

ARCHITECTURE:
    Lexicon (02_ARCANE_SCHOOLS/*.md) → Canon Scanner → Rituals Scanner
    
    This scanner IMPORTS from canon.py to get authoritative list of 20 arcane schools.
    Schools are dynamically loaded from lexicon YAML front matter, never hardcoded.

SUPPORTED FILE TYPES:
- .ccraft  - Ritual source files (primary)
- .ritual  - Compressed ritual files
- .cclog   - CodeCraft execution logs
- .txt     - Text files with CodeCraft signatures

SUPPORTED PATTERNS:
- Ritual blocks: ::RITUAL:: ... ::END::
- Invocations: ::invoke:, ::bind:, ::summon:
- Schools: Detected from canon (e.g., ::NECROMANCY::, ::CHRONOMANCY::)
- Cantrips: let it bind., May the Source be with You!
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import re
from collections import defaultdict

# Import canon scanner to get authoritative school list
try:
    from omni.scanners.discovery.canon import scan_source_front_matter
    CANON_AVAILABLE = True
except ImportError:
    CANON_AVAILABLE = False

# CodeCraft file extensions
CODECRAFT_EXTENSIONS = {'.ccraft', '.ritual', '.cclog'}

def load_arcane_schools_from_canon() -> Dict[str, List[str]]:
    """
    Load 20 Arcane Schools from canon scanner (YAML front matter).
    
    Returns dynamically generated school patterns from lexicon source.
    Falls back to minimal set if canon unavailable.
    """
    if not CANON_AVAILABLE:
        # Minimal fallback if canon scanner not available
        return {
            'cantrips': ['cantrip', '::get:', '::set:', '::check:', 'let it bind'],
            'invocations': ['::invoke:', '::summon:', '::call:'],
        }
    
    # Scan lexicon YAML front matter
    canon_result = scan_source_front_matter(Path.cwd())
    
    if "error" in canon_result or not canon_result.get("schools"):
        # Fallback if scan failed
        return {
            'cantrips': ['cantrip', '::get:', '::set:', '::check:', 'let it bind'],
            'invocations': ['::invoke:', '::summon:', '::call:'],
        }
    
    # Build school patterns from canon
    schools = {}
    for school in canon_result["schools"]:
        school_name = school["name"].lower()
        school_tokens = school.get("tokens", [])
        
        # Generate pattern list from tokens
        patterns = []
        for token in school_tokens:
            patterns.append(f"::{token}:")
            patterns.append(token.lower())
        
        # Add school name itself
        patterns.append(school_name)
        patterns.append(f"::{school_name.upper()}::")
        
        # Store in dict (use filename-safe key)
        key = school_name.replace(" ", "_").replace("-", "_")
        schools[key] = patterns
    
    return schools

# Load schools dynamically from canon
ARCANE_SCHOOLS = load_arcane_schools_from_canon()

# Ritual patterns
RITUAL_BLOCK_PATTERN = r'::RITUAL::(.*?)(?:::END::|$)'
INVOCATION_PATTERN = r'::(invoke|summon|call|bind|enchant|conjure)::(\w+)'
CANTRIP_PATTERN = r'let it bind\.|May the Source be with You!|::get:|::set:|::check:'

# CodeCraft file signatures (for detecting CodeCraft in non-.ccraft files)
CCRAFT_SIGNATURES = [
    '::RITUAL::',       # Ritual block
    'let it bind.',     # Canonical cantrip
    '# CodeCraft',      # Python comment marker
    '// CodeCraft',     # JS/TS comment
    '/* CodeCraft',     # C-style comment
    '<!-- CodeCraft',   # HTML comment
]


def detect_ritual_blocks(content: str) -> List[Dict[str, str]]:
    """
    Detect ::RITUAL:: blocks in file.
    
    Args:
        content: File content
    
    Returns:
        List of ritual block dicts
    """
    blocks = []
    
    for match in re.finditer(RITUAL_BLOCK_PATTERN, content, re.DOTALL):
        ritual_content = match.group(1).strip()
        
        blocks.append({
            'type': 'ritual_block',
            'content': ritual_content[:200],  # First 200 chars
            'length': len(ritual_content),
        })
    
    return blocks


def detect_invocations(content: str) -> List[Dict[str, str]]:
    """
    Detect invocation patterns (::invoke::, ::summon::, etc.).
    
    Args:
        content: File content
    
    Returns:
        List of invocation dicts
    """
    invocations = []
    
    for match in re.finditer(INVOCATION_PATTERN, content):
        operation = match.group(1)
        target = match.group(2)
        
        invocations.append({
            'type': 'invocation',
            'operation': operation,
            'target': target,
        })
    
    return invocations


def detect_cantrips(content: str) -> List[str]:
    """
    Detect cantrip patterns (::get:, let it bind., etc.).
    
    Args:
        content: File content
    
    Returns:
        List of cantrip names
    """
    cantrips = []
    
    for match in re.finditer(CANTRIP_PATTERN, content):
        cantrip = match.group(0)
        if cantrip not in cantrips:
            cantrips.append(cantrip)
    
    return cantrips


def classify_arcane_school(content: str) -> List[str]:
    """
    Classify file by Arcane School signatures.
    
    Args:
        content: File content
    
    Returns:
        List of matching school names
    """
    content_lower = content.lower()
    schools = []
    
    for school_name, patterns in ARCANE_SCHOOLS.items():
        if any(pattern.lower() in content_lower for pattern in patterns):
            schools.append(school_name)
    
    return schools


def is_codecraft_file(file_path: Path, content: str) -> Tuple[bool, List[str]]:
    """
    Detect if file contains CodeCraft signatures.
    
    Checks for:
    - .ccraft extension (ritual source files)
    - .ritual extension (compressed ritual files)
    - .cclog extension (CodeCraft execution logs)
    - .txt files with CodeCraft signatures
    - Any file with CodeCraft content signatures
    
    Args:
        file_path: Path to file
        content: File content
    
    Returns:
        (is_codecraft, list_of_signatures_found)
    """
    signatures_found = []
    
    # Extension checks for native CodeCraft file types
    if file_path.suffix in CODECRAFT_EXTENSIONS:
        signatures_found.append(f'{file_path.suffix} extension')
    
    # Content signatures (required for .txt files, optional for native types)
    for signature in CCRAFT_SIGNATURES:
        if signature in content:
            signatures_found.append(signature)
    
    # .txt files need at least one content signature
    if file_path.suffix == '.txt':
        # Only consider CodeCraft if has content signatures
        return len([s for s in signatures_found if s != '.txt extension']) > 0, signatures_found
    
    return len(signatures_found) > 0, signatures_found


def analyze_file_rituals(file_path: Path) -> Dict[str, any]:
    """
    Extract ritual data from a single file.
    
    Args:
        file_path: Path to file
    
    Returns:
        Dict with ritual analysis
    """
    result = {
        'path': str(file_path),
        'name': file_path.name,
        'extension': file_path.suffix,
        'is_codecraft': False,
        'codecraft_signatures': [],
        'ritual_blocks': [],
        'invocations': [],
        'cantrips': [],
        'arcane_schools': [],
    }
    
    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        result['error'] = str(e)
        return result
    
    # CodeCraft detection
    is_cc, signatures = is_codecraft_file(file_path, content)
    result['is_codecraft'] = is_cc
    result['codecraft_signatures'] = signatures
    
    if is_cc:
        # Ritual block detection
        result['ritual_blocks'] = detect_ritual_blocks(content)
        
        # Invocation detection
        result['invocations'] = detect_invocations(content)
        
        # Cantrip detection
        result['cantrips'] = detect_cantrips(content)
        
        # School classification
        result['arcane_schools'] = classify_arcane_school(content)
    
    return result


def scan(
    target_path: Optional[str] = None,
    pattern: str = "**/*",
    **kwargs
) -> Dict:
    """
    Main scanner entry point (Omni interface).
    
    Args:
        target_path: Path to scan (default: current directory)
        pattern: File pattern (default: **/* for all files)
        **kwargs: Additional options (max_files)
    
    Returns:
        Scanner result dict with metadata
    """
    if target_path is None:
        target_path = os.getcwd()
    
    root = Path(target_path)
    max_files = kwargs.get('max_files', 1000)
    
    # Scan files
    files = list(root.glob(pattern))[:max_files]
    
    # Analyze each file
    results = []
    codecraft_files = []
    all_schools = []
    
    for file_path in files:
        if file_path.is_file():
            analysis = analyze_file_rituals(file_path)
            results.append(analysis)
            
            if analysis['is_codecraft']:
                codecraft_files.append(analysis)
                all_schools.extend(analysis['arcane_schools'])
    
    # School distribution
    school_distribution = {}
    for school in all_schools:
        school_distribution[school] = school_distribution.get(school, 0) + 1
    
    # Statistics
    total_files = len(results)
    total_codecraft = len(codecraft_files)
    total_ritual_blocks = sum(len(r.get('ritual_blocks', [])) for r in results)
    total_invocations = sum(len(r.get('invocations', [])) for r in results)
    total_cantrips = sum(len(r.get('cantrips', [])) for r in results)
    
    return {
        'scanner': 'library/rituals',
        'target': str(root),
        'pattern': pattern,
        'total_files': total_files,
        'codecraft_files': total_codecraft,
        'ritual_blocks': total_ritual_blocks,
        'invocations': total_invocations,
        'cantrips': total_cantrips,
        'school_distribution': school_distribution,
        'files': results,
        'codecraft_files_detail': codecraft_files,
        'options': {
            'max_files': max_files,
        },
        'metadata': {
            'love_letter': "The Arcane Eye - detect ritual signatures in the code",
            'authority': "High-value categories for CodeCraft auto-sort into languages/ wing",
            'contract': "C-OMNI-LIBRARY-RITUALS-001"
        }
    }
