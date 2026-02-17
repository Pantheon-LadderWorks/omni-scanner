"""
CMP Entities Scanner
====================
Scans entity_mentions table in CMP database (for knowledge graph).

Hybrid Approach:
- Backend: GET /api/entities
- SQL: SELECT DISTINCT entity_name, entity_type, COUNT(*) FROM entity_mentions
"""
from pathlib import Path
from typing import Dict, Any
from .base_db_scanner import BaseDatabaseScanner


def scan(target: Path, entity_type: str = None, limit: int = 100) -> Dict[str, Any]:
    """
    Scan entities (knowledge graph nodes) in CMP database.
    
    Args:
        target: Path to Infrastructure root
        entity_type: Optional entity type to filter by (e.g., "AGENT", "PROJECT", "STATION")
        limit: Maximum entities to return (default: 100)
    
    Returns:
        {
            "count": int,
            "items": [{"entity_name": str, "entity_type": str, "mention_count": int}],
            "metadata": {"scanner": "cmp_entities", "source": "BACKEND|SQL"}
        }
    """
    scanner = BaseDatabaseScanner(target)
    
    # Backend endpoint with params
    backend_endpoint = "/api/entities"
    backend_params = {}
    if entity_type:
        backend_params["entity_type"] = entity_type
    if limit:
        backend_params["limit"] = limit
    
    # SQL fallback query
    if entity_type:
        sql_query = f"""
            SELECT 
                entity_name,
                entity_type,
                COUNT(*) as mention_count
            FROM entity_mentions
            WHERE entity_type = '{entity_type}'
            GROUP BY entity_name, entity_type
            ORDER BY mention_count DESC
            LIMIT {limit}
        """
    else:
        sql_query = f"""
            SELECT 
                entity_name,
                entity_type,
                COUNT(*) as mention_count
            FROM entity_mentions
            GROUP BY entity_name, entity_type
            ORDER BY mention_count DESC
            LIMIT {limit}
        """
    
    def transform_entity(item: Dict) -> Dict:
        """Transform entity data to canonical format."""
        return {
            "entity_name": item.get("entity_name"),
            "entity_type": item.get("entity_type"),
            "mention_count": int(item.get("mention_count", 0)),
        }
    
    results = scanner.scan_hybrid(
        backend_endpoint=backend_endpoint,
        sql_query=sql_query,
        backend_params=backend_params,
        transform_fn=transform_entity
    )
    
    results["metadata"]["scanner"] = "cmp_entities"
    results["summary"] = {
        "total_entities": results["count"],
        "filtered_by_type": entity_type is not None,
        "limit_applied": limit,
        "by_entity_type": {},
        "total_mentions": sum(e.get("mention_count", 0) for e in results["items"])
    }
    
    # Count by entity type
    for entity in results["items"]:
        etype = entity.get("entity_type", "UNKNOWN")
        results["summary"]["by_entity_type"][etype] = \
            results["summary"]["by_entity_type"].get(etype, 0) + 1
    
    return results


if __name__ == "__main__":
    # Standalone test
    from pathlib import Path
    infra_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    result = scan(infra_root, limit=50)
    
    print(f"\n{'='*60}")
    print(f"CMP Entities Scanner Test")
    print(f"{'='*60}")
    print(f"Source: {result['metadata'].get('source', 'UNKNOWN')}")
    print(f"Total Entities: {result['count']}")
    print(f"Total Mentions: {result['summary']['total_mentions']}")
    print(f"\nBy Entity Type:")
    for etype, count in result['summary']['by_entity_type'].items():
        print(f"  {etype}: {count}")
    
    if result["items"]:
        print(f"\nTop 10 Most Mentioned Entities:")
        for entity in result["items"][:10]:
            print(f"  {entity['entity_name']} ({entity['entity_type']}) - {entity['mention_count']} mentions")
