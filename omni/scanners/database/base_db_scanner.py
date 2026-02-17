"""
Base Database Scanner
=====================
Hybrid backend/SQL approach for CMP database access.

Architecture:
1. Try FastAPI backend first (http://127.0.0.1:8000)
2. Fall back to direct PostgreSQL if backend is down
3. Use federation_heart for path and env resolution

NOTE: All DB calls are SYNCHRONOUS (psycopg2) so this works
inside MCP event loops, CLI, or any other context.
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger("Omni.Scanner.DB")

# Import federation_heart pillars (pip installed as seraphina-federation)
try:
    from federation_heart.pillars.cartography import CartographyPillar
    from federation_heart.pillars.constitution import ConstitutionPillar
    HEART_AVAILABLE = True
except ImportError:
    HEART_AVAILABLE = False


class BaseDatabaseScanner:
    """
    Base class for all database scanners.
    
    Implements:
    - Backend connectivity (FastAPI)
    - Database connectivity (PostgreSQL)
    - Hybrid fallback logic
    - Environment resolution (via ConstitutionPillar)
    - Path resolution (via CartographyPillar)
    """
    
    def __init__(self, infra_root: Path = None):
        # Find Infrastructure root if not provided
        if infra_root is None:
            current = Path.cwd()
            while current != current.parent:
                if (current / "governance").exists() and (current / "agents").exists():
                    infra_root = current
                    break
                current = current.parent
            
            if infra_root is None:
                infra_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        
        self.infra_root = infra_root
        self.backend_url = None
        self.db_url = None
        self._cartography = None
        self._constitution = None
        
        # Initialize pillars if available
        if HEART_AVAILABLE:
            self._cartography = CartographyPillar(self.infra_root)
            self._constitution = ConstitutionPillar(self.infra_root, self._cartography)
            
            # Load environment
            if self._constitution.status().get("env", {}).get("loaded"):
                self.backend_url = self._constitution.env.get("CMP_BACKEND_URL", "http://127.0.0.1:8000")
                self.db_url = self._build_db_url()
        
        # Fallback to defaults
        if not self.backend_url:
            self.backend_url = "http://127.0.0.1:8000"
        if not self.db_url:
            self.db_url = "postgresql://postgres:58913070Krdpn!!@localhost:5433/cms_db"
    
    def _build_db_url(self) -> str:
        """Build PostgreSQL connection URL from env vars."""
        env = self._constitution.env
        host = env.get("CMP_DB_HOST", "localhost")
        port = env.get("CMP_DB_PORT", "5433")
        database = env.get("CMP_DB_NAME", "cms_db")
        user = env.get("CMP_DB_USER", "postgres")
        password = env.get("CMP_DB_PASSWORD", "58913070Krdpn!!")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def check_backend(self) -> bool:
        """Check if FastAPI backend is accessible."""
        try:
            import httpx
            # Try multiple health endpoints (FastAPI sometimes uses different paths)
            for endpoint in ["/api/health", "/health", "/"]:
                try:
                    response = httpx.get(f"{self.backend_url}{endpoint}", timeout=2)
                    if response.status_code == 200:
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False
    
    def query_backend(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Query FastAPI backend (synchronous).
        
        Args:
            endpoint: API endpoint (e.g., "/projects", "/agents")
            params: Query parameters
        
        Returns:
            Response JSON or None if failed
        """
        try:
            import httpx
            url = f"{self.backend_url}{endpoint}"
            response = httpx.get(url, params=params or {}, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.debug(f"Backend query failed: {e}")
            return None
    
    def query_sql(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """
        Query PostgreSQL database directly (synchronous via psycopg2).
        
        Args:
            query: SQL query string
            params: Query parameters (tuple)
        
        Returns:
            List of row dicts or None if failed
        """
        try:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(self.db_url, connect_timeout=5)
            
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            logger.debug(f"SQL query failed: {e}")
            return None
    
    def scan_hybrid(
        self,
        backend_endpoint: str,
        sql_query: str,
        backend_params: Dict = None,
        sql_params: tuple = None,
        transform_fn = None
    ) -> Dict[str, Any]:
        """
        Hybrid scan: Try backend first, fall back to SQL.
        
        All calls are synchronous — safe inside MCP event loops.
        
        Args:
            backend_endpoint: API endpoint to query
            sql_query: SQL query to fall back to
            backend_params: Query params for backend
            sql_params: Query params for SQL
            transform_fn: Optional function to transform results
        
        Returns:
            Standardized scanner result dict
        """
        results = {
            "count": 0,
            "items": [],
            "metadata": {
                "scanner": "database_hybrid",
                "source": "UNKNOWN"
            }
        }
        
        # Try backend first
        if self.check_backend():
            try:
                data = self.query_backend(backend_endpoint, backend_params)
                if data:
                    items = data if isinstance(data, list) else [data]
                    if transform_fn:
                        items = [transform_fn(item) for item in items]
                    results["items"] = items
                    results["count"] = len(items)
                    results["metadata"]["source"] = "BACKEND"
                    return results
            except Exception as e:
                logger.warning(f"Backend scan failed, falling back to SQL: {e}")
        
        # Fall back to SQL (synchronous psycopg2)
        try:
            rows = self.query_sql(sql_query, sql_params)
            if rows:
                items = rows
                if transform_fn:
                    items = [transform_fn(item) for item in items]
                results["items"] = items
                results["count"] = len(items)
                results["metadata"]["source"] = "SQL"
                return results
        except Exception as e:
            results["metadata"]["error"] = f"Both backend and SQL failed: {e}"
        
        return results
    
    def get_cmp_path(self) -> Optional[Path]:
        """Get path to conversation-memory-project using Cartography."""
        if not self._cartography:
            # Fallback: Manual path resolution
            cmp_path = self.infra_root / "conversation-memory-project"
            return cmp_path if cmp_path.exists() else None
        
        # Use Cartography to resolve
        return self._cartography.resolve_path("conversation-memory-project")
