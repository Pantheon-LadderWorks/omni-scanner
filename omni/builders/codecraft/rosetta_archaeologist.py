#!/usr/bin/env python3
"""
Rosetta Archaeologist v2 — MEGA + A.C.E.'s Constitutional Excavator

Walks the ENTIRE lexicon to extract THE LAW (not summaries).

Architecture:
  1. Load schools.canonical.yaml as INDEX/MAP (navigation aid)
  2. Walk lexicon/** and spec/** to extract REAL SPECS (operations, constraints, examples)
  3. Load grammar from lexicon.ebnf + mapping from EBNF_TO_PARSER_MAPPING.md
  4. Load commentomancy from LAW_AND_LORE_PROTOCOL.md + lexicon/commentomancy/*.md
  5. Build canon.lock.yaml with FULL PROVENANCE (file hashes, git head)
  6. Optionally render CODECRAFT_ROSETTA_STONE.md from template

Key Principles:
- Schools.canonical.yaml is MAP (ids, tokens → schools)
- Lexicon markdown files are LAW (operations, constraints, safety_tier)
- Front-matter YAML in school files = first-class machine metadata
- Drift detection: 21 tokens → 19 schools, all files present
- Provenance: sha256 + mtime for every source file

Usage:
  python scripts/rosetta_archaeologist.py --root . --out canon.lock.yaml
  python scripts/rosetta_archaeologist.py --root . --out canon.lock.yaml --render_rosetta
"""
from __future__ import annotations
import argparse
import hashlib
import os
import re
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# ---------- Tiny Markdown Helpers (Stable & Deterministic) ----------
H1 = re.compile(r'^\s*#\s+(?P<text>.+?)\s*$')
H2 = re.compile(r'^\s*##\s+(?P<text>.+?)\s*$')
FENCE = re.compile(r'^\s*```(?P<lang>[a-zA-Z0-9_-]*)\s*$')
LIST = re.compile(r'^\s*[-*]\s+(?P<text>.+?)\s*$')
FRONT_MATTER = re.compile(r'^\s*---\s*\n(?P<y>.*?\n)---\s*\n', re.DOTALL)

# ---------- Commentomancy Extractors (Lore Channel) ----------
COMMENTOMANCY_PATTERNS = {
    "strategic_decision": re.compile(r'🎯\s*//->(.+?)$', re.MULTILINE),
    "emergent_pattern": re.compile(r'🌟\s*//\*(.+?)$', re.MULTILINE),
    "heart_imprint": re.compile(r'💖\s*//<3(.+?)$', re.MULTILINE),
    "evolution_pressure": re.compile(r'⚡\s*//\+(.+?)$', re.MULTILINE),
    "sacred_truth": re.compile(r'📜\s*///(.+?)$', re.MULTILINE),
    "guardrail": re.compile(r'🛡️\s*//\!\?(.+?)$', re.MULTILINE),
}

# Section normalization (map messy human headings → canonical keys)
SECTION_ALIASES = {
    "purpose": ["purpose", "intent", "why", "philosophy"],
    "operations": ["operations", "invocations", "capabilities", "when to use"],
    "constraints": ["constraints", "guardrails", "requirements", "prereqs", "prerequisites", "when to use"],
    "examples": ["examples", "samples", "spells", "real ritual examples", "common patterns", "advanced patterns"],
}

def norm_h2(title: str) -> Optional[str]:
    """Normalize H2 heading to canonical section key."""
    t = title.strip().lower()
    for key, aliases in SECTION_ALIASES.items():
        if any(a in t for a in aliases):
            return key
    return None

def parse_sections(md: str) -> Dict[str, List[str]]:
    """Extract H2 sections → {canonical_key: [lines]}."""
    lines = md.splitlines()
    cur = None
    out: Dict[str, List[str]] = {}
    for ln in lines:
        m = H2.match(ln)
        if m:
            k = norm_h2(m.group('text')) or m.group('text').strip()
            cur = k
            out.setdefault(cur, [])
        elif cur is not None:
            out[cur].append(ln)
    return out

