"""
CLI Command Decorator Pattern
==============================
Auto-registration system for Omni commands (stolen from Federation Heart).

Pattern:
    @command("name", "description", category="util")
    def cmd_example(args):
        ...
    
    # CLI auto-builds parser from COMMAND_REGISTRY
    
Authority: "Never manually wire commands - let them register themselves" - ACE
Contract: C-CLI-OMNI-AUTO-REGISTRATION-001
"""
from typing import Dict, List, Callable, Optional, Any

# Global command registry
COMMAND_REGISTRY: Dict[str, Dict[str, Any]] = {}


def command(
    name: str,
    description: str,
    category: str = "general",
    aliases: Optional[List[str]] = None,
    supports_flags: Optional[List[str]] = None,
    supports_targets: bool = False,
    supports_verbose: bool = False,
    **kwargs
):
    """
    Command decorator - auto-registers CLI commands.
    
    Args:
        name: Command name (primary)
        description: Help text shown in --help
        category: Command category (utility, scanner, registry, etc.)
        aliases: Alternative names for the command
        supports_flags: List of flag names this command accepts
        supports_targets: Whether command accepts positional target argument
        supports_verbose: Whether command accepts --verbose flag
        **kwargs: Additional metadata (love_letter, systems_empathy_note, etc.)
    
    Example:
        @command(
            "introspect",
            "Omni examines itself",
            category="utility",
            supports_flags=["--drift", "--scanners"]
        )
        def cmd_introspect(args):
            ...
    """
    def decorator(func: Callable):
        cmd_info = {
            "name": name,
            "description": description,
            "category": category,
            "func": func,
            "aliases": aliases or [],
            "supports_flags": supports_flags or [],
            "supports_targets": supports_targets,
            "supports_verbose": supports_verbose,
            **kwargs
        }
        
        # Register primary name
        COMMAND_REGISTRY[name] = cmd_info
        
        # Register aliases
        for alias in (aliases or []):
            COMMAND_REGISTRY[alias] = cmd_info.copy()
            COMMAND_REGISTRY[alias]["is_alias"] = True
            COMMAND_REGISTRY[alias]["primary_name"] = name
        
        return func
    
    return decorator


def list_all_commands(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all registered commands, optionally filtered by category.
    
    Args:
        category: Filter by category (optional)
        
    Returns:
        List of command info dicts
    """
    commands = []
    seen = set()
    
    for cmd_name, cmd_info in COMMAND_REGISTRY.items():
        # Skip aliases in listing (show primary only)
        if cmd_info.get("is_alias"):
            continue
        
        # Skip duplicates
        primary = cmd_info.get("primary_name", cmd_name)
        if primary in seen:
            continue
        seen.add(primary)
        
        # Filter by category if requested
        if category and cmd_info.get("category") != category:
            continue
        
        commands.append(cmd_info)
    
    return sorted(commands, key=lambda x: (x.get("category", ""), x["name"]))


def get_command(name: str) -> Optional[Dict[str, Any]]:
    """
    Get command info by name (supports aliases).
    
    Args:
        name: Command name or alias
        
    Returns:
        Command info dict or None if not found
    """
    return COMMAND_REGISTRY.get(name)


def get_categories() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all commands grouped by category.
    
    Returns:
        Dict mapping category name to list of commands
    """
    categories = {}
    
    for cmd_info in list_all_commands():
        category = cmd_info.get("category", "general")
        if category not in categories:
            categories[category] = []
        categories[category].append(cmd_info)
    
    return categories
