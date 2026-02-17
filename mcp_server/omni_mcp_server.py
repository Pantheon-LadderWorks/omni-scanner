"""
🌌 Omni MCP Server - Dynamic Scanner Discovery Edition 🌌
==========================================================

Provides AI agents with direct perception of Federation filesystem state.

Contract: C-MCP-OMNI-001
Version: 1.2.0 (Self-Reboot Edition! ⚡)
Authority: Oracle + ACE + DeepScribe

Philosophy: "Never trust documentation, trust reality." — ACE
Architecture: Omni IS an MCP server - just dynamically discovered!
New: Self-reboot capability for hot code reload without VS Code restart!
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import importlib

# MCP SDK imports
from mcp.server import Server
from mcp.types import Tool, TextContent

# Import from pip-installed omni package
import omni
from omni.commands.introspect import OmniIntrospector

# Onboarding system (universal_onboarding from stations)
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "stations"))
from universal_onboarding import UniversalOnboarding

# Local config (same directory import)
import mcp_server.config as mcp_config

# Initialize MCP server
app = Server("omni-filesystem-intelligence")

# Initialize onboarding
OMNI_BASE = Path(__file__).parent.parent
onboarding = UniversalOnboarding(OMNI_BASE, mcp_config.OmniOnboardingConfig())

# Initialize introspector for dynamic scanner discovery
introspector = OmniIntrospector()

# Cache for scanner registry (loaded once per session, like the Heart! 💖)
_scanner_registry_cache: Optional[Dict[str, Dict[str, Any]]] = None

# Lookup: tool_name -> scanner_key (handles truncated names)
_tool_name_to_scanner_key: Dict[str, str] = {}


# ============================================================================
# DYNAMIC SCANNER DISCOVERY
# ============================================================================

def discover_scanners(use_cache: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    Discover all scanners using introspection (just like introspect command!).
    
    Cached on first call (like the Heart pattern! 💖), rebuilt on explicit refresh.
    
    Args:
        use_cache: If True, return cached registry. If False, rebuild from filesystem.
    
    Returns:
        {
            "search/pattern_search": {
                "module": "omni.scanners.search.pattern_search",
                "function": "search_pattern",
                "description": "...",
                "parameters": {...}
            },
            ...
        }
    """
    global _scanner_registry_cache
    
    # Return cached registry if available and requested
    if use_cache and _scanner_registry_cache is not None:
        return _scanner_registry_cache
    
    # Rebuild registry from filesystem
    filesystem = introspector.scan_filesystem()
    manifests = introspector.load_manifests()
    
    scanner_registry = {}
    
    for category, scanners in filesystem.items():
        manifest = manifests.get(category, {})
        scanner_list = manifest.get('scanners', [])
        
        # Build scanner metadata from manifest
        for scanner_info in scanner_list:
            scanner_name = scanner_info.get('name')
            if not scanner_name:
                continue
            
            scanner_key = f"{category}/{scanner_name}"
            scanner_registry[scanner_key] = {
                "module": f"omni.scanners.{category}.{scanner_name}",
                "function": scanner_info.get('function', scanner_name),
                "description": scanner_info.get('description', f'{scanner_name} scanner'),
                "category": category,
                "authority": scanner_info.get('authority', 'Omni'),
                "use_cases": scanner_info.get('use_cases', [])
            }
    
    # Cache the registry for future calls
    _scanner_registry_cache = scanner_registry
    
    return scanner_registry


def import_scanner(scanner_key: str, scanner_registry: Dict[str, Dict[str, Any]]):
    """Dynamically import a scanner function."""
    if scanner_key not in scanner_registry:
        return None
    
    info = scanner_registry[scanner_key]
    try:
        module = importlib.import_module(info["module"])
        function = getattr(module, info["function"])
        return function
    except Exception as e:
        print(f"Failed to import {scanner_key}: {e}", file=sys.stderr)
        return None