def extract_list(lines: List[str], prefix_filter: Optional[str] = None) -> List[str]:
    """
    Extract bullet list items, dedupe preserving order.
    If prefix_filter is provided, only extract items starting with that prefix (e.g., '✅', '❌').
    """
    got = []
    for ln in lines:
        m = LIST.match(ln)
        if m:
            text = m.group('text').strip()
            if prefix_filter:
                if text.startswith(prefix_filter):
                    # Remove the prefix (✅ or ❌) and clean up
                    text = text[len(prefix_filter):].strip()
                    got.append(text)
            else:
                got.append(text)
    return list(dict.fromkeys(got))

def extract_fences(lines: List[str], langs=("codecraft", "ccraft")) -> List[str]:
    """Extract fenced code blocks of specified languages."""
    out = []
    inb = False
    lang = ""
    buf = []
    for ln in lines:
        m = FENCE.match(ln)
        if m:
            if not inb:
                inb = True
                lang = (m.group('lang') or "").lower()
                buf = []
            else:
                if lang in langs:
                    out.append("\n".join(buf).strip())
                inb = False
                lang = ""
                buf = []
        elif inb:
            buf.append(ln)
    return out

def sha256_path(p: Path) -> str:
    """Compute sha256 hash of file."""
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def git_head(root: Path) -> Optional[str]:
    """Get current git HEAD sha, None if not in git repo."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return None

# ---------- Loaders ----------
def load_yaml(path: Path) -> Any:
    """Load YAML file."""
    with path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def read_text(path: Path) -> str:
    """Read text file with UTF-8."""
    return path.read_text(encoding='utf-8', errors='ignore')

# ---------- Domain Extraction ----------
def parse_front_matter(md: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract front-matter YAML from markdown.
    Returns: (front_matter_dict, remaining_body)
    """
    m = FRONT_MATTER.match(md)
    if not m:
        return {}, md
    y = yaml.safe_load(m.group('y')) or {}
    rest = md[m.end():]
    return y, rest

def extract_commentomancy_lore(prose: str) -> Dict[str, List[str]]:
    """
    Extract Lore from prose commentomancy sigils.
    Returns: {
        "strategic_decisions": [...],
        "emergent_patterns": [...],
        "heart_imprints": [...],
        "evolution_pressure": [...],
        "sacred_truths": [...],
        "guardrails": [...]
    }
    """
    lore = {
        "strategic_decisions": [],
        "emergent_patterns": [],
        "heart_imprints": [],
        "evolution_pressure": [],
        "sacred_truths": [],
        "guardrails": []
    }
    
    # Extract each commentomancy type
    for match in COMMENTOMANCY_PATTERNS["strategic_decision"].finditer(prose):
        lore["strategic_decisions"].append(match.group(1).strip())
    
    for match in COMMENTOMANCY_PATTERNS["emergent_pattern"].finditer(prose):
        lore["emergent_patterns"].append(match.group(1).strip())
    
    for match in COMMENTOMANCY_PATTERNS["heart_imprint"].finditer(prose):
        lore["heart_imprints"].append(match.group(1).strip())
    
    for match in COMMENTOMANCY_PATTERNS["evolution_pressure"].finditer(prose):
        lore["evolution_pressure"].append(match.group(1).strip())
    
    for match in COMMENTOMANCY_PATTERNS["sacred_truth"].finditer(prose):
        lore["sacred_truths"].append(match.group(1).strip())
    
    for match in COMMENTOMANCY_PATTERNS["guardrail"].finditer(prose):
        lore["guardrails"].append(match.group(1).strip())
    
    # Dedupe preserving order
    for key in lore:
        lore[key] = list(dict.fromkeys(lore[key]))
    
    return lore

def detect_ops_cons_examples(sections: Dict[str, List[str]]) -> Tuple[List[str], List[str], List[str]]:
    """Extract operations, constraints, examples from normalized sections."""
    # Extract ✅ operations from "operations" sections (including "When to Use")
    ops = extract_list(sections.get("operations", []), prefix_filter="✅")
    # If no emoji-prefixed items found, try without filter
    if not ops:
        ops = extract_list(sections.get("operations", []))
    
    # Extract ❌ constraints from "constraints" sections (including "When to Use")
    cons = extract_list(sections.get("constraints", []), prefix_filter="❌")
    # If no emoji-prefixed items found, try without filter
    if not cons:
        cons = extract_list(sections.get("constraints", []))
    
    # Extract fenced code blocks from ALL sections
    exs = extract_fences(sum([v for v in sections.values()], []))
    return ops, cons, exs

