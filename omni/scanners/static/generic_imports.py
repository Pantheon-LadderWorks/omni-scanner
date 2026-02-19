"""
Generic Import Scanner
======================
Config-driven import scanner. READS from `omni/config/imports/*.yaml`.

Checks for:
- Banned Modules (deny)
- Restricted Modules (allow-list for specific paths)

Relies on `omni.scanners.architecture.imports.extract_imports` for AST parsing.
"""
import yaml
import os
import ast
from pathlib import Path
from typing import Dict, Any, List
from omni.lib.files import walk_project

# Reuse the robust AST extractor from the architecture scanner
try:
    from omni.scanners.architecture.imports import extract_imports
except ImportError:
    # Fallback if imports.py not available or refactored
    def extract_imports(filepath: Path) -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(filepath.read_text(encoding="utf-8"))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({"module": alias.name, "line": node.lineno})
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append({"module": node.module, "line": node.lineno})
            return imports
        except:
            return []

def scan(target: Path, **options) -> Dict[str, Any]:
    """
    Main entry point for generic import scanning.
    """
    results = {
        "count": 0,
        "items": [],
        "errors": []
    }
    
    # 1. Locate Configs
    config_dir = target / "omni" / "config" / "imports"
    if not config_dir.exists():
        # Fallback to package default
        config_dir = Path(__file__).parent.parent.parent / "config" / "imports"
    
    if not config_dir.exists():
        return results

    # 2. Load Rules
    rules = []
    for config_file in config_dir.glob("*.yaml"):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and 'rules' in config:
                    rules.extend(config['rules'])
        except Exception as e:
            results["errors"].append(f"Config load error {config_file.name}: {e}")

    if not rules:
        return results

    # 3. Scan Files
    # Walk all Python files using standardized walker
    for py_file in walk_project(target, extensions={".py"}):

        try:
            file_imports = extract_imports(py_file)
            for imp in file_imports:
                module = imp.get("module", "")
                
                for rule in rules:
                    pattern = rule.get("pattern", "")
                    if not pattern: continue
                    
                    # Check match (simple robust startswith)
                    if module == pattern or module.startswith(pattern + "."):
                        
                        # Check restrictions
                        allowed_paths = rule.get("allowed_paths", [])
                        rel_path = str(py_file.relative_to(target)).replace("\\", "/")
                        
                        is_allowed = False
                        if allowed_paths:
                            for allowed in allowed_paths:
                                if rel_path.startswith(allowed):
                                    is_allowed = True
                                    break
                        else:
                            # If no allowed_paths defined, it's a global ban unless type logic differs
                            pass

                        # Decision Logic
                        rule_type = rule.get("type", "deny")
                        
                        violation = None
                        if rule_type == "deny":
                            violation = True
                        elif rule_type == "restrict":
                            if not is_allowed:
                                violation = True
                        
                        if violation:
                            results["items"].append({
                                "file": rel_path,
                                "line": imp.get("line"),
                                "module": module,
                                "rule": rule.get("name", "banned_import"),
                                "description": rule.get("description", "Import violation"),
                                "severity": rule.get("severity", "warning")
                            })
                            results["count"] += 1

        except Exception as e:
             # creating noise? results["errors"].append(f"{py_file.name}: {e}")
             pass
            
    return results