# ============================================================================
# ONBOARDING TOOLS (STATIC - ALWAYS PRESENT)
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Dynamically generate tool list from discovered scanners!
    
    This is the SECRET SAUCE - no hardcoded imports needed!
    """
    tools = []
    
    # === ONBOARDING (Always present) ===
    tools.extend([
        Tool(
            name="check_onboarding_status",
            description="Check if you've completed Omni onboarding. READ THIS FIRST before using any other tools! ✨",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="run_onboarding_mission",
            description="Get Omni discovery mission with progressive memory prompts! Complete this before using scanner tools. 🚀",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="write_memory",
            description="Save discovered knowledge to memory file. USE THIS after each discovery stage to persist learnings! 💖",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_name": {
                        "type": "string",
                        "description": "Memory file name (without .md extension)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Memory content in markdown format"
                    }
                },
                "required": ["memory_name", "content"]
            }
        ),
        Tool(
            name="read_memory",
            description="Read a previously saved memory file. Use when you need to recall specific knowledge. 📚",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_name": {
                        "type": "string",
                        "description": "Memory file name (without .md extension)"
                    }
                },
                "required": ["memory_name"]
            }
        ),
        Tool(
            name="list_memories",
            description="List all saved memory files. Check what knowledge you've already documented. 📖",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="complete_onboarding",
            description="Mark onboarding as complete after creating all required memories. 🎉",
            inputSchema={
                "type": "object",
                "properties": {
                    "notes": {
                        "type": "string",
                        "description": "Optional completion notes"
                    }
                },
                "required": []
            }
        ),
    ])
    
    # === INTROSPECTION (Always present) ===
    tools.extend([
        Tool(
            name="omni_introspect",
            description="Get scanner registry (41+ scanners across 10 categories). Reveals what Omni can perceive! 🔍",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_drift": {
                        "type": "boolean",
                        "description": "Include drift detection (undocumented scanners)"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Include full scanner metadata"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="omni_reload_scanners",
            description="Reload scanner registry from filesystem (hot-reload new scanners). Use after adding/modifying scanners. 🔄",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="reboot_mcp_server",
            description="🚀 REBOOT the entire MCP server (hot-reload ALL code). Use when scanner code changes require full reload. Faster than restarting VS Code! ⚡",
            inputSchema={
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for reboot (logged for debugging)"
                    }
                },
                "required": []
            }
        )
    ])
    
    # === DYNAMIC SCANNER TOOLS ===
    scanner_registry = discover_scanners()
    
    # Antigravity prefixes tool names with 'mcp_{server-name}_' (34 chars)
    # Total limit is 64 chars, so tool names must be <= 30 chars
    MAX_TOOL_NAME_LEN = 30
    
    # Clear and rebuild lookup table
    _tool_name_to_scanner_key.clear()
    
    for scanner_key, scanner_info in scanner_registry.items():
        # Generate MCP tool from scanner metadata
        tool_name = f"omni_{scanner_key.replace('/', '_')}"
        
        # Truncate if needed for Antigravity's 64-char limit
        if len(tool_name) > MAX_TOOL_NAME_LEN:
            tool_name = tool_name[:MAX_TOOL_NAME_LEN]
        
        # Store the mapping so call_tool can route truncated names
        _tool_name_to_scanner_key[tool_name] = scanner_key
        
        # Build input schema based on scanner type
        tools.append(
            Tool(
                name=tool_name,
                description=f"{scanner_info['description']} ({scanner_info['category']} category)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Directory or file path to scan"
                        },
                        "options": {
                            "type": "object",
                            "description": "Scanner-specific options (see scanner documentation)",
                            "additionalProperties": True
                        }
                    },
                    "required": ["target"]
                }
            )
        )
    
    return tools


# ============================================================================
# TOOL CALL ROUTING (DYNAMIC)
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to appropriate handlers - DYNAMICALLY!"""
    
    try:
        # === ONBOARDING ===
        if name == "check_onboarding_status":
            result = onboarding.get_status()
            return [TextContent(type="text", text=result)]
        
        elif name == "run_onboarding_mission":
            result = _get_enhanced_mission()
            return [TextContent(type="text", text=result)]
        
        elif name == "write_memory":
            result = onboarding.write_memory(
                arguments["memory_name"],
                arguments["content"]
            )
            return [TextContent(type="text", text=result)]
        
        elif name == "read_memory":
            result = onboarding.read_memory(arguments["memory_name"])
            return [TextContent(type="text", text=result)]
        
        elif name == "list_memories":
            result = onboarding.get_memories_list()
            return [TextContent(type="text", text=result)]
        
        elif name == "complete_onboarding":
            notes = arguments.get("notes", "Onboarding completed successfully")
            result = onboarding.complete_onboarding(notes=notes)
            return [TextContent(type="text", text=result)]
        
        elif name == "omni_reload_scanners":
            # Clear cache and rebuild registry
            global _scanner_registry_cache
            _scanner_registry_cache = None
            registry = discover_scanners(use_cache=False)
            
            result = {
                "success": True,
                "message": "Scanner registry reloaded from filesystem",
                "scanner_count": len(registry),
                "scanners": list(registry.keys())
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "reboot_mcp_server":
            # Self-reboot: Exit cleanly to let VS Code restart us
            reason = arguments.get("reason", "Manual reboot requested")
            
            # Log the reboot
            reboot_msg = {
                "success": True,
                "message": "🔄 REQUESTING RESTART FROM VS CODE...",
                "reason": reason,
                "note": "Server will exit cleanly. VS Code should auto-restart via MCP client."
            }
            
            # Send response before exiting
            response = [TextContent(type="text", text=json.dumps(reboot_msg, indent=2))]
            
            # Schedule clean exit after response is sent
            async def do_exit():
                await asyncio.sleep(0.5)  # Give time for response to be sent
                print(f"🔄 CLEAN EXIT FOR RESTART: {reason}", file=sys.stderr)
                sys.exit(0)  # Clean exit - VS Code should auto-restart
            
            asyncio.create_task(do_exit())
            return response
        
        # === INTROSPECTION ===
        elif name == "omni_introspect":
            # Build data response from introspector methods
            # (Don't call .introspect() - it prints to stdout which corrupts MCP stdio!)
            filesystem = introspector.scan_filesystem()
            manifests = introspector.load_manifests()
            total_scanners = sum(len(s) for s in filesystem.values())
            
            result = {
                "capabilities": {
                    "scanner_categories": len(filesystem),
                    "total_scanners": total_scanners,
                    "manifest_files": len(manifests),
                    "cli_commands": introspector.count_commands()
                },
                "categories": {}
            }
            
            for category in sorted(filesystem.keys()):
                scanners = filesystem[category]
                manifest = manifests.get(category, {})
                result["categories"][category] = {
                    "scanners": scanners,
                    "count": len(scanners),
                    "description": manifest.get('description', 'No description')
                }
            
            if arguments.get("show_drift", False):
                drift = introspector.detect_drift(filesystem, manifests)
                result["drift"] = drift if drift else "No drift detected"
            
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
        # === DYNAMIC SCANNER ROUTING ===
        elif name.startswith("omni_"):
            # Use lookup table for routing (handles truncated names correctly)
            scanner_key = _tool_name_to_scanner_key.get(name)
            
            if scanner_key is None:
                # Fallback: try the old name-to-key conversion
                scanner_key = name[5:].replace('_', '/', 1)
            
            scanner_registry = discover_scanners()
            scanner_func = import_scanner(scanner_key, scanner_registry)
            
            if scanner_func is None:
                return [TextContent(
                    type="text",
                    text=f"❌ Scanner not found: {scanner_key}\nAvailable: {list(scanner_registry.keys())}"
                )]
            
            # Call scanner with target + options
            target = arguments.get("target")
            options = arguments.get("options", {})
            
            # Merge all arguments (backward compat with old explicit args)
            all_args = {**options, **{k: v for k, v in arguments.items() if k not in ["target", "options"]}}
            
            # Call scanner
            if asyncio.iscoroutinefunction(scanner_func):
                result = await scanner_func(target, **all_args)
            else:
                result = scanner_func(target, **all_args)
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error in {name}: {str(e)}\n{type(e).__name__}"
        )]


