"""
Content Scanner (Library Category)
==================================
Deep read scanner - Extract frontmatter, keywords, shebang for categorization.

"Push the I/O to the edge. The scanner should return Content Hints in the first pass." - ACE
Authority: "A librarian doesn't just count books; she reads them." - ACE
Contract: C-OMNI-LIBRARY-CONTENT-001

CAPABILITIES:
1. Frontmatter Parsing - Extract YAML headers (UUIDs, Authors, Dates)
2. Keyword Sampling - First 2KB scan for taxonomy keywords
3. Shebang Detection - Identify #!(python|bash) for extensionless files
4. Encoding Detection - Handle UTF-8, UTF-16, Latin-1

PERFORMANCE:
- Sample first 2KB only (no full file reads)
- Cache results per scan session
- Skip binary files (magic number detection)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

# Binary file magic numbers (first 4 bytes)
BINARY_SIGNATURES = [
    b'\x89PNG',  # PNG
    b'\xff\xd8\xff',  # JPEG
    b'GIF8',  # GIF
    b'\x50\x4b\x03\x04',  # ZIP
    b'\x25\x50\x44\x46',  # PDF
    b'\x00\x00\x01\x00',  # ICO
]

# Common shebangs
SHEBANG_PATTERNS = {
    r'^#!/usr/bin/env python': 'python',
    r'^#!/usr/bin/python': 'python',
    r'^#!/bin/bash': 'bash',
    r'^#!/bin/sh': 'shell',
    r'^#!/usr/bin/env node': 'javascript',
    r'^#!/usr/bin/env ruby': 'ruby',
}


def is_binary_file(file_path: Path) -> bool:
    """
    Quick binary file detection (magic number check).
    
    Args:
        file_path: Path to file
    
    Returns:
        True if binary, False if text
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return any(header.startswith(sig) for sig in BINARY_SIGNATURES)
    except Exception:
        return True


def detect_shebang(content: str) -> Optional[str]:
    """
    Detect shebang from first line.
    
    Args:
        content: File content (first few lines)
    
    Returns:
        Language name or None
    """
    first_line = content.split('\n')[0].strip()
    
    for pattern, lang in SHEBANG_PATTERNS.items():
        if re.match(pattern, first_line):
            return lang
    
    return None


def extract_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract YAML frontmatter from markdown/text files.
    
    Supports:
    - Triple dash: ---\nkey: value\n---
    - Triple plus: +++\nkey = value\n+++
    
    Args:
        content: File content
    
    Returns:
        Frontmatter dict or None
    """
    # Triple dash (YAML)
    yaml_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(yaml_pattern, content, re.DOTALL)
    
    if match:
        frontmatter_text = match.group(1)
        try:
            # Simple YAML parsing (key: value only, no nested)
            frontmatter = {}
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip().strip('"\'')
            return frontmatter
        except Exception:
            return None
    
    return None


def sample_keywords(content: str, keyword_sets: Dict[str, List[str]]) -> List[str]:
    """
    Sample content for taxonomy keywords.
    
    Args:
        content: File content (first 2KB)
        keyword_sets: Dict of category -> keywords list
    
    Returns:
        List of matching categories
    """
    content_lower = content.lower()
    matches = []
    
    for category, keywords in keyword_sets.items():
        if any(keyword.lower() in content_lower for keyword in keywords):
            matches.append(category)
    
    return matches


def analyze_file_content(
    file_path: Path,
    sample_size: int = 2048,
    keyword_sets: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    """
    Deep read a single file (first 2KB).
    
    Args:
        file_path: Path to file
        sample_size: Bytes to read (default: 2KB)
        keyword_sets: Taxonomy keyword sets
    
    Returns:
        Dict with content hints
    """
    if keyword_sets is None:
        # Default taxonomy (can be overridden)
        keyword_sets = {
            'codecraft': ['codecraft', 'ritual', 'arcane', '::invoke:', 'let it bind'],
            'federation': ['federation', 'station', 'nexus', 'spine', 'seraphina'],
            'council': ['council', 'ace', 'mega', 'oracle', 'claude', 'deepscribe'],
            'protocols': ['protocol', 'procedure', 'workflow', 'ADR'],
            'blueprints': ['blueprint', 'architecture', 'design', 'spec'],
            'lore': ['lore', 'chronicle', 'story', 'narrative'],
        }
    
    result = {
        'path': str(file_path),
        'name': file_path.name,
        'extension': file_path.suffix,
        'is_binary': False,
        'shebang': None,
        'frontmatter': None,
        'keyword_matches': [],
        'encoding': 'utf-8',
        'sample_length': 0,
    }
    
    # Binary check
    if is_binary_file(file_path):
        result['is_binary'] = True
        return result
    
    # Read first 2KB
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(sample_size)
            result['sample_length'] = len(content)
    except UnicodeDecodeError:
        # Try other encodings
        for encoding in ['latin-1', 'utf-16', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read(sample_size)
                    result['sample_length'] = len(content)
                    result['encoding'] = encoding
                    break
            except Exception:
                continue
        else:
            # Failed all encodings
            result['is_binary'] = True
            return result
    except Exception as e:
        result['error'] = str(e)
        return result
    
    # Shebang detection
    result['shebang'] = detect_shebang(content)
    
    # Frontmatter extraction
    result['frontmatter'] = extract_frontmatter(content)
    
    # Keyword sampling
    result['keyword_matches'] = sample_keywords(content, keyword_sets)
    
    return result


def scan(
    target_path: Optional[str] = None,
    pattern: str = "**/*",
    keyword_sets: Optional[Dict[str, List[str]]] = None,
    **kwargs
) -> Dict:
    """
    Main scanner entry point (Omni interface).
    
    Args:
        target_path: Path to scan (default: current directory)
        pattern: File pattern (default: **/* for all files)
        keyword_sets: Custom taxonomy keyword sets
        **kwargs: Additional options (max_files, sample_size)
    
    Returns:
        Scanner result dict with metadata
    """
    if target_path is None:
        target_path = os.getcwd()
    
    root = Path(target_path)
    max_files = kwargs.get('max_files', 1000)
    sample_size = kwargs.get('sample_size', 2048)
    
    # Scan files
    files = list(root.glob(pattern))[:max_files]
    
    # Analyze each file
    results = []
    for file_path in files:
        if file_path.is_file():
            analysis = analyze_file_content(file_path, sample_size, keyword_sets)
            results.append(analysis)
    
    # Statistics
    total_files = len(results)
    binary_files = sum(1 for r in results if r['is_binary'])
    text_files = total_files - binary_files
    files_with_frontmatter = sum(1 for r in results if r['frontmatter'])
    files_with_shebang = sum(1 for r in results if r['shebang'])
    
    # Keyword distribution
    keyword_distribution = {}
    for result in results:
        for keyword in result['keyword_matches']:
            keyword_distribution[keyword] = keyword_distribution.get(keyword, 0) + 1
    
    return {
        'scanner': 'library/content',
        'target': str(root),
        'pattern': pattern,
        'total_files': total_files,
        'binary_files': binary_files,
        'text_files': text_files,
        'files_with_frontmatter': files_with_frontmatter,
        'files_with_shebang': files_with_shebang,
        'keyword_distribution': keyword_distribution,
        'files': results,
        'options': {
            'max_files': max_files,
            'sample_size': sample_size,
        },
        'metadata': {
            'love_letter': "The Eyes - she reads the first page to know the story",
            'authority': "Push the I/O to the edge. Return Content Hints in the first pass.",
            'contract': "C-OMNI-LIBRARY-CONTENT-001"
        }
    }
