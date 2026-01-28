"""
Canon Scanner - Scan CodeCraft schools (source YAML or built canon.lock)

Modes:
  omni scan --scanners canon                    # Scan built canon.lock.yaml
  omni scan --scanners canon --source           # Scan source YAML front matter
  omni scan --scanners canon --verify           # Compare source vs built

Supports:
  --school <num|name>  # Filter to specific school
  --schema <path>      # Verify against schema (default: SCHOOL_FRONT_MATTER_SCHEMA.md)
"""
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from omni.core.paths import get_infrastructure_root

# Front matter extraction (same as rosetta_archaeologist.py)
FRONT_MATTER = re.compile(r'^\s*---\s*\n(?P<y>.*?\n)---\s*\n', re.DOTALL)

def parse_front_matter(md_text: str) -> Dict[str, Any]:
    """Extract YAML front matter from markdown."""
    match = FRONT_MATTER.match(md_text)
    if not match:
        return {}
    
    yaml_text = match.group('y')
    try:
        return yaml.safe_load(yaml_text) or {}
    except Exception:
        return {}

def validate_school_against_schema(school_data: Dict[str, Any], schema_version: str = "2.3") -> Dict[str, Any]:
    """
    Validate school YAML front matter against schema.
    
    Returns:
        {
            "valid": bool,
            "schema_version": str,
            "issues": [<list of validation errors>],
            "enhancements": {
                "has_allowed_values": bool,
                "has_relationships": bool,
                "operations_with_enums": int,
                "operations_with_relationships": int
            }
        }
    """
    issues = []
    enhancements = {
        "has_allowed_values": False,
        "has_relationships": False,
        "operations_with_enums": 0,
        "operations_with_relationships": 0
    }
    
    # Check required top-level keys
    if "school" not in school_data:
        issues.append("Missing 'school' key")
    
    if "law" not in school_data:
        issues.append("Missing 'law' key")
    
    # Check schema version
    declared_version = str(school_data.get("schema_version", "unknown"))
    expected_version = str(schema_version)
    if declared_version != expected_version:
        issues.append(f"Schema version mismatch: declared={declared_version}, expected={expected_version}")
    
    # Check law.operations structure
    if "law" in school_data and "operations" in school_data["law"]:
        ops = school_data["law"]["operations"]
        
        for idx, op in enumerate(ops):
            # Check required operation fields
            if "name" not in op:
                issues.append(f"Operation {idx}: missing 'name'")
            if "signature" not in op:
                issues.append(f"Operation {idx}: missing 'signature'")
            if "description" not in op:
                issues.append(f"Operation {idx}: missing 'description'")
            if "safety_tier" not in op:
                issues.append(f"Operation {idx}: missing 'safety_tier'")
            
            # Check for v2.3 enhancements
            if "params" in op:
                for param in op["params"]:
                    if "allowed_values" in param:
                        enhancements["has_allowed_values"] = True
                        enhancements["operations_with_enums"] += 1
                        
                        # Validate allowed_values structure
                        for val in param["allowed_values"]:
                            if "value" not in val:
                                issues.append(f"Operation {op.get('name', idx)}: allowed_values missing 'value'")
                            if "semantic" not in val:
                                issues.append(f"Operation {op.get('name', idx)}: allowed_values missing 'semantic'")
            
            if "relationships" in op:
                enhancements["has_relationships"] = True
                enhancements["operations_with_relationships"] += 1
                
                # Validate relationships structure
                rel = op["relationships"]
                if not isinstance(rel, dict):
                    issues.append(f"Operation {op.get('name', idx)}: relationships must be a dict")
    
    return {
        "valid": len(issues) == 0,
        "schema_version": declared_version,
        "issues": issues,
        "enhancements": enhancements
    }

