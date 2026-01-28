"""
Omni Librarian - The Curator
=============================
Taxonomy-aware documentation analysis engine.
Transforms raw file census into organized, understood library entries.

Pattern: Read → Classify → Understand → Organize
"""
import hashlib
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# --- Data Models ---

@dataclass
class LibraryEntry:
    """A curated, understood document with taxonomy classification."""
    id: str
    title: str
    path: str
    type: str
    scope: str
    system: str
    status: str
    tags: List[str]
    hash: str
    size_bytes: int
    created_at: Optional[str]
    modified_at: Optional[str]
    template_id: Optional[str] = None
    template_category: Optional[str] = None
    template_confidence: float = 0.0
    canonical: bool = True
    duplicate_of: Optional[str] = None
    duplicates: List[str] = None
    frontmatter: Dict[str, str] = None
    age_days: int = 0
    age_bucket: str = "fresh"

# --- Constants & Regex ---

FRONTMATTER_RE = re.compile(r"^([A-Za-z ]+):\s*(.+)$")
TITLE_RE = re.compile(r"^#\s+(.*)$")

# --- Helpers ---

def read_head(path: Path, max_lines: int = 40) -> List[str]:
    """Read first N lines of a file for metadata extraction."""
    lines = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line.rstrip("\n"))
    except Exception:
        pass
    return lines

def infer_title_and_frontmatter(head: List[str]) -> Tuple[str, Dict[str, str]]:
    """Extract title and frontmatter from document head."""
    title = ""
    front = {}
    for line in head:
        if not title:
            m = TITLE_RE.match(line)
            if m:
                title = m.group(1).strip()
        
        m = FRONTMATTER_RE.match(line)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip()
            front[key] = val
            
    if not title:
        for line in head:
            if line.strip():
                title = line.strip()
                break
    return title or "(untitled)", front

def infer_type_scope_status(front: Dict[str, str], title: str) -> Tuple[str, str, str]:
    """Infer document type, scope, and status from metadata."""
    raw_type = (front.get("Type") or "").lower()
    lower_title = title.lower()
    
    # Type Inference
    if "blueprint" in raw_type or "blueprint" in lower_title:
        t = "blueprint"
    elif "protocol" in raw_type or "protocol" in lower_title:
        t = "protocol"
    elif "ritual" in raw_type or "ritual" in lower_title:
        t = "ritual"
    elif "persona" in raw_type or "identity" in raw_type:
        t = "persona"
    elif "theorem" in raw_type:
        t = "theorem"
    elif "doctrine" in raw_type:
        t = "doctrine"
    elif "chronicle" in raw_type:
        t = "chronicle"
    elif "manifest" in raw_type or "manifest" in lower_title:
        t = "manifest"
    elif "registry" in raw_type or "registry" in lower_title:
        t = "registry"
    else:
        t = "other"

    # Scope Inference
    if "(global" in raw_type:
        scope = "global"
    else:
        scope = "project"

    # Status Inference
    status = "active"
    if "draft" in raw_type or "wip" in raw_type:
        status = "draft"
    if "deprecated" in raw_type or "superseded" in raw_type:
        status = "deprecated"
    
    return t, scope, status

def infer_system(path: Path, tags: List[str]) -> str:
    """Infer which system/domain a document belongs to."""
    p = str(path).lower()
    if "conversation-memory-project" in p or "cmp" in tags:
        return "cmp"
    if "federation_space" in p or "federation" in tags:
        return "federation-space"
    if "codecraft" in p:
        return "codecraft"
    if "quantum-nonary" in p:
        return "quantum-nonary"
    if "seraphina" in p:
        return "seraphina"
    if "refined" in p:
        return "refined"
    if "yard" in p or "americold" in p:
        return "yard-pilot"
    if "dwos" in p:
        return "dwos"
    if "governance" in p:
        return "governance"
    if "orchestration" in p:
        return "orchestration"
    if "memory-substrate" in p:
        return "memory-substrate"
    if "stations" in p:
        return "stations"
    if "agents" in p:
        return "agents"
    if "languages" in p:
        return "languages"
    if "mcp-servers" in p:
        return "mcp-servers"
    return "unknown"

def normalize_tags(front: Dict[str, str]) -> List[str]:
    """Normalize tags from frontmatter."""
    tags = []
    raw = front.get("Tags") or front.get("tags") or ""
    if isinstance(raw, str):
        sep = "," if "," in raw else ";"
        parts = [p.strip() for p in raw.split(sep)] if raw else []
    elif isinstance(raw, list):
        parts = raw
    else:
        parts = []
    
    for t in parts:
        if not t:
            continue
        norm = t.strip().lower().replace(" ", "-")
        tags.append(norm)
    return sorted(set(tags))

def compute_hash(path: Path) -> str:
    """Compute SHA-256 hash of file content."""
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except Exception:
        return ""
    return "sha256:" + h.hexdigest()

def make_slug(title: str, type_: str) -> str:
    """Generate unique slug from title and type."""
    cleaned = re.sub(r"[^\w\s\-]+", "", title)
    cleaned = re.sub(r"\s+", "-", cleaned.strip().lower())
    return f"{type_}.{cleaned}"