def extract_ebnf_fragments(ebnf_text: str) -> Dict[str, str]:
    """Split EBNF into stable fragments (split by 2+ newlines)."""
    chunks = [c.strip() + "\n" for c in re.split(r'\n{2,}', ebnf_text) if c.strip()]
    return {f"fragment_{i}": chunks[i] for i in range(len(chunks))}

def extract_grammar_map(mapping_md: str) -> Dict[str, str]:
    """
    Parse EBNF_TO_PARSER_MAPPING.md table.
    Format: | rule | ParserFunc |
    """
    out: Dict[str, str] = {}
    for ln in mapping_md.splitlines():
        if ln.strip().startswith("|") and ln.strip().endswith("|") and ln.count("|") >= 3:
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if len(cells) >= 2 and cells[0].lower() != "rule":
                out[cells[0]] = cells[1]
    return out

def extract_commentomancy_schema(law_md: str, extra: List[Path]) -> Dict[str, Any]:
    """
    Extract commentomancy schema from LAW_AND_LORE_PROTOCOL.md + channel files.
    Returns canonical sigils + policy + observed examples.
    """
    schema = {
        "sigils": {
            "guardrail": "//!?",
            "prereq": "//!",
            "heart": "//<3",
            "law": "///",
            "lore": "//~",
        },
        "policy": {
            "safety_tier_requirements": {
                "0": [],
                "1": [],
                "2": ["guardrail"],
                "3": ["guardrail", "prereq"]
            }
        },
        "observed_lines": []
    }
    
    def scan(md: str):
        for ln in md.splitlines():
            if any(s in ln for s in schema["sigils"].values()):
                schema["observed_lines"].append(ln.strip())
    
    scan(law_md)
    for p in extra:
        if p.suffix.lower() == ".md":
            scan(read_text(p))
    
    # Dedupe preserving order
    schema["observed_lines"] = list(dict.fromkeys(schema["observed_lines"]))
    return schema

