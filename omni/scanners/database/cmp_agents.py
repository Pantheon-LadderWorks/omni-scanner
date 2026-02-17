"""
CMP Agents Scanner
==================
Scans agents table in CMP database.

Hybrid Approach:
- Backend: GET /api/agents
- SQL: SELECT id, name, key, role FROM agents

NOTE: Agents may also exist in COUNCIL_UUID_REGISTRY.yaml (file-based source of truth).
This scanner focuses on database records only.
"""
from pathlib import Path
from typing import Dict, Any
from .base_db_scanner import BaseDatabaseScanner


def scan(target: Path) -> Dict[str, Any]:
    """
    Scan all agents in CMP database.
    
    Args:
        target: Path to Infrastructure root
    
    Returns:
        {
            "count": int,
            "items": [{"uuid": str, "name": str, "key": str, "role": str, ...}],
            "metadata": {"scanner": "cmp_agents", "source": "BACKEND|SQL"}
        }
    """
    scanner = BaseDatabaseScanner(target)
    
    # Backend endpoint
    backend_endpoint = "/api/agents"
    
    # SQL fallback query
    sql_query = """
        SELECT 
            id,
            name,
            kind,
            role,
            metadata_->>'clearance_tier' as clearance_tier,
            metadata_->>'twin_bond' as twin_bond
        FROM agents
        ORDER BY name
    """
    
    def transform_agent(item: Dict) -> Dict:
        """Transform agent data to canonical format."""
        return {
            "uuid": item.get("id"),
            "name": item.get("name"),
            "kind": item.get("kind"),
            "role": item.get("role"),
            "clearance_tier": item.get("clearance_tier"),
            "twin_bond": item.get("twin_bond"),
        }
    
    results = scanner.scan_hybrid(
        backend_endpoint=backend_endpoint,
        sql_query=sql_query,
        transform_fn=transform_agent
    )
    
    results["metadata"]["scanner"] = "cmp_agents"
    results["summary"] = {
        "total_agents": results["count"],
        "council_members": sum(1 for a in results["items"] if a.get("role") == "COUNCIL"),
        "by_role": {}
    }
    
    # Count by role
    for agent in results["items"]:
        role = agent.get("role", "UNKNOWN")
        results["summary"]["by_role"][role] = results["summary"]["by_role"].get(role, 0) + 1
    
    return results


if __name__ == "__main__":
    # Standalone test
    from pathlib import Path
    infra_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    result = scan(infra_root)
    
    print(f"\n{'='*60}")
    print(f"CMP Agents Scanner Test")
    print(f"{'='*60}")
    print(f"Source: {result['metadata'].get('source', 'UNKNOWN')}")
    print(f"Total Agents: {result['count']}")
    print(f"Council Members: {result['summary']['council_members']}")
    print(f"\nBy Role:")
    for role, count in result['summary']['by_role'].items():
        print(f"  {role}: {count}")
    
    if result["items"]:
        print(f"\nAll Agents:")
        for agent in result["items"]:
            kind = agent.get('kind', 'UNKNOWN')
            print(f"  {agent['name']} ({kind}) - {agent['role']} - {agent['uuid']}")
