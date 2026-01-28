"""
Fleet generation config for CodeCraft Station.

Fleet consists of 3 pip-installed MCP servers for the ritual pipeline.
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone


def generate_fleet(station_path: Path = None, cartography_pillar=None) -> Dict[str, Any]:
    """Generate CodeCraft fleet from pip-installed MCP servers."""
    return {
        "station_id": "station-codecraft",
        "version": "1.0.0",
        "description": "CodeCraft Station - 3 MCP servers for ritual pipeline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fleet_type": "mcp_servers",
        "servers": [
            {
                "id": "lexicon",
                "name": "Lexicon MCP Server",
                "role": "analyzer",
                "pillar": "Ethics & Safety (Judge/Scribe)",
                "runtime": "python_mcp",
                "command": "lexicon-mcp",
                "host": "localhost",
                "port": 7001,
                "source": "pip",
                "location": "federation-lexicon-mcp (pip package)",
                "tools": ["validate_codecraft", "canonize_codecraft"],
                "description": "Constitutional validator - Judge mode detects violations, Scribe mode auto-canonizes rituals"
            },
            {
                "id": "codeverter",
                "name": "CodeVerter MCP Server",
                "role": "generator",
                "pillar": "Genesis / Blueprinting (Arcane Weaver)",
                "runtime": "python_mcp",
                "command": "codeverter-mcp",
                "host": "localhost",
                "port": 7002,
                "source": "pip",
                "location": "federation-codeverter-mcp (pip package)",
                "tools": ["convert_code_to_codecraft"],
                "description": "Dual-engine ritual generator - Arcane Weaver (Gemini) + Clockwork Scribe (local transpiler)"
            },
            {
                "id": "native-embassy",
                "name": "CodeCraft Native Embassy",
                "role": "executor",
                "pillar": "Execution / Deployment (Rust VM)",
                "runtime": "python_mcp",
                "command": "embassy-mcp",
                "host": "localhost",
                "port": 7003,
                "source": "pip",
                "location": "federation-embassy-mcp (pip package)",
                "tools": ["execute_codecraft_ritual"],
                "description": "Universal executor via Rust VM - 7 backends (python, js, web, quantum, native, llm, mcp)"
            }
        ]
    }


# Export metadata about this config
CONFIG_META = {
    "station_id": "station-codecraft",
    "fleet_type": "mcp_servers",
    "description": "3 pip-installed MCP servers for CodeCraft ritual pipeline"
}
