"""
AST Utility Library
===================
Shared logic for AST parsing and extraction.
Centralizes "piggybacking" logic for scanners that need to parse Python code.
"""
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

def extract_imports(filepath: Path) -> List[Dict[str, Any]]:
    """Parse a Python file and extract all import statements."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append({
                "line": node.lineno,
                "module": node.module,
                "names": [alias.name for alias in node.names],
                "type": "from",
            })
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "line": node.lineno,
                    "module": alias.name,
                    "names": [alias.name],
                    "type": "import",
                })
    return imports

def extract_decorators(filepath: Path) -> List[Dict[str, Any]]:
    """Extract all decorators and their arguments."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    decorators = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                dec_info = {"line": node.lineno, "function": node.name, "type": type(node).__name__}
                
                if isinstance(dec, ast.Name):
                    dec_info["name"] = dec.id
                elif isinstance(dec, ast.Attribute):
                    dec_info["name"] = f"{dec.value.id}.{dec.attr}" if isinstance(dec.value, ast.Name) else "complex"
                elif isinstance(dec, ast.Call):
                    # Handle @command(...) or @server.call_tool(...)
                    if isinstance(dec.func, ast.Name):
                        dec_info["name"] = dec.func.id
                    elif isinstance(dec.func, ast.Attribute):
                        dec_info["name"] = f"{dec.func.value.id}.{dec.func.attr}" if isinstance(dec.func.value, ast.Name) else "complex"
                    
                    # Extract args (simplified)
                    args = []
                    for arg in dec.args:
                        if isinstance(arg, ast.Constant):
                            args.append(arg.value)
                    dec_info["args"] = args
                
                decorators.append(dec_info)
    return decorators