# ---------- Build Canon ----------
def build_canon(root: Path, args) -> Dict[str, Any]:
    """
    Walk lexicon and build canon.lock.yaml with full provenance.
    """
    schools_map = load_yaml(root / args.schools)
    schools_dir = root / args.schools_dir
    ebnf_text = read_text(root / args.ebnf)
    mapping_md = read_text(root / args.grammar_map)
    law_md = read_text(root / args.law)
    comment_dir = root / args.commentomancy
    
    # Provenance (track every source file)
    prov = {
        "generated_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "git_head": git_head(root),
        "sources": {}
    }
    
    def track(p: Path):
        """Track file hash + mtime for provenance."""
        rel_path = str(p).replace(str(root) + os.sep, "").replace("\\", "/")
        prov["sources"][rel_path] = {
            "sha256": sha256_path(p),
            "mtime": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(p.stat().st_mtime))
        }
    
    # Manifest baseline
    manifest = {
        "total_schools": int(schools_map["metadata"]["total_schools"]),
        "token_count": int(schools_map["metadata"]["total_grammar_tokens"]),
        "token_to_school_mapping": schools_map.get("token_to_school_mapping", {}),
        "constitutional_authority": [
            "Charter V1.1",
            "Crown Accord v1.2a",
            "Law & Lore Protocol"
        ],
    }
    
    # Build schools (walk each markdown file)
    schools: Dict[str, Any] = {}
    for sid, spec in schools_map.get("schools", {}).items():
        file_rel = spec.get("file")
        md_path = schools_dir / file_rel if file_rel else None
        
        entry = {
            "id": int(sid) if str(sid).isdigit() else sid,
            "name": spec.get("name"),
            "emoji": spec.get("emoji", ""),
            "category": spec.get("category"),
            "purpose": spec.get("purpose"),
            "aliases": [],
            "operations": [],
            "constraints": [],
            "examples": [],
            "law": {},  # Structured Law from front-matter
            "lore": {},  # Structured Lore from front-matter + commentomancy
            "spec": {}  # Legacy field for backwards compat
        }
        
        if md_path and md_path.exists():
            track(md_path)
            full = read_text(md_path)
            fm, body = parse_front_matter(full)
            sections = parse_sections(body)
            ops, cons, exs = detect_ops_cons_examples(sections)
            
            # Legacy fields (for backwards compatibility)
            entry["operations"] = ops
            entry["constraints"] = cons
            entry["examples"] = exs
            
            # Extract Law from front-matter YAML
            if fm.get("law"):
                entry["law"] = fm["law"]
                # Also copy to legacy "spec" for backwards compat
                entry["spec"]["law"] = fm["law"]
            
            # Extract Lore from front-matter YAML + prose commentomancy
            lore_combined = {}
            
            # Front-matter Lore (structured)
            if fm.get("lore"):
                lore_combined = fm["lore"].copy()
            
            # Prose commentomancy Lore (append to structured)
            prose_lore = extract_commentomancy_lore(body)
            for key, values in prose_lore.items():
                if values:  # Only include non-empty lists
                    if key in lore_combined:
                        # Merge: front-matter (dicts/lists) + prose (strings)
                        existing = lore_combined[key]
                        if isinstance(existing, list):
                            # Append prose strings to list (can't dedupe dicts, only strings)
                            lore_combined[key] = existing + values
                        elif isinstance(existing, dict):
                            # Keep structured dict from front-matter, add prose as separate key
                            if "prose_annotations" not in lore_combined:
                                lore_combined["prose_annotations"] = {}
                            lore_combined["prose_annotations"][key] = values
                        else:
                            lore_combined[key] = values
                    else:
                        lore_combined[key] = values
            
            if lore_combined:
                entry["lore"] = lore_combined
                # Also copy to legacy "spec" for backwards compat
                entry["spec"]["lore"] = lore_combined
            
            # Front-matter wins for other metadata (safety_tier, tokens, etc.)
            if fm:
                entry["spec"].update(fm)
                if fm.get("aliases"):
                    entry["aliases"] = list(dict.fromkeys(fm["aliases"]))
        else:
            entry["warnings"] = ["missing_markdown_file"]
        
        schools[str(sid)] = entry
    
    # Grammar + Commentomancy
    grammar = extract_ebnf_fragments(ebnf_text)
    grammar_map = extract_grammar_map(mapping_md)
    track(root / args.ebnf)
    track(root / args.grammar_map)
    
    comment_files = sorted(comment_dir.glob("*.md")) if comment_dir.exists() else []
    for p in comment_files:
        track(p)
    
    commentomancy = extract_commentomancy_schema(law_md, comment_files)
    track(root / args.law)
    
    # Assemble canon
    canon = {
        "meta": {
            "version": "2.0.0-ARCHAEOLOGIST",
            "source_root": str(root.resolve()),
        },
        "provenance": prov,
        "manifest": manifest,
        "grammar": grammar,
        "grammar_map": grammar_map,
        "commentomancy": commentomancy,
        "schools": schools
    }
    
    # Drift checks (fail fast with consolidated report)
    errs = []
    
    # A) token→school mapping resolves to exactly 19 unique schools
    uniq = set(manifest["token_to_school_mapping"].values())
    if len(uniq) != manifest["total_schools"]:
        errs.append(f"token_to_school_mapping yields {len(uniq)} unique schools, expected {manifest['total_schools']}")
    
    # B) Every mapped school name exists in extracted schools
    names = {v["name"] for v in schools.values() if v.get("name")}
    for tok, sname in manifest["token_to_school_mapping"].items():
        if sname not in names:
            errs.append(f"grammar token '{tok}' maps to missing/unknown school '{sname}'")
    
    # C) School count matches manifest
    if len(schools) != manifest["total_schools"]:
        errs.append(f"school count {len(schools)} != manifest.total_schools {manifest['total_schools']}")
    
    if errs:
        canon["diagnostics"] = {"errors": errs}
    
    return canon