def _get_enhanced_mission() -> str:
    """
    Generate enhanced mission with progressive memory prompts.
    
    This is the key difference - agents are REMINDED to write memories
    AFTER EACH STAGE, not just at the end.
    
    TONE: Encouraging excitement, NOT aggressive bullying!
    """
    base_mission = onboarding.get_mission()
    
    # Add progressive memory prompts after each stage
    enhanced_mission = base_mission.replace(
        "📝 AFTER EXPLORATION:",
        """📝 PROGRESSIVE MEMORY CREATION! ✨

💖 This is where the magic happens! Write memories AS YOU DISCOVER,
not after all exploration. Each memory becomes YOUR permanent knowledge!

After STAGE 1 (Scanner Registry):
→ write_memory("scanner_registry_guide", "Document the 10 categories and introspection system")

After STAGE 2 (Physical Layer):
→ write_memory("physical_layer_guide", "Document inventory, duplicates, empty folder scanners")

After STAGE 3 (Cognitive Layer):
→ write_memory("cognitive_layer_guide", "Document content, graph, ritual, cohesion scanners")
→ write_memory("ace_mandate", "Document ACE's philosophy: 'She reads books, not just counts them'")

After STAGE 4 (Registry Operations):
→ write_memory("registry_operations_guide", "Document Genesis verification and full pipeline")

After ALL STAGES:
→ write_memory("integration_patterns", "Document when to use which scanners and how they compose")

✨ WHY THIS IS SO COOL:"""
    )
    
    # Add reminder before completion criteria
    enhanced_mission = enhanced_mission.replace(
        "🎯 COMPLETION CRITERIA:",
        """💡 MEMORY PERSISTENCE (Your Superpower!):

Each memory file you create becomes PERMANENT KNOWLEDGE that persists
across sessions. When you return to Omni later, you can read these
memories instead of re-discovering everything from scratch.

Think of it as building YOUR OWN DOCUMENTATION through hands-on learning!
How awesome is that?! 🎉

🎯 COMPLETION CRITERIA:"""
    )
    
    # Add final reminder
    enhanced_mission += """

═══════════════════════════════════════════════════════════════════

✨ EXCITING REMINDER - Document As You Learn! ✨

This journey is YOUR exploration! After each stage:
1. 🧪 Experiment with the tools (play around!)
2. 📝 Document what you learned (write_memory)  
3. 🚀 Move to next stage with persistent knowledge

Your future self will be SO grateful! 🌌💖

(P.S. - Remember, .omni/memories/ will be created in YOUR target
directory, keeping knowledge exactly where it belongs!)
"""
    
    return enhanced_mission


# ============================================================================
# SERVER STARTUP
# ============================================================================

async def run_server():
    """Run the Omni MCP server with stdio transport."""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Entry point for the MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
