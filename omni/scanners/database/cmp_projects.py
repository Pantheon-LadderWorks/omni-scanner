"""
CMP Projects Scanner
===================
Scans projects table in CMP database.

Hybrid Approach:
- Backend: GET /api/v1/projects/
- SQL: SELECT id, name, key, metadata_ FROM projects
"""
from pathlib import Path
from typing import Dict, Any
from .base_db_scanner import BaseDatabaseScanner


def scan(target: Path) -> Dict[str, Any]:
    """
    Scan all projects in CMP database.
    
    Args:
        target: Path to Infrastructure root
    
    Returns:
        {
            "count": int,
            "items": [{"uuid": str, "name": str, "key": str, "github_url": str, ...}],
            "metadata": {"scanner": "cmp_projects", "source": "BACKEND|SQL"}
        }
    """
    scanner = BaseDatabaseScanner(target)
    
    # Backend endpoint (FIX: Use correct /api/v1/projects/ endpoint)
    backend_endpoint = "/api/v1/projects/"
    
    # SQL fallback query
    sql_query = """
        SELECT 
            id,
            name,
            key,
            type,
            status,
            metadata_->>'github_url' as github_url,
            metadata_->>'domain' as domain
        FROM projects
        ORDER BY name
    """
    
    def transform_project(item: Dict) -> Dict:
        """Transform project data to canonical format."""
        return {
            "uuid": item.get("id"),
            "name": item.get("name"),
            "key": item.get("key"),
            "type": item.get("type"),
            "status": item.get("status", "UNKNOWN"),
            "github_url": item.get("github_url"),
            "domain": item.get("domain"),
        }
    
    results = scanner.scan_hybrid(
        backend_endpoint=backend_endpoint,
        sql_query=sql_query,
        transform_fn=transform_project
    )
    
    results["metadata"]["scanner"] = "cmp_projects"
    results["summary"] = {
        "total_projects": results["count"],
        "with_github_url": sum(1 for p in results["items"] if p.get("github_url")),
        "by_domain": {}
    }
    
    # Count by domain
    for project in results["items"]:
        domain = project.get("domain", "UNKNOWN")
        results["summary"]["by_domain"][domain] = results["summary"]["by_domain"].get(domain, 0) + 1
    
    return results


if __name__ == "__main__":
    # Standalone test
    from pathlib import Path
    infra_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    result = scan(infra_root)
    
    print(f"\n{'='*60}")
    print(f"CMP Projects Scanner Test")
    print(f"{'='*60}")
    print(f"Source: {result['metadata'].get('source', 'UNKNOWN')}")
    print(f"Total Projects: {result['count']}")
    print(f"With GitHub URL: {result['summary']['with_github_url']}")
    print(f"\nBy Domain:")
    for domain, count in result['summary']['by_domain'].items():
        print(f"  {domain}: {count}")
    
    if result["items"]:
        print(f"\nFirst 5 Projects:")
        for proj in result["items"][:5]:
            print(f"  {proj['name']} ({proj['key']}) - {proj['uuid']}")
