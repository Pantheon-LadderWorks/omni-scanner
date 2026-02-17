"""
CMP Artifacts Scanner
=====================
Scans artifacts table in CMP database.

Hybrid Approach:
- Backend: GET /api/artifacts
- SQL: SELECT id, title, content_type, conversation_id FROM artifacts
"""
from pathlib import Path
from typing import Dict, Any
from .base_db_scanner import BaseDatabaseScanner


def scan(target: Path, conversation_id: str = None, limit: int = 100) -> Dict[str, Any]:
    """
    Scan artifacts in CMP database.
    
    Args:
        target: Path to Infrastructure root
        conversation_id: Optional conversation UUID to filter by
        limit: Maximum artifacts to return (default: 100)
    
    Returns:
        {
            "count": int,
            "items": [{"uuid": str, "title": str, "content_type": str, ...}],
            "metadata": {"scanner": "cmp_artifacts", "source": "BACKEND|SQL"}
        }
    """
    scanner = BaseDatabaseScanner(target)
    
    # Backend endpoint with params
    backend_endpoint = "/api/artifacts"
    backend_params = {}
    if conversation_id:
        backend_params["conversation_id"] = conversation_id
    if limit:
        backend_params["limit"] = limit
    
    # SQL fallback query (artifacts table has kind, not content_type)
    if conversation_id:
        sql_query = f"""
            SELECT 
                a.id,
                a.title,
                a.kind,
                a.project_id,
                a.status,
                a.created_at,
                ca.conversation_id
            FROM artifacts a
            LEFT JOIN conversation_artifacts ca ON a.id = ca.artifact_id
            WHERE ca.conversation_id = '{conversation_id}'
            ORDER BY a.created_at DESC
            LIMIT {limit}
        """
    else:
        sql_query = f"""
            SELECT 
                id,
                title,
                kind,
                project_id,
                status,
                created_at
            FROM artifacts
            ORDER BY created_at DESC
            LIMIT {limit}
        """
    
    def transform_artifact(item: Dict) -> Dict:
        """Transform artifact data to canonical format."""
        return {
            "uuid": item.get("id"),
            "title": item.get("title"),
            "kind": item.get("kind"),
            "project_id": item.get("project_id"),
            "conversation_id": item.get("conversation_id"),
            "status": item.get("status"),
            "created_at": str(item.get("created_at")) if item.get("created_at") else None,
        }
    
    results = scanner.scan_hybrid(
        backend_endpoint=backend_endpoint,
        sql_query=sql_query,
        backend_params=backend_params,
        transform_fn=transform_artifact
    )
    
    results["metadata"]["scanner"] = "cmp_artifacts"
    results["summary"] = {
        "total_artifacts": results["count"],
        "filtered_by_conversation": conversation_id is not None,
        "limit_applied": limit,
        "by_kind": {}
    }
    
    # Count by kind
    for artifact in results["items"]:
        kind = artifact.get("kind", "UNKNOWN")
        results["summary"]["by_kind"][kind] = \
            results["summary"]["by_kind"].get(kind, 0) + 1
    
    return results


if __name__ == "__main__":
    # Standalone test
    from pathlib import Path
    infra_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    result = scan(infra_root, limit=20)
    
    print(f"\n{'='*60}")
    print(f"CMP Artifacts Scanner Test")
    print(f"{'='*60}")
    print(f"Source: {result['metadata'].get('source', 'UNKNOWN')}")
    print(f"Total Artifacts: {result['count']}")
    print(f"\nBy Kind:")
    for kind, count in result['summary']['by_kind'].items():
        print(f"  {kind}: {count}")
    
    if result["items"]:
        print(f"\nRecent 5 Artifacts:")
        for artifact in result["items"][:5]:
            print(f"  {artifact['title']} ({artifact['kind']}) - {artifact['created_at']}")