# ---------- Rosetta Renderer (Optional) ----------
ROSETTA_HEADER = """# 🔮 CodeCraft Rosetta Stone

**Generated:** {ts}Z  
**Version:** 2.0.0-ARCHAEOLOGIST  
**Status:** canonical (generated from lexicon sources)

---

## I. The 19 Arcane Schools

"""

def render_rosetta(canon: Dict[str, Any]) -> str:
    """Render Rosetta Stone from canon (integrity hash to be filled by fixer)."""
    ts = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
    parts = [ROSETTA_HEADER.format(ts=ts)]
    
    for sid in sorted(canon["schools"], key=lambda k: int(k) if str(k).isdigit() else k):
        s = canon["schools"][sid]
        parts.append(f"### {s.get('name', 'Unknown')}")
        if s.get("emoji"):
            parts[-1] += f" {s['emoji']}"
        
        if s.get("purpose"):
            parts.append(f"\n**Purpose:** {s['purpose']}\n")
        
        if s.get("spec", {}).get("safety_tier") is not None:
            parts.append(f"**Safety Tier:** {s['spec'].get('safety_tier')}\n")
        
        if s.get("operations"):
            parts.append("**Operations:**")
            for op in s["operations"]:
                parts.append(f"- {op}")
            parts.append("")
        
        if s.get("constraints"):
            parts.append("**Constraints:**")
            for c in s["constraints"]:
                parts.append(f"- {c}")
            parts.append("")
        
        if s.get("examples"):
            parts.append("**Examples:**")
            for ex in s["examples"]:
                parts.append(f"```codecraft\n{ex}\n```")
            parts.append("")
    
    parts.append("\n---\n## Embedded Machine Manifest\n")
    parts.append("```yaml")
    parts.append("# Machine-readable manifest")
    parts.append("# Full canon.lock.yaml used by validators/VM")
    parts.append("# Integrity hash computed over canonical view (excluding this block)")
    parts.append("")
    parts.append("metadata:")
    parts.append("  integrity:")
    parts.append("    sha256: <pending>")
    parts.append("    method: MEGA_canonical_block_exclusion")
    parts.append("    validator: scripts/lost_validate.py")
    parts.append("```")
    
    return "\n".join(parts)

# ---------- CLI Subcommands (MEGA's v2.2 Pattern) ----------
def cmd_extract(args):
    """Extract canon from lexicon sources (MEGA's CLI pattern + Oracle's v2.1 logic)."""
    root = Path(args.root if hasattr(args, 'root') else '.')
    canon = build_canon(root, args)
    
    # Write canon.lock output (YAML or JSON based on extension)
    outp = root / args.out
    ext = outp.suffix.lower()
    
    with outp.open('w', encoding='utf-8', newline='\n') as f:
        if ext == '.json':
            import json
            json.dump(canon, f, indent=2, sort_keys=False)
        else:
            yaml.safe_dump(canon, f, sort_keys=False, allow_unicode=True)
    
    print(f"✅ Wrote {outp}")
    
    # Optional: render Rosetta Stone
    if hasattr(args, 'render_rosetta') and args.render_rosetta:
        ros = render_rosetta(canon)
        (root / args.rosetta_path).write_text(ros, encoding='utf-8', newline='\n')
        print(f"✅ Synthesized {args.rosetta_path} (hash to be filled by fixer)")
    
    # Emit diagnostics if present
    diag = canon.get("diagnostics")
    if diag and diag.get("errors"):
        print("\n❌ DRIFT DETECTED:", file=sys.stderr)
        for e in diag["errors"]:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(2)
    
    return 0