def scan_source_front_matter(target_path: Path, school_filter: Optional[str] = None) -> Dict[str, Any]:
    """Scan YAML front matter from school markdown files."""
    # Get Infrastructure root from CartographyPillar
    infra_root = get_infrastructure_root()
    
    if not infra_root:
        # Fallback: look for INFRASTRUCTURE_MANIFEST_V1.yaml upwards from cwd
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / "INFRASTRUCTURE_MANIFEST_V1.yaml").exists():
                infra_root = parent
                break
    
    if not infra_root:
        return {
            "error": "Infrastructure root not found (CartographyPillar unavailable and no manifest found)",
            "count": 0,
            "schools": []
        }
    
    # Find schools directory
    schools_dir = infra_root / "languages" / "codecraft" / "lexicon" / "02_ARCANE_SCHOOLS"
    
    if not schools_dir.exists() or not schools_dir.is_dir():
        return {
            "error": f"Schools directory not found at {schools_dir}",
            "count": 0,
            "schools": []
        }
    
    # Scan all school markdown files
    school_files = sorted(schools_dir.glob("*.md"))
    schools = []
    
    for school_file in school_files:
        # Skip schema files
        if "SCHEMA" in school_file.name.upper() or "TEMPLATE" in school_file.name.upper():
            continue
        
        try:
            with open(school_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            continue
        
        front_matter = parse_front_matter(content)
        
        if not front_matter:
            continue
        
        # Extract school metadata
        school_meta = front_matter.get("school", {})
        school_id = school_meta.get("id", None)
        school_name = school_meta.get("name", school_file.stem)
        
        # Skip if no valid school id
        if school_id is None:
            continue
        
        # Apply filter if specified
        if school_filter:
            school_query = str(school_filter).lower().strip()
            matched = False
            
            if school_query.isdigit():
                # Numeric filter - compare to school id
                if int(school_query) == school_id:
                    matched = True
            else:
                # Name filter - partial match
                if school_query in school_name.lower():
                    matched = True
            
            if not matched:
                continue
        
        # Validate against schema
        validation = validate_school_against_schema(front_matter)
        
        # Extract operations
        operations = []
        if "law" in front_matter and "operations" in front_matter["law"]:
            for op in front_matter["law"]["operations"]:
                op_summary = {
                    "name": op.get("name", "unknown"),
                    "signature": op.get("signature", ""),
                    "description": op.get("description", ""),
                    "safety_tier": op.get("safety_tier", 0),
                    "has_enum_semantics": False,
                    "has_relationships": False
                }
                
                # Check for enhancements
                if "params" in op:
                    for param in op["params"]:
                        if "allowed_values" in param:
                            op_summary["has_enum_semantics"] = True
                            break
                
                if "relationships" in op:
                    op_summary["has_relationships"] = True
                
                operations.append(op_summary)
        
        schools.append({
            "id": school_id,
            "name": school_name,
            "emoji": school_meta.get("emoji", ""),
            "tokens": school_meta.get("tokens", []),
            "category": school_meta.get("category", ""),
            "purpose": school_meta.get("purpose", ""),
            "safety_tier": front_matter.get("law", {}).get("safety_tier", 0),
            "operation_count": len(operations),
            "operations": operations,
            "schema_version": front_matter.get("schema_version", "unknown"),
            "source_file": school_file.name,
            "validation": validation
        })
    
    return {
        "count": len(schools),
        "total_schools": len(school_files) - 1,  # Exclude schema file
        "schools": schools,
        "source_dir": str(schools_dir),
        "mode": "source_front_matter"
    }

def scan(target_path: Path, **kwargs) -> Dict[str, Any]:
    """
    Scan CodeCraft schools - either source YAML front matter or built canon.lock.
    
    Args:
        target_path: Root path to scan
        **kwargs: 
            source (bool): Scan YAML front matter instead of canon.lock
            school (str): Filter to specific school
            verify (bool): Compare source vs built
    
    Returns:
        Scan results with schools, operations, validation
    """
    scan_source = kwargs.get("source", False)
    verify_mode = kwargs.get("verify", False)
    school_filter = kwargs.get("school")
    
    if scan_source:
        # Scan YAML front matter from markdown files
        return scan_source_front_matter(target_path, school_filter)
    
    if verify_mode:
        # Compare source vs built
        source_result = scan_source_front_matter(target_path, school_filter)
        built_result = scan_built_canon(target_path, school_filter)
        
        return {
            "mode": "verification",
            "source": source_result,
            "built": built_result,
            "comparison": compare_source_to_built(source_result, built_result)
        }
    
    # Default: scan built canon.lock.yaml
    return scan_built_canon(target_path, school_filter)

def compare_source_to_built(source_result: Dict[str, Any], built_result: Dict[str, Any]) -> Dict[str, Any]:
    """Compare source YAML front matter to built canon.lock."""
    issues = []
    
    if source_result.get("error"):
        return {"error": f"Source scan failed: {source_result['error']}"}
    
    if built_result.get("error"):
        return {"error": f"Built scan failed: {built_result['error']}"}
    
    source_schools = {s["id"]: s for s in source_result.get("schools", [])}
    built_schools = {s["id"]: s for s in built_result.get("schools", [])}
    
    # Check for missing schools in built
    for school_id in source_schools:
        if school_id not in built_schools:
            issues.append(f"School {school_id} exists in source but not in built canon")
    
    # Check for extra schools in built
    for school_id in built_schools:
        if school_id not in source_schools:
            issues.append(f"School {school_id} exists in built canon but not in source")
    
    # Compare operation counts
    for school_id in source_schools:
        if school_id in built_schools:
            source_ops = source_schools[school_id]["operation_count"]
            built_ops = built_schools[school_id]["operation_count"]
            
            if source_ops != built_ops:
                issues.append(f"School {school_id}: operation count mismatch (source={source_ops}, built={built_ops})")
    
    return {
        "in_sync": len(issues) == 0,
        "issues": issues,
        "source_count": len(source_schools),
        "built_count": len(built_schools)
    }

def scan_built_canon(target_path: Path, school_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Scan CodeCraft canon.lock.yaml for schools and operations.
    
    Args:
        target_path: Root path to scan (searches for canon.lock.yaml)
        **kwargs: Optional filters (school=<num or name>)
    
    Returns:
        {
            "count": <total schools>,
            "schools": [<school summaries>],
            "canon_path": <path to canon.lock.yaml>,
            "version": <canon version>
        }
    """
    # Auto-detect canon.lock.yaml
    canon_candidates = [
        target_path / "canon" / "canon.lock.yaml",  # codecraft-native/canon/
        target_path / "canon.lock.yaml",            # direct
        target_path / ".." / "codecraft-native" / "canon" / "canon.lock.yaml",  # from codecraft/
        target_path / ".." / ".." / "languages" / "codecraft-native" / "canon" / "canon.lock.yaml",  # from Infrastructure root
    ]
    
    canon_path = None
    for candidate in canon_candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            canon_path = resolved
            break
    
    if not canon_path:
        return {
            "error": "Canon lock file not found",
            "searched": [str(c) for c in canon_candidates],
            "count": 0,
            "schools": []
        }
    
    # Load canon.lock.yaml
    try:
        with open(canon_path, 'r', encoding='utf-8') as f:
            canon = yaml.safe_load(f)
    except Exception as e:
        return {
            "error": f"Failed to load canon: {e}",
            "canon_path": str(canon_path),
            "count": 0,
            "schools": []
        }
    
    if not canon or "schools" not in canon:
        return {
            "error": "Invalid canon format (no 'schools' key)",
            "canon_path": str(canon_path),
            "count": 0,
            "schools": []
        }
    
    schools_data = canon["schools"]
    school_filter = kwargs.get("school")  # Optional filter
    
    # Extract school summaries
    schools = []
    for key, school in sorted(schools_data.items(), key=lambda x: x[1].get("id", 999)):
        school_id = school.get("id", "?")
        school_name = school.get("name", key)
        
        # Apply filter if specified
        if school_filter:
            school_query = str(school_filter).lower().strip()
            if school_query.isdigit():
                if int(school_query) != school_id:
                    continue
            elif school_query not in school_name.lower():
                continue
        
        # Extract operations from law.operations (v2.3) or operations (legacy)
        operations = []
        if "law" in school and "operations" in school["law"]:
            # v2.3 schema with enhanced front matter
            ops_list = school["law"]["operations"]
            for op in ops_list:
                op_name = op.get("name", "unknown")
                op_sig = op.get("signature", "")
                op_desc = op.get("description", "")
                
                # Check for enhanced fields (allowed_values, relationships)
                has_enums = False
                has_relationships = False
                
                if "params" in op:
                    for param in op["params"]:
                        if "allowed_values" in param:
                            has_enums = True
                            break
                
                if "relationships" in op:
                    has_relationships = True
                
                operations.append({
                    "name": op_name,
                    "signature": op_sig,
                    "description": op_desc,
                    "emoji": op.get("emoji", ""),
                    "safety_tier": op.get("safety_tier", 0),
                    "enhanced": has_enums or has_relationships,  # v2.3 features
                    "has_enum_semantics": has_enums,
                    "has_relationships": has_relationships
                })
        elif "operations" in school:
            # Legacy format (just operation names)
            operations = [{"name": op, "legacy": True} for op in school["operations"]]
        
        schools.append({
            "id": school_id,
            "name": school_name,
            "emoji": school.get("emoji", ""),
            "tokens": school.get("tokens", []),
            "category": school.get("category", ""),
            "purpose": school.get("purpose", ""),
            "safety_tier": school.get("safety_tier", 0),
            "operation_count": len(operations),
            "operations": operations,
            "schema_version": school.get("schema_version", "unknown")
        })
    
    return {
        "count": len(schools),
        "total_schools": len(schools_data),
        "schools": schools,
        "canon_path": str(canon_path),
        "version": canon.get("meta", {}).get("version", "unknown"),
        "filtered": school_filter is not None
    }