def match_template(
    front: Dict[str, str], 
    title: str, 
    tags: List[str], 
    templates: List[Dict], 
    path_str: str = ""
) -> Optional[Dict]:
    """Match document against taxonomy templates."""
    best = None
    best_score = 0.0
    lower_title = title.lower()
    lower_path = path_str.lower()
    filename = Path(path_str).name.lower()
    type_val = (front.get("Type") or "").lower()
    
    for tmpl in templates:
        score = 0.0
        match_rules = tmpl.get("match", {})
        
        # Frontmatter matching
        if "frontmatter" in match_rules:
            for key, expected in match_rules["frontmatter"].items():
                if key == "Type_contains" and expected.lower() in type_val:
                    score += 0.8
                elif key == "template_id_contains":
                    tid = front.get("template_id", "")
                    if expected.lower() in tid.lower():
                        score += 0.9

        # Title matching
        if "title_contains" in match_rules:
            if match_rules["title_contains"].lower() in lower_title:
                score += 0.6

        # Path matching
        if "path_contains" in match_rules:
            if match_rules["path_contains"].lower() in lower_path:
                score += 0.4
                
        # Filename matching
        if "filename_contains" in match_rules:
            if match_rules["filename_contains"].lower() in filename:
                score += 0.5

        if "filename_is" in match_rules:
            if match_rules["filename_is"].lower() == filename:
                score += 1.0

        if score > best_score:
            best_score = score
            best = tmpl
            
    if best and best_score >= 0.5:
        return {
            "id": best["id"], 
            "category": best["category"], 
            "confidence": best_score
        }
    return None

def calculate_age_bucket(age_days: int) -> str:
    """Classify document age into buckets."""
    if age_days <= 30:
        return "fresh"
    if age_days <= 90:
        return "recent"
    if age_days <= 180:
        return "stale_3_6m"
    if age_days <= 365:
        return "stale_6_12m"
    return "ancient"

# --- Main Curation Logic ---

def curate_entries_from_census(
    census_items: List[Dict], 
    templates: List[Dict]
) -> List[LibraryEntry]:
    """
    Transform raw census data into curated library entries.
    
    This is where the magic happens - files become understood documents.
    """
    entries = []
    for item in census_items:
        path = Path(item["path"])
        if not path.exists():
            continue
        
        head = read_head(path)
        title, front = infer_title_and_frontmatter(head)
        type_, scope, status = infer_type_scope_status(front, title)
        tags = normalize_tags(front)
        tmpl_match = match_template(front, title, tags, templates, path_str=str(path))
        system = infer_system(path, tags)
        
        # Get file metadata
        stat = path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime)
        age_days = (datetime.now() - modified_at).days
        
        entry = LibraryEntry(
            id=make_slug(title, type_),
            title=title,
            path=str(path),
            type=type_,
            scope=scope,
            system=system,
            status=status,
            tags=tags,
            hash=compute_hash(path),
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            modified_at=modified_at.isoformat(),
            template_id=tmpl_match["id"] if tmpl_match else None,
            template_category=tmpl_match["category"] if tmpl_match else None,
            template_confidence=tmpl_match["confidence"] if tmpl_match else 0.0,
            canonical=True,
            duplicate_of=None,
            duplicates=[],
            frontmatter=front,
            age_days=age_days,
            age_bucket=calculate_age_bucket(age_days)
        )
        
        if item.get("stale"):
            entry.tags.append("stale>90d")
        
        entries.append(entry)
    return entries

# --- Export to Registry Format ---

def export_to_instruction_registry(entries: List[LibraryEntry]) -> Dict:
    """
    Export library entries to INSTRUCTION_REGISTRY_V1.yaml format.
    
    Pattern: LibraryEntry → InstructionNode
    """
    nodes = []
    
    # Filter for copilot-instructions.md files
    instruction_entries = [
        e for e in entries 
        if "copilot-instructions.md" in e.path.lower()
    ]
    
    for entry in instruction_entries:
        path_obj = Path(entry.path)
        
        # Infer scope from path (directory BEFORE .github folder)
        # Pattern: governance/.github/copilot-instructions.md → scope = "governance/"
        infrastructure_root = Path(r"C:\Users\kryst\Infrastructure")
        
        # Get parent of .github folder
        github_parent = path_obj.parent.parent
        
        if github_parent == infrastructure_root:
            scope = ""  # Root
        else:
            try:
                rel_path = github_parent.relative_to(infrastructure_root)
                scope = str(rel_path).replace("\\", "/")
                # Filter out "." (current directory)
                if scope == ".":
                    scope = ""
            except ValueError:
                scope = str(github_parent)
        
        # Infer priority based on depth
        depth = len(Path(scope).parts) if scope else 0
        if depth == 0:
            priority = 100  # Root
        elif depth == 1:
            priority = 90   # Domain
        elif depth == 2:
            priority = 80   # Subdomain
        else:
            priority = 75   # Leaf
        
        node = {
            "key": f"{entry.system}.{entry.type}" if entry.system != "unknown" else entry.id,
            "path": entry.path.replace("\\", "/"),
            "scope": scope,
            "priority": priority,
            "description": entry.title,
            "authority": entry.template_category or entry.system,
            "status": entry.status
        }
        nodes.append(node)
    
    return {
        "schema": "plw.registry.instruction.v1",
        "version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generated_by": "omni.core.librarian",
        "metadata": {
            "total_instructions": len(nodes),
            "systems": list(set(e.system for e in instruction_entries))
        },
        "nodes": sorted(nodes, key=lambda n: (-n["priority"], n["scope"]))
    }
