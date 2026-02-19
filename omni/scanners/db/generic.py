"""
Generic SQL Scanner
===================
Config-driven database scanner. READS from `omni/config/db/*.yaml`.

Schema:
  name: "project_db"
  description: "Scans project table"
  connection:
    type: "postgres"
    host: "localhost" # or ENV_VAR
    port: 5432
    user: "postgres"
    password: "password" # or ENV_VAR
    database: "mydb"
  queries:
    - name: "projects"
      sql: "SELECT * FROM projects"
      params: []
"""
import yaml
import os
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("omni.scanners.db")

def scan(target: Path, **options) -> Dict[str, Any]:
    """
    Main entry point for generic DB scanning.
    Iterates over all config files in `omni/config/db/` and runs defined queries.
    """
    results = {
        "count": 0,
        "items": [],
        "errors": []
    }
    
    # 1. Locate Configs
    # Try local config first
    config_dir = target / "omni" / "config" / "db"
    
    # Use global setting if available
    try:
        from omni.config import settings
        infra_root = settings.get_infrastructure_root()
        if infra_root:
             global_config = infra_root / "config" / "omni" / "db"
             if global_config.exists():
                 # Merge? or prefer? Let's treat them as additive.
                 pass
    except ImportError:
        pass

    # Fallback to package config (for templates/defaults)
    package_config = Path(__file__).parent.parent.parent / "config" / "db"
    
    config_files = []
    if config_dir.exists():
        config_files.extend(config_dir.glob("*.yaml"))
    if package_config.exists():
        config_files.extend(package_config.glob("*.yaml"))

    if not config_files:
        return results

    # 2. Iterate Configs
    for config_file in config_files:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config: continue
            
            # Execute Queries
            db_items = _execute_config(config)
            results["items"].extend(db_items)
            results["count"] += len(db_items)
            
        except Exception as e:
            results["errors"].append(f"{config_file.name}: {e}")
            logger.error(f"Failed to scan {config_file}: {e}")
            
    return results

def _execute_config(config: Dict) -> List[Dict]:
    """Execute SQL queries defined in a single config file."""
    items = []
    conn_info = config.get('connection', {})
    queries = config.get('queries', [])
    
    if not queries: return items
    
    # Resolver environment variables in connection info
    # e.g. password: ${DB_PASSWORD}
    resolved_conn = _resolve_env_vars(conn_info)
    
    try:
        # Import psycopg2 locally to avoid hard dependency at module level
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Build DSN
        dsn = f"host={resolved_conn.get('host', 'localhost')} " \
              f"port={resolved_conn.get('port', 5432)} " \
              f"dbname={resolved_conn.get('database', 'postgres')} " \
              f"user={resolved_conn.get('user', 'postgres')} " \
              f"password={resolved_conn.get('password', '')}"
        
        with psycopg2.connect(dsn) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for q in queries:
                    sql = q.get('sql')
                    params = q.get('params', ())
                    name = q.get('name', 'query')
                    
                    try:
                        cur.execute(sql, params)
                        rows = cur.fetchall()
                        
                        for row in rows:
                            # Add metadata
                            row['__source_query'] = name
                            row['__source_config'] = config.get('name', 'unknown')
                            items.append(row)
                            
                    except Exception as q_err:
                        logger.error(f"Query {name} failed: {q_err}")
                        items.append({"error": str(q_err), "query": name})
                        
    except ImportError:
        items.append({"error": "psycopg2 not installed", "config": config.get('name')})
    except Exception as e:
        items.append({"error": str(e), "config": config.get('name')})
        
    return items

def _resolve_env_vars(config_node: Any) -> Any:
    """Recursively resolve strings like ${VAR_NAME} from os.environ."""
    if isinstance(config_node, dict):
        return {k: _resolve_env_vars(v) for k, v in config_node.items()}
    elif isinstance(config_node, list):
        return [_resolve_env_vars(i) for i in config_node]
    elif isinstance(config_node, str) and config_node.startswith("${") and config_node.endswith("}"):
        var_name = config_node[2:-1]
        return os.environ.get(var_name, config_node) # Fallback to raw string if not set? Or empty?
    return config_node