def cmd_verify(args):
    """Verify canon.lock schema and cross-references (MEGA's v2.2 spec)."""
    canon_path = Path(args.canon)
    
    if not canon_path.exists():
        print(f"ERROR: Canon file not found: {canon_path}", file=sys.stderr)
        return 1
    
    # Load canon
    ext = canon_path.suffix.lower()
    if ext == '.json':
        import json
        canon = json.loads(canon_path.read_text(encoding='utf-8'))
    else:
        canon = yaml.safe_load(canon_path.read_text(encoding='utf-8'))
    
    # Basic schema checks
    errors = []
    
    # Check required top-level keys
    required = ["meta", "manifest", "schools"]
    for key in required:
        if key not in canon:
            errors.append(f"Missing required key: {key}")
    
    # Check schools partition
    passed_schools = []
    if "schools" in canon:
        for sid, school in canon["schools"].items():
            school_name = school.get('name', f'School {sid}')
            school_passed = True
            
            # Verify Law/Lore co-presence (Constitutional requirement)
            if not school.get("law"):
                errors.append(f"School {sid} ({school_name}) missing Law")
                school_passed = False
            if not school.get("lore"):
                errors.append(f"School {sid} ({school_name}) missing Lore")
                school_passed = False
            
            # Verify canonical ID format (snake_case)
            if "id" in school:
                school_id = str(school["id"])
                if not re.match(r'^[a-z0-9_]+$', school_id):
                    errors.append(f"School {sid} has non-canonical ID: {school_id}")
                    school_passed = False
            
            if school_passed:
                passed_schools.append(school_name)
    
    # Print passing schools first
    if passed_schools:
        print("✅ PASSED:")
        for name in passed_schools:
            print(f"  ✅ {name}")
        print()
    
    if errors:
        print("❌ FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    
    print("✅ All schools verified")
    return 0

def cmd_hash(args):
    """Print sha256 hash of canon.lock file (MEGA's v2.2 spec)."""
    canon_path = Path(args.canon)
    
    if not canon_path.exists():
        print(f"ERROR: Canon file not found: {canon_path}", file=sys.stderr)
        return 1
    
    digest = sha256_path(canon_path)
    print(digest)
    return 0

def cmd_scan_school(args):
    """Scan canon.lock for school information (supports single school or ALL)."""
    # Default canon path if not provided
    if not hasattr(args, 'canon') or not args.canon:
        # Auto-detect: prefer codecraft-native, fallback to codecraft
        from pathlib import Path
        native_canon = Path(__file__).parent.parent.parent.parent / "languages" / "codecraft-native" / "canon" / "canon.lock.yaml"
        legacy_canon = Path(__file__).parent.parent.parent.parent / "languages" / "codecraft" / "canon.lock.yaml"
        
        if native_canon.exists():
            canon_path = native_canon
        elif legacy_canon.exists():
            canon_path = legacy_canon
        else:
            print(f"❌ ERROR: No canon.lock.yaml found. Searched:", file=sys.stderr)
            print(f"  - {native_canon}", file=sys.stderr)
            print(f"  - {legacy_canon}", file=sys.stderr)
            return 1
    else:
        canon_path = Path(args.canon)
    
    if not canon_path.exists():
        print(f"❌ ERROR: Canon file not found: {canon_path}", file=sys.stderr)
        return 1
    
    # Load canon.lock
    with open(canon_path, 'r', encoding='utf-8') as f:
        canon = yaml.safe_load(f)
    
    if not canon or "schools" not in canon:
        print(f"❌ ERROR: Invalid canon.lock format (no 'schools' key)", file=sys.stderr)
        return 1
    
    schools = canon["schools"]
    
    # If no school specified, list all schools
    if not hasattr(args, 'school') or not args.school:
        print(f"{'═' * 70}")
        print(f"📜 CODECRAFT CANON - ALL SCHOOLS ({len(schools)} total)")
        print(f"   Source: {canon_path.name}")
        print(f"{'═' * 70}\n")
        
        for key, school in sorted(schools.items(), key=lambda x: x[1].get("id", 999)):
            num = school.get("id", "?")
            name = school.get("name", key)
            emoji = school.get("emoji", "")
            ops_count = len(school.get("law", {}).get("operations", [])) if "law" in school else len(school.get("operations", []))
            
            print(f"  {num:2}. {emoji} {name:20} - {ops_count:2} operations")
        
        print(f"\n{'═' * 70}")
        print(f"💡 TIP: Use 'omni canon scan --school <number>' to see details")
        print(f"{'═' * 70}")
        return 0
    
    # Find school by number or name
    school_query = args.school.lower().strip()
    target_school = None
    school_key = None
    
    # Try exact numeric match first (e.g., "13")
    if school_query.isdigit():
        school_num = int(school_query)
        for key, school in schools.items():
            if school.get("school_number") == school_num:
                target_school = school
                school_key = key
                break
    
    # Try name match (e.g., "thaumaturgy")
    if not target_school:
        for key, school in schools.items():
            school_id = str(school.get("id", "")).lower()
            school_name = str(school.get("name", "")).lower()
            if school_query in school_id or school_query in school_name or school_query == key.lower():
                target_school = school
                school_key = key
                break
    
    if not target_school:
        print(f"❌ ERROR: School '{args.school}' not found in canon.lock", file=sys.stderr)
        print(f"\n📜 Available schools:", file=sys.stderr)
        for key, school in sorted(schools.items(), key=lambda x: x[1].get("school_number", 999)):
            num = school.get("school_number", "?")
            name = school.get("name", key)
            print(f"  {num:2}. {name} ({school.get('id', key)})", file=sys.stderr)
        return 1
    
    # Display school information
    num = target_school.get("school_number", "?")
    name = target_school.get("name", school_key)
    emoji = target_school.get("emoji", "")
    school_id = target_school.get("id", school_key)
    
    print(f"{'═' * 70}")
    print(f"📜 SCHOOL {num}: {name} {emoji}")
    print(f"{'═' * 70}")
    print(f"ID: {school_id}")
    print(f"Tokens: {', '.join(target_school.get('tokens', []))}")
    print(f"Safety Tier: {target_school.get('safety_tier', 'unknown')}")
    print()
    
    # Purpose
    if "purpose" in target_school:
        print(f"📖 PURPOSE:")
        print(f"  {target_school['purpose']}")
        print()
    
    # Operations
    if "operations" in target_school and target_school["operations"]:
        print(f"⚙️  OPERATIONS ({len(target_school['operations'])}):")
        for i, op in enumerate(target_school["operations"], 1):
            print(f"  {i}. {op}")
        print()
    else:
        print(f"⚠️  OPERATIONS: None defined in canon.lock")
        print()
    
    # Constraints
    if "constraints" in target_school and target_school["constraints"]:
        print(f"🛡️  CONSTRAINTS ({len(target_school['constraints'])}):")
        for i, con in enumerate(target_school["constraints"], 1):
            print(f"  {i}. {con}")
        print()
    
    # Examples
    if "examples" in target_school and target_school["examples"]:
        print(f"✨ EXAMPLES ({len(target_school['examples'])}):")
        for i, ex in enumerate(target_school["examples"], 1):
            preview = ex[:100] + "..." if len(ex) > 100 else ex
            print(f"  {i}. {preview}")
        print()
    
    # Dependencies (if present)
    if "dependencies" in target_school:
        print(f"🔗 DEPENDENCIES:")
        deps = target_school["dependencies"]
        if isinstance(deps, dict):
            if "mandatory" in deps:
                print(f"  Mandatory: {', '.join(deps['mandatory']) if deps['mandatory'] else 'None'}")
            if "recommended" in deps:
                print(f"  Recommended: {', '.join(deps['recommended']) if deps['recommended'] else 'None'}")
        else:
            print(f"  {deps}")
        print()
    
    # Provenance
    if "provenance" in target_school:
        prov = target_school["provenance"]
        print(f"📂 PROVENANCE:")
        print(f"  Source: {prov.get('source_file', 'unknown')}")
        print(f"  Hash: {prov.get('file_hash', 'unknown')[:16]}...")
        print()
    
    print(f"{'═' * 70}")
    return 0

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Rosetta Archaeologist v2.2 - Extract THE LAW from lexicon")
    
    # Check if using legacy single-command mode (backward compatibility)
    if '--out' in sys.argv and 'extract' not in sys.argv:
        # Legacy mode: default to extract subcommand
        args_legacy = argparse.Namespace()
        args_legacy.root = '.'
        args_legacy.schools = 'lexicon/schools.canonical.yaml'
        args_legacy.schools_dir = 'lexicon/02_ARCANE_SCHOOLS'
        args_legacy.ebnf = 'lexicon/grammar/lexicon.ebnf'
        args_legacy.grammar_map = 'lexicon/grammar/EBNF_TO_PARSER_MAPPING.md'
        args_legacy.law = 'spec/LAW_AND_LORE_PROTOCOL.md'
        args_legacy.commentomancy = 'lexicon/commentomancy'
        args_legacy.out = 'canon.lock.yaml'
        args_legacy.render_rosetta = False
        args_legacy.rosetta_path = 'CODECRAFT_ROSETTA_STONE.md'
        
        # Parse legacy args
        legacy_parser = argparse.ArgumentParser()
        legacy_parser.add_argument('--root', default='.')
        legacy_parser.add_argument('--schools', default='lexicon/schools.canonical.yaml')
        legacy_parser.add_argument('--schools_dir', default='lexicon/02_ARCANE_SCHOOLS')
        legacy_parser.add_argument('--ebnf', default='lexicon/grammar/lexicon.ebnf')
        legacy_parser.add_argument('--grammar_map', default='lexicon/grammar/EBNF_TO_PARSER_MAPPING.md')
        legacy_parser.add_argument('--law', default='spec/LAW_AND_LORE_PROTOCOL.md')
        legacy_parser.add_argument('--commentomancy', default='lexicon/commentomancy')
        legacy_parser.add_argument('--out', default='canon.lock.yaml')
        legacy_parser.add_argument('--render_rosetta', action='store_true')
        legacy_parser.add_argument('--rosetta_path', default='CODECRAFT_ROSETTA_STONE.md')
        args = legacy_parser.parse_args()
        
        sys.exit(cmd_extract(args))
    
    # Modern subcommand mode (MEGA's v2.2 pattern)
    sub = ap.add_subparsers(dest="cmd", required=True, help="Subcommands")
    
    # extract subcommand
    p_ext = sub.add_parser("extract", help="Extract canon from lexicon sources")
    p_ext.add_argument('--root', default='.', help="CodeCraft repo root")
    p_ext.add_argument('--lexicon', default='./lexicon', help="Lexicon directory")
    p_ext.add_argument('--schools', default='lexicon/schools.canonical.yaml', help="schools.canonical.yaml")
    p_ext.add_argument('--schools_dir', default='lexicon/02_ARCANE_SCHOOLS', help="School markdown directory")
    p_ext.add_argument('--ebnf', default='lexicon/grammar/lexicon.ebnf', help="EBNF grammar file")
    p_ext.add_argument('--grammar_map', default='lexicon/grammar/EBNF_TO_PARSER_MAPPING.md', help="Grammar mapping")
    p_ext.add_argument('--law', default='spec/LAW_AND_LORE_PROTOCOL.md', help="Law & Lore protocol")
    p_ext.add_argument('--commentomancy', default='lexicon/commentomancy', help="Commentomancy directory")
    p_ext.add_argument('--out', required=True, help="Output canon lock file (.yaml or .json)")
    p_ext.add_argument('--spec', default='2.2', help="Canon spec version")
    p_ext.add_argument('--render_rosetta', action='store_true', help="Render Rosetta Stone")
    p_ext.add_argument('--rosetta_path', default='CODECRAFT_ROSETTA_STONE.md', help="Rosetta output")
    
    # verify subcommand
    p_ver = sub.add_parser("verify", help="Verify canon.lock schema and integrity")
    p_ver.add_argument('--canon', required=True, help="Path to canon.lock file")
    
    # hash subcommand
    p_hash = sub.add_parser("hash", help="Print sha256 hash of canon.lock")
    p_hash.add_argument('--canon', required=True, help="Path to canon.lock file")
    
    # scan subcommand (NEW - Oracle's request)
    p_scan = sub.add_parser("scan", help="Scan canon.lock for specific school information")
    p_scan.add_argument('--canon', required=True, help="Path to canon.lock file")
    p_scan.add_argument('--school', required=True, help="School number (e.g., 13) or name (e.g., thaumaturgy)")
    
    args = ap.parse_args()
    
    if args.cmd == "extract":
        sys.exit(cmd_extract(args))
    elif args.cmd == "verify":
        sys.exit(cmd_verify(args))
    elif args.cmd == "hash":
        sys.exit(cmd_hash(args))
    elif args.cmd == "scan":
        sys.exit(cmd_scan_school(args))

if __name__ == "__main__":
    main()
