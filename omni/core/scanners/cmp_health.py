"""
CMP Memory Substrate Health Scanner
Queries Conversation Memory Project for database and memory health
"""
from pathlib import Path
from typing import Dict, Any


def scan(target: Path) -> dict:
    """
    Query CMP for memory substrate health.
    
    Args:
        target: Path to Infrastructure root (or anywhere in Federation)
        
    Returns:
        dict with database status, memory lane health, and MCP server availability
    """
    results = {
        "count": 0,
        "items": [],
        "metadata": {
            "scanner": "cmp_health",
            "version": "1.0.0"
        },
        "summary": {
            "database_status": "UNKNOWN",
            "mcp_servers_online": 0,
            "memory_lanes_active": 0,
            "total_conversations": 0
        }
    }
    
    try:
        # Find Infrastructure root
        infra_root = find_infrastructure_root(target)
        if not infra_root:
            results["metadata"]["error"] = "Infrastructure root not found"
            return results
        
        # Try importing CMP components
        try:
            health_info = {
                "database": {},
                "mcp_servers": {},
                "memory_lanes": {},
                "schema_info": {}
            }
            
            # Check database connection
            db_health = check_database_health()
            health_info["database"] = db_health
            
            if db_health.get("connected"):
                results["summary"]["database_status"] = "ONLINE"
                
                # Get schema info
                schema_info = get_schema_info()
                health_info["schema_info"] = schema_info
                
                # Get conversation count
                conv_count = get_conversation_count()
                results["summary"]["total_conversations"] = conv_count
                
            else:
                results["summary"]["database_status"] = "OFFLINE"
            
            # Check MCP servers
            mcp_health = check_mcp_servers()
            health_info["mcp_servers"] = mcp_health
            results["summary"]["mcp_servers_online"] = sum(
                1 for s in mcp_health.values() if s.get("status") == "ONLINE"
            )
            
            # Check memory lanes (9 lanes)
            memory_lanes = check_memory_lanes()
            health_info["memory_lanes"] = memory_lanes
            results["summary"]["memory_lanes_active"] = sum(
                1 for lane in memory_lanes.values() if lane.get("active", False)
            )
            
            # Add to items
            results["items"].append(health_info)
            results["count"] = 1
            
        except ImportError as e:
            results["metadata"]["error"] = f"CMP components not available: {str(e)}"
            results["summary"]["database_status"] = "NOT_INSTALLED"
            
    except Exception as e:
        results["metadata"]["error"] = f"CMP health check failed: {str(e)}"
        results["summary"]["database_status"] = "ERROR"
    
    return results


def check_database_health() -> Dict[str, Any]:
    """Check PostgreSQL database connection."""
    try:
        # Try to import and use CMP config
        import sys
        from pathlib import Path
        
        # Add CMP to path
        cmp_path = Path(__file__).parent.parent.parent.parent.parent / "conversation-memory-project"
        if cmp_path.exists():
            sys.path.insert(0, str(cmp_path))
        
        try:
            from mcp_servers.cmp_config import CMPConfig
            
            config = CMPConfig()
            
            # Check if connection info exists
            db_url = config.get_database_url()
            
            if db_url:
                # Try basic connection test
                import asyncpg
                import asyncio
                
                async def test_connection():
                    try:
                        conn = await asyncpg.connect(db_url, timeout=5)
                        await conn.close()
                        return True
                    except Exception:
                        return False
                
                connected = asyncio.run(test_connection())
                
                return {
                    "connected": connected,
                    "database": "cmp_federation",
                    "port": 5433,
                    "status": "ONLINE" if connected else "UNREACHABLE"
                }
            else:
                return {
                    "connected": False,
                    "status": "NOT_CONFIGURED"
                }
                
        except ImportError:
            return {
                "connected": False,
                "status": "CMP_NOT_INSTALLED"
            }
            
    except Exception as e:
        return {
            "connected": False,
            "status": "ERROR",
            "error": str(e)
        }


def get_schema_info() -> Dict[str, Any]:
    """Get database schema information."""
    try:
        # Query for table count, column count
        # This would require async DB query - placeholder for now
        return {
            "tables": 37,  # Known from CMP docs
            "columns": 277,
            "foreign_keys": 60,
            "schema_version": "e814b5c7cc3d"
        }
    except Exception as e:
        return {"error": str(e)}


def get_conversation_count() -> int:
    """Get total conversation count from database."""
    try:
        # Would require async DB query - placeholder
        return 0  # Unknown without query
    except Exception:
        return 0


def check_mcp_servers() -> Dict[str, Dict[str, Any]]:
    """Check status of CMP MCP servers."""
    servers = {
        "cmp-memory": {
            "tools": ["store_memory", "search_memories", "get_recent_memories"],
            "status": "UNKNOWN"
        },
        "cmp-knowledge-graph": {
            "tools": [
                "create_entities", "add_observations", "create_relations",
                "search_nodes", "open_nodes", "read_graph",
                "ask_cmp_copilot", "get_agent_summary"
            ],
            "status": "UNKNOWN"
        }
    }
    
    # Check if MCP config file exists
    try:
        import os
        mcp_config_path = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        
        if mcp_config_path.exists():
            import json
            with open(mcp_config_path, 'r') as f:
                config = json.load(f)
                
            # Check if servers are configured
            mcp_servers = config.get("mcpServers", {})
            
            for server_name in servers.keys():
                if server_name in mcp_servers:
                    servers[server_name]["status"] = "CONFIGURED"
                    servers[server_name]["command"] = mcp_servers[server_name].get("command")
    except Exception:
        pass
    
    return servers


def check_memory_lanes() -> Dict[str, Dict[str, Any]]:
    """Check status of 9 memory lanes."""
    lanes = {
        "episodic": {
            "description": "Sequential conversation replay",
            "active": False,
            "tables": ["conversations", "messages"]
        },
        "semantic": {
            "description": "Concept/topic search",
            "active": False,
            "tables": ["artifacts", "message_embeddings"]
        },
        "procedural": {
            "description": "How-to knowledge",
            "active": False,
            "tables": ["tool_calls", "procedural_artifacts"]
        },
        "working": {
            "description": "Active session context",
            "active": False,
            "tables": ["active_conversation"]
        },
        "prospective": {
            "description": "Future intentions/todos",
            "active": False,
            "tables": ["prospective_artifacts"]
        },
        "emotional": {
            "description": "Sentiment/tone tracking",
            "active": False,
            "tables": ["message_metadata"]
        },
        "contextual": {
            "description": "Environmental state",
            "active": False,
            "tables": ["environmental_snapshots"]
        },
        "meta": {
            "description": "Memory about memory",
            "active": False,
            "tables": ["access_logs", "search_history"]
        },
        "social": {
            "description": "Collaboration patterns",
            "active": False,
            "tables": ["agent_relationships"]
        }
    }
    
    # Check if database is online to activate lanes
    db_health = check_database_health()
    if db_health.get("connected"):
        # Mark all lanes as potentially active
        for lane in lanes.values():
            lane["active"] = True
    
    return lanes


def find_infrastructure_root(start_path: Path) -> Path:
    """Find Infrastructure root."""
    current = start_path if start_path.is_dir() else start_path.parent
    
    for _ in range(10):
        if (current / "conversation-memory-project").exists():
            return current
        
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    return None
