# 🔄 Watchdog test: If you see this, auto-reload is working!
"""
Library Scanner - The Eyes of the Curator
==========================================
Scans filesystem for documents and builds raw census data with classification.

"Oracle is finally waking up to the true scale of the Grand Library." - ACE
Authority: "The Eyes of the Curator - Oracle uses this to regenerate INSTRUCTION_REGISTRY_V1.yaml"
Contract: C-OMNI-LIBRARY-LIBRARY-001

CAPABILITIES:
1. Multi-Format Support - .md, .pdf, .docx, .txt, .epub, .mobi
2. Document Classification - Technical docs vs Comics/Art (PDF type detection)
3. Freshness Detection - Age tracking with content date parsing
4. Piggyback Architecture - Uses census.py size buckets for classification

CLASSIFICATION HEURISTICS (ACE's "Comic vs Document" Filter):
- PDF > 10MB + in assets/gallery/comics/ = 🎨 Comic/Art
- PDF < 1MB + in docs/documentation/ = 📄 Technical Document
- DOCX in Literature/ = 📚 Creative Writing
- MD in .github/ = 🏛️ Constitutional Law

Pattern: Walk → Discover → Classify → Measure → Report
"""
import os
import datetime
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

# Exclusions (inherited from MEGA's script)
EXCLUDED_DIRS = {
    '.git', 'node_modules', '__pycache__', 'venv', '.venv', 
    'dist', 'build', 'site-packages', 'bin', 'obj', 'lib', 
    'external-frameworks', '.gemini'
}

# Document types supported (The Grand Library!)
DOCUMENT_EXTENSIONS = {
    '.md', '.pdf', '.docx', '.txt', '.epub', '.mobi',
    '.doc', '.rtf', '.odt',  # Office documents
    '.cbr', '.cbz',  # Comic book archives! 🎨
    '.djvu'  # DjVu ebooks/scans! 📜
}

# Size buckets (from census.py)
SIZE_BUCKETS = [
    (1024, "tiny"),              # < 1KB
    (100 * 1024, "small"),       # 1KB - 100KB
    (1024 * 1024, "medium"),     # 100KB - 1MB
    (10 * 1024 * 1024, "large"), # 1MB - 10MB
    (float('inf'), "huge")       # > 10MB
]

# Path-based classification patterns
CLASSIFICATION_PATTERNS = {
    'comic': ['gallery', 'comics', 'chapter_', 'issues', 'Art'],
    'technical_doc': ['docs', 'documentation', 'blueprints', 'adr', 'knowledge'],
    'creative_writing': ['Literature', 'books', 'drafts', 'novels', 'stories'],
    'constitutional': ['.github', 'copilot-instructions', 'governance', 'constitutional-law'],
    'lore': ['lore', 'narrative', 'chronicles', 'legends'],
    'code_comments': ['README', 'CHANGELOG', 'LICENSE', 'CONTRIBUTING'],
}

def get_size_bucket(size: int) -> str:
    """Categorize file size into bucket (from census.py)."""
    for threshold, label in SIZE_BUCKETS:
        if size < threshold:
            return label
    return "huge"

