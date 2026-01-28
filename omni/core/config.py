import yaml
from pathlib import Path
from typing import Dict, Any, List

# Default Configuration
DEFAULT_CONFIG = {
    "scan": {
        "include": ["**/*.py", "**/*.js", "**/*.ts", "**/*.go", "**/*.rs", "**/*.java"],
        "exclude": [
            "dist", "build", "node_modules", "tests", "__pycache__", 
            ".git", ".venv", "venv", "env", "site-packages",
            "external-frameworks", "mcp-servers/serena",
            "**/.gemini/antigravity/brain",
            "var", "data", "input", "output",
            "INBOX", "archive", "older_versions",
            # Exclude self-scanning
            "tools/omni/core", "tools/omni/tests", 
            "tools/omni", # Exclude the entire omni tool directory to avoid self-scanning noise as requested
            # Exclude docs by default (separate channel if needed)
            "docs", "contracts",
            # NOISE KILLERS
            "agent-backup", "*_template*", "templates", 
            "ghost-finger-manager", "ghost_fingers",
            "_temp", "recovery", "download_docs", "Unsorted Desktop Docs"
        ],
        "patterns": {
            "generic_events": [
                r"\.publish\(",
                r"\.emit\(",
                r"\.dispatch\(",
                r"crown://"
            ]
        }
    }
}

def load_config(root_path: Path = None) -> Dict[str, Any]:
    """
    Load omni.yml from the root path or current directory.
    Falls back to DEFAULT_CONFIG if no file is found.
    """
    if root_path is None:
        root_path = Path.cwd()
    
    config_path = root_path / "omni.yml"
    
    if not config_path.exists():
        # Try looking up one level (common in monorepos)
        parent_config = root_path.parent / "omni.yml"
        if parent_config.exists():
            config_path = parent_config
            
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                return _merge_config(DEFAULT_CONFIG, user_config)
        except Exception as e:
            print(f"[WARN] Failed to load omni.yml: {e}. Using defaults.")
            return DEFAULT_CONFIG
            
    return DEFAULT_CONFIG

def _merge_config(default: Dict, user: Dict) -> Dict:
    """Deep merge user config into default config."""
    result = default.copy()
    if not user:
        return result
        
    for key, value in user.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result
