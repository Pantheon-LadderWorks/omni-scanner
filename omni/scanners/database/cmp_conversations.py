"""
CMP Conversations Scanner
=========================
Scans conversations table in CMP database.

Hybrid Approach:
- Backend: GET /api/conversations
- SQL: SELECT id, title, project_id, created_at FROM conversations
"""
from pathlib import Path
from typing import Dict, Any
from .base_db_scanner import BaseDatabaseScanner


def scan(target: Path, project_id: str = None, limit: int = 100) -> Dict[str, Any]:
    """
    Scan conversations in CMP database.
    
    Args:
        target: Path to Infrastructure root
        project_id: Optional project UUID to filter by
        limit: Maximum conversations to return (default: 100)
    
    Returns:
        {
            "count": int,
            "items": [{"uuid": str, "title": str, "project_id": str, ...}],
            "metadata": {"scanner": "cmp_conversations", "source": "BACKEND|SQL"}
        }
    """
    scanner = BaseDatabaseScanner(target)
    
    # Backend endpoint with params
    backend_endpoint = "/api/conversations"
    backend_params = {}
    if project_id:
        backend_params["project_id"] = project_id
    if limit:
        backend_params["limit"] = limit
    
    # SQL fallback query
    if project_id:
        sql_query = f"""
            SELECT 
                id,
                title,
                project_id,
                session_tag,
                domain,
                status,
                start_time,
                end_time
            FROM conversations
            WHERE project_id = '{project_id}'
            ORDER BY start_time DESC
            LIMIT {limit}
        """
    else:
        sql_query = f"""
            SELECT 
                id,
                title,
                project_id,
                session_tag,
                domain,
                status,
                start_time,
                end_time
            FROM conversations
            ORDER BY start_time DESC
            LIMIT {limit}
        """
    
    def transform_conversation(item: Dict) -> Dict:
        """Transform conversation data to canonical format."""
        return {
            "uuid": item.get("id"),
            "title": item.get("title"),
            "project_id": item.get("project_id"),
            "session_tag": item.get("session_tag"),
            "domain": item.get("domain"),
            "status": item.get("status"),
            "start_time": str(item.get("start_time")) if item.get("start_time") else None,
            "end_time": str(item.get("end_time")) if item.get("end_time") else None,
        }
    
    results = scanner.scan_hybrid(
        backend_endpoint=backend_endpoint,
        sql_query=sql_query,
        backend_params=backend_params,
        transform_fn=transform_conversation
    )
    
    results["metadata"]["scanner"] = "cmp_conversations"
    results["summary"] = {
        "total_conversations": results["count"],
        "filtered_by_project": project_id is not None,
        "limit_applied": limit,
        "by_project": {}
    }
    
    # Count by project
    for conv in results["items"]:
        proj_id = conv.get("project_id", "UNKNOWN")
        results["summary"]["by_project"][proj_id] = results["summary"]["by_project"].get(proj_id, 0) + 1
    
    return results


if __name__ == "__main__":
    # Standalone test
    from pathlib import Path
    infra_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    result = scan(infra_root, limit=20)
    
    print(f"\n{'='*60}")
    print(f"CMP Conversations Scanner Test")
    print(f"{'='*60}")
    print(f"Source: {result['metadata'].get('source', 'UNKNOWN')}")
    print(f"Total Conversations: {result['count']}")
    print(f"\nBy Project (Top 5):")
    sorted_projects = sorted(
        result['summary']['by_project'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    for proj_id, count in sorted_projects:
        print(f"  {proj_id}: {count}")
    
    if result["items"]:
        print(f"\nRecent 5 Conversations:")
        for conv in result["items"][:5]:
            print(f"  {conv['title']} - {conv['created_at']}")