def classify_document(file_path: Path, size: int, extension: str) -> Tuple[str, str]:
    """
    Classify document by type and category.
    
    Args:
        file_path: Path to document
        size: File size in bytes
        extension: File extension
    
    Returns:
        (document_type, category)
        
    Examples:
        - PDF 50MB in gallery/comics/ → ("pdf", "comic")
        - PDF 500KB in docs/ → ("pdf", "technical_doc")
        - DOCX in Literature/ → ("docx", "creative_writing")
        - MD in .github/ → ("md", "constitutional")
    """
    path_str = str(file_path).lower()
    size_bucket = get_size_bucket(size)
    
    # Determine document type
    doc_type = extension.lstrip('.')
    
    # Classify by path patterns
    category = "general"
    
    for cat, patterns in CLASSIFICATION_PATTERNS.items():
        if any(pattern.lower() in path_str for pattern in patterns):
            category = cat
            break
    
    # PDF-specific heuristics (ACE's "Comic vs Document" filter)
    if extension == '.pdf':
        # Huge PDFs in asset paths = likely comics/art
        if size_bucket in ['large', 'huge'] and category in ['comic', 'creative_writing']:
            category = 'comic'
        # Small/medium PDFs in doc paths = likely technical docs
        elif size_bucket in ['tiny', 'small', 'medium'] and category == 'general':
            # Check if in a documentation-ish location
            if any(doc_hint in path_str for doc_hint in ['doc', 'manual', 'spec', 'blueprint']):
                category = 'technical_doc'
    
    return (doc_type, category)

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
    """Extract metadata from a file with classification."""
    stat = path.stat()
    size = stat.st_size
    extension = path.suffix.lower()
    
    # Use the oldest of mtime or ctime to try and catch original creation
    fs_date = datetime.datetime.fromtimestamp(min(stat.st_mtime, stat.st_ctime))
    
    content_date = get_date_from_content(path)
    final_date = content_date if content_date else fs_date
    
    # Classify document
    doc_type, category = classify_document(path, size, extension)
    size_bucket = get_size_bucket(size)
    
    return {
        "path": str(path),
        "name": path.name,
        "extension": extension,
        "size": size,
        "size_bucket": size_bucket,
        "document_type": doc_type,
        "category": category,
        "date": final_date.isoformat(),
        "source": "content" if content_date else "filesystem",
        "age_days": (datetime.datetime.now() - final_date).days,
        "stale": (datetime.datetime.now() - final_date).days >= 90
    }

def scan(target, pattern: str = "**/*", extensions: set = None) -> Dict:
    """
    Scan target directory for documents matching pattern.
    
    Args:
        target: Root directory to scan (str or Path)
        pattern: Glob pattern for files to include (default: **/* for all files)
        extensions: Set of extensions to filter (default: all DOCUMENT_EXTENSIONS)
    
    Returns:
        Census data with metadata and classification for all discovered documents
    """
    # Convert string to Path if needed (MCP server compatibility)
    if isinstance(target, str):
        target = Path(target)
    
    if extensions is None:
        extensions = DOCUMENT_EXTENSIONS
    
    print(f"📚 Scanning library: {target}")
    print(f"   Pattern: {pattern}")
    print(f"   Extensions: {', '.join(sorted(extensions))}")
    
    files = []
    
    # Use standardized project walker
    from omni.lib.files import walk_project
    
    for file_path in walk_project(target):
        # Filter by extension
        if file_path.suffix.lower() not in extensions:
            continue
            
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
    
    # Category breakdown
    category_counts = {}
    for f in files:
        cat = f.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Document type breakdown
    type_counts = {}
    for f in files:
        dtype = f.get("document_type", "unknown")
        type_counts[dtype] = type_counts.get(dtype, 0) + 1
    
    # Size bucket breakdown
    size_counts = {}
    for f in files:
        bucket = f.get("size_bucket", "unknown")
        size_counts[bucket] = size_counts.get(bucket, 0) + 1
    
    census = {
        "schema": "omni.census.library.v2",  # Upgraded schema with classification
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "target": str(target),
        "pattern": pattern,
        "summary": {
            "total_files": len(files),
            "fresh_count": len(fresh_files),
            "stale_count": len(stale_files),
            "total_bytes": sum(f["size"] for f in files),
            "total_gb": round(sum(f["size"] for f in files) / (1024**3), 2),
            "by_category": category_counts,
            "by_type": type_counts,
            "by_size": size_counts,
        },
        "files": files
    }
    
    print(f"✅ Census complete:")
    print(f"   Total files: {len(files)}")
    print(f"   Fresh (< 90 days): {len(fresh_files)}")
    print(f"   Stale (>= 90 days): {len(stale_files)}")
    print(f"   Total size: {census['summary']['total_gb']} GB")
    print(f"\n📊 By Category:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat:20} : {count:4} files")
    
    return census

def scan_copilot_instructions(infrastructure_root) -> Dict:
    """
    Specialized scanner for copilot-instructions.md files.
    
    This is the scanner Oracle uses to regenerate INSTRUCTION_REGISTRY_V1.yaml.
    Maintains backward compatibility with original library scanner usage.
    
    Args:
        infrastructure_root: Infrastructure root path (str or Path)
    """
    # Convert string to Path if needed
    if isinstance(infrastructure_root, str):
        infrastructure_root = Path(infrastructure_root)
    
    # Only scan .md files in .github directories
    return scan(infrastructure_root, pattern="**/.github/copilot-instructions.md", extensions={'.md'})
