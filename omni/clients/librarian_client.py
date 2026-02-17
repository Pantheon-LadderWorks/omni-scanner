"""
Librarian Client - Omni interface for Grand Librarian workflows

Wraps Omni scanner orchestration for the 7 Librarian Workflows:
1. Census - Survey library (static/discovery scanners)
2. Categorize - Taxonomy classification (semantic matching)
3. Deduplicate - Find duplicates (hash-based detection)
4. Organize - Module sovereignty (cohesion analysis)
5. Catalog - Metadata index (git/phoenix/health)
6. Archive - Empty folders & behavioral analysis
7. Validate - Health checks & drift detection

"A librarian doesn't count every book by hand. She uses scanners." - Infrastructure, 2026
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger("Omni.Clients.Librarian")


class LibrarianClient:
    """
    High-level interface for Grand Librarian to trigger Omni scanner orchestration.
    
    The Librarian should NEVER directly implement scanning logic.
    The Librarian should ONLY call this client to orchestrate Omni scanners.
    
    Pattern: Librarian defines WHAT to organize, Omni defines HOW to scan.
    """
    
    def __init__(self, omni_root: Optional[Path] = None):
        """
        Initialize Librarian client.
        
        Args:
            omni_root: Path to Omni root (defaults to auto-detect)
        """
        self.omni_root = omni_root or self._find_omni_root()
        
    def _find_omni_root(self) -> Path:
        """Auto-detect Omni installation."""
        # Try common locations
        candidates = [
            Path(__file__).parent.parent.parent,  # tools/omni/omni/clients -> tools/omni
            Path.cwd() / "tools" / "omni",
            Path.home() / "Infrastructure" / "tools" / "omni",
        ]
        
        for candidate in candidates:
            if (candidate / "omni").exists():
                return candidate
        
        # Fallback
        return Path(__file__).parent.parent.parent
    
    # ========================================================================
    # 1. CENSUS - Survey the Library
    # ========================================================================
    
    def census(
        self,
        target: Path,
        pattern: str = "**/*",
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Survey library using static/discovery scanners.
        
        Scanners used:
        - static/inventory - File listing with metadata
        - discovery/canon - Canon detection
        - discovery/project - Project structure detection
        
        Args:
            target: Directory to scan
            pattern: File pattern (default: **/* for all files)
            include_metadata: Include file metadata (size, mtime, etc.)
        
        Returns:
            Dict with census results
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"📊 Census: Surveying {target}")
            
            results = {}
            
            # Static inventory
            if "static/inventory" in SCANNERS or "inventory" in SCANNERS:
                scanner_name = "static/inventory" if "static/inventory" in SCANNERS else "inventory"
                logger.info(f"   Running {scanner_name}...")
                results["inventory"] = SCANNERS[scanner_name](str(target), pattern=pattern)
            
            # Canon detection
            if "discovery/canon" in SCANNERS or "canon" in SCANNERS:
                scanner_name = "discovery/canon" if "discovery/canon" in SCANNERS else "canon"
                logger.info(f"   Running {scanner_name}...")
                results["canon"] = SCANNERS[scanner_name](str(target))
            
            # Project structure
            if "discovery/project" in SCANNERS or "project" in SCANNERS:
                scanner_name = "discovery/project" if "discovery/project" in SCANNERS else "project"
                logger.info(f"   Running {scanner_name}...")
                results["project"] = SCANNERS[scanner_name](str(target))
            
            # Aggregate file count
            total_files = 0
            if "inventory" in results:
                total_files = results["inventory"].get("file_count", 0)
            
            return {
                "success": True,
                "operation": "census",
                "target": str(target),
                "total_files": total_files,
                "scanners_run": list(results.keys()),
                "results": results,
            }
            
        except Exception as e:
            logger.error(f"Census failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "census",
            }
    
    # ========================================================================
    # 2. CATEGORIZE - Taxonomy Classification
    # ========================================================================
    
    def categorize(
        self,
        files: List[Path],
        taxonomy: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Classify files using content scanner (ACE's cognitive layer).
        
        Scanners used:
        - library/content - Deep read with keyword sampling
        
        Args:
            files: List of files to categorize
            taxonomy: Taxonomy dict (keyword_sets - optional)
        
        Returns:
            Dict with categorization results
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"🏷️ Categorize: Classifying {len(files)} files")
            
            scanner_name = "library/content" if "library/content" in SCANNERS else "content"
            
            if scanner_name not in SCANNERS:
                logger.warning("content scanner not available")
                return {
                    "success": False,
                    "operation": "categorize",
                    "reason": "content scanner not found",
                }
            
            # Run content scanner with taxonomy keyword sets
            logger.info(f"   Running {scanner_name}...")
            
            # Convert file list to target directory (scan parent)
            target = files[0].parent if files else Path.cwd()
            
            result = SCANNERS[scanner_name](
                str(target),
                keyword_sets=taxonomy,
            )
            
            keyword_distribution = result.get("keyword_distribution", {})
            
            return {
                "success": True,
                "operation": "categorize",
                "files_analyzed": result.get("text_files", 0),
                "keyword_distribution": keyword_distribution,
                "results": result,
            }
            
        except Exception as e:
            logger.error(f"Categorize failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "categorize",
            }
    
    # ========================================================================
    # 3. DEDUPLICATE - Find Duplicates
    # ========================================================================
    
    def deduplicate(
        self,
        target: Path,
        algorithm: str = "hash",
    ) -> Dict[str, Any]:
        """
        Find duplicate files using hash-based detection.
        
        Scanners used:
        - static/duplicates - SHA256 hash-based duplicate detection
        
        Args:
            target: Directory to scan
            algorithm: Deduplication algorithm (default: hash)
        
        Returns:
            Dict with deduplication results
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"🔍 Deduplicate: Scanning {target}")
            
            scanner_name = "static/duplicates" if "static/duplicates" in SCANNERS else "duplicates"
            
            if scanner_name not in SCANNERS:
                logger.warning("duplicates scanner not available")
                return {
                    "success": False,
                    "operation": "deduplicate",
                    "reason": "duplicates scanner not found",
                }
            
            logger.info(f"   Running {scanner_name}...")
            result = SCANNERS[scanner_name](str(target))
            
            duplicate_groups = result.get("duplicate_groups", [])
            total_duplicates = sum(len(group["files"]) - 1 for group in duplicate_groups)
            
            return {
                "success": True,
                "operation": "deduplicate",
                "target": str(target),
                "duplicate_groups": len(duplicate_groups),
                "total_duplicates": total_duplicates,
                "results": result,
            }
            
        except Exception as e:
            logger.error(f"Deduplicate failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "deduplicate",
            }
    
    # ========================================================================
    # 4. ORGANIZE - Module Sovereignty (Cohesion Analysis)
    # ========================================================================
    
    def organize(
        self,
        target: Path,
        min_cohesion: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Analyze folder cohesion to distinguish modules from dump grounds.
        
        Scanners used:
        - library/cohesion - ACE's sovereignty detection
        
        Args:
            target: Directory to scan
            min_cohesion: Minimum cohesion score for modules (default: 0.6)
        
        Returns:
            Dict with cohesion analysis
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"🧬 Organize: Analyzing cohesion in {target}")
            
            scanner_name = "library/cohesion" if "library/cohesion" in SCANNERS else "cohesion"
            
            if scanner_name not in SCANNERS:
                logger.warning("cohesion scanner not available")
                return {
                    "success": False,
                    "operation": "organize",
                    "reason": "cohesion scanner not found",
                }
            
            logger.info(f"   Running {scanner_name}...")
            result = SCANNERS[scanner_name](str(target), min_cohesion=min_cohesion)
            
            return {
                "success": True,
                "operation": "organize",
                "target": str(target),
                "modules_found": result.get("modules_found", 0),
                "sovereign_modules": result.get("sovereign_modules", 0),
                "dump_grounds": result.get("dump_grounds", 0),
                "avg_cohesion": result.get("avg_cohesion", 0.0),
                "results": result,
            }
            
        except Exception as e:
            logger.error(f"Organize failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "organize",
            }
    
    # ========================================================================
    # 5. CATALOG - Metadata Index
    # ========================================================================
    
    def catalog(
        self,
        target: Path,
        include_git: bool = True,
        include_phoenix: bool = True,
    ) -> Dict[str, Any]:
        """
        Build metadata index using git/phoenix/health scanners.
        
        Scanners used:
        - git/* - Version control metadata (authors, commits, branches)
        - phoenix/* - Resurrection data (snapshots, recovery points)
        - health/* - Health metrics (staleness, drift)
        
        Args:
            target: Directory to scan
            include_git: Include git metadata (default: True)
            include_phoenix: Include phoenix data (default: True)
        
        Returns:
            Dict with catalog metadata
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"📚 Catalog: Building metadata index for {target}")
            
            results = {}
            
            # Git metadata
            if include_git:
                for scanner in ["git/authors", "git/commits", "git/repos"]:
                    if scanner in SCANNERS:
                        logger.info(f"   Running {scanner}...")
                        results[scanner] = SCANNERS[scanner](str(target))
            
            # Phoenix data
            if include_phoenix:
                for scanner in ["phoenix/snapshots", "phoenix/ledger", "phoenix/archive_scanner"]:
                    if scanner in SCANNERS:
                        logger.info(f"   Running {scanner}...")
                        results[scanner] = SCANNERS[scanner](str(target))
            
            # Health metrics
            for scanner in ["health/staleness", "health/drift"]:
                if scanner in SCANNERS:
                    logger.info(f"   Running {scanner}...")
                    results[scanner] = SCANNERS[scanner](str(target))
            
            return {
                "success": True,
                "operation": "catalog",
                "target": str(target),
                "scanners_run": list(results.keys()),
                "results": results,
            }
            
        except Exception as e:
            logger.error(f"Catalog failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "catalog",
            }
    
    # ========================================================================
    # 6. ARCHIVE - Empty Folders & Behavioral Analysis
    # ========================================================================
    
    def archive(
        self,
        target: Path,
        find_empty: bool = True,
    ) -> Dict[str, Any]:
        """
        Identify archive candidates (empty folders, ghosts, cleanup targets).
        
        Scanners used:
        - library/empty_folders - Empty folder detection
        
        Args:
            target: Directory to scan
            find_empty: Find empty folders (default: True)
        
        Returns:
            Dict with archive analysis
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"📦 Archive: Scanning for archive candidates in {target}")
            
            results = {}
            
            # Empty folders
            if find_empty:
                scanner_name = "library/empty_folders" if "library/empty_folders" in SCANNERS else "empty_folders"
                if scanner_name in SCANNERS:
                    logger.info(f"   Running {scanner_name}...")
                    results["empty_folders"] = SCANNERS[scanner_name](str(target))
            
            total_empty = 0
            if "empty_folders" in results:
                total_empty = results["empty_folders"].get("total_empty", 0)
            
            return {
                "success": True,
                "operation": "archive",
                "target": str(target),
                "total_empty_folders": total_empty,
                "scanners_run": list(results.keys()),
                "results": results,
            }
            
        except Exception as e:
            logger.error(f"Archive failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "archive",
            }
    
    # ========================================================================
    # 7. VALIDATE - Health Check
    # ========================================================================
    
    def validate(
        self,
        target: Path,
    ) -> Dict[str, Any]:
        """
        Health check the library using drift/staleness/health scanners.
        
        Scanners used:
        - health/drift - Detect configuration drift
        - health/staleness - Find stale files
        - health/registry_sync - Check registry synchronization
        
        Args:
            target: Directory to validate
        
        Returns:
            Dict with validation report
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"✅ Validate: Health check for {target}")
            
            results = {}
            
            # Run all health scanners
            for scanner in ["health/drift", "health/staleness", "health/registry_sync"]:
                if scanner in SCANNERS:
                    logger.info(f"   Running {scanner}...")
                    results[scanner] = SCANNERS[scanner](str(target))
            
            # Aggregate health score (placeholder - actual logic in health scanners)
            health_score = 100.0
            issues_found = sum(len(r.get("issues", [])) for r in results.values())
            
            return {
                "success": True,
                "operation": "validate",
                "target": str(target),
                "health_score": health_score,
                "issues_found": issues_found,
                "scanners_run": list(results.keys()),
                "results": results,
            }
            
        except Exception as e:
            logger.error(f"Validate failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "validate",
            }
    
    # ========================================================================
    # ORCHESTRATION - Full Librarian Pipeline
    # ========================================================================
    
    def analyze_content(
        self,
        target: Path,
        taxonomy: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Deep read content with keyword sampling (ACE's cognitive layer).
        
        Scanners used:
        - library/content - Frontmatter, keywords, shebang
        
        Args:
            target: Directory to scan
            taxonomy: Custom keyword sets (optional)
        
        Returns:
            Dict with content analysis
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"👁️ Analyze Content: Deep read {target}")
            
            scanner_name = "library/content" if "library/content" in SCANNERS else "content"
            
            if scanner_name not in SCANNERS:
                logger.warning("content scanner not available")
                return {
                    "success": False,
                    "operation": "analyze_content",
                    "reason": "content scanner not found",
                }
            
            logger.info(f"   Running {scanner_name}...")
            result = SCANNERS[scanner_name](str(target), keyword_sets=taxonomy)
            
            return {
                "success": True,
                "operation": "analyze_content",
                "target": str(target),
                "text_files": result.get("text_files", 0),
                "files_with_frontmatter": result.get("files_with_frontmatter", 0),
                "keyword_distribution": result.get("keyword_distribution", {}),
                "results": result,
            }
            
        except Exception as e:
            logger.error(f"Analyze content failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "analyze_content",
            }
    
    def analyze_graph(
        self,
        target: Path,
    ) -> Dict[str, Any]:
        """
        Extract knowledge graph (links, imports, dependencies).
        
        Scanners used:
        - library/graph - Link extraction, broken link detection
        
        Args:
            target: Directory to scan
        
        Returns:
            Dict with graph analysis
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"🕸️ Analyze Graph: Mapping connections in {target}")
            
            scanner_name = "library/graph" if "library/graph" in SCANNERS else "graph"
            
            if scanner_name not in SCANNERS:
                logger.warning("graph scanner not available")
                return {
                    "success": False,
                    "operation": "analyze_graph",
                    "reason": "graph scanner not found",
                }
            
            logger.info(f"   Running {scanner_name}...")
            result = SCANNERS[scanner_name](str(target))
            
            return {
                "success": True,
                "operation": "analyze_graph",
                "target": str(target),
                "total_links": result.get("total_links", 0),
                "total_imports": result.get("total_imports", 0),
                "broken_links": result.get("total_broken_links", 0),
                "graph_edges": result.get("graph_edges", {}),
                "results": result,
            }
            
        except Exception as e:
            logger.error(f"Analyze graph failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "analyze_graph",
            }
    
    def analyze_rituals(
        self,
        target: Path,
    ) -> Dict[str, Any]:
        """
        Detect CodeCraft rituals and classify by Arcane School.
        
        Scanners used:
        - library/rituals - Ritual blocks, invocations, school detection
        
        Args:
            target: Directory to scan
        
        Returns:
            Dict with ritual analysis
        """
        try:
            from omni.scanners import SCANNERS
            
            logger.info(f"🔮 Analyze Rituals: Detecting CodeCraft in {target}")
            
            scanner_name = "library/rituals" if "library/rituals" in SCANNERS else "rituals"
            
            if scanner_name not in SCANNERS:
                logger.warning("rituals scanner not available")
                return {
                    "success": False,
                    "operation": "analyze_rituals",
                    "reason": "rituals scanner not found",
                }
            
            logger.info(f"   Running {scanner_name}...")
            result = SCANNERS[scanner_name](str(target))
            
            return {
                "success": True,
                "operation": "analyze_rituals",
                "target": str(target),
                "codecraft_files": result.get("codecraft_files", 0),
                "ritual_blocks": result.get("ritual_blocks", 0),
                "school_distribution": result.get("school_distribution", {}),
                "results": result,
            }
            
        except Exception as e:
            logger.error(f"Analyze rituals failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "analyze_rituals",
            }
    
    # ========================================================================
    # ORCHESTRATION - Full Librarian Pipeline
    # ========================================================================
    
    def full_library_pipeline(
        self,
        target: Path,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Run complete 7-workflow librarian pipeline.
        
        Workflows:
        1. Census → 2. Categorize → 3. Deduplicate →
        4. Organize → 5. Catalog → 6. Archive → 7. Validate
        
        Args:
            target: Directory to organize
            dry_run: Preview without executing (default: True)
        
        Returns:
            Dict with full pipeline results
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would run full librarian pipeline on {target}")
            return {
                "success": True,
                "dry_run": True,
                "operation": "full_pipeline",
                "target": str(target),
                "workflows": [
                    "census", "categorize", "deduplicate",
                    "organize", "catalog", "archive", "validate"
                ],
            }
        
        try:
            logger.info(f"🌌 Full Librarian Pipeline: {target}")
            
            results = {}
            
            # 1. Census
            logger.info("\n1️⃣ CENSUS (Physical Inventory)")
            results["census"] = self.census(target)
            
            # 2. Content Analysis (ACE's Cognitive Layer - The Eyes)
            logger.info("\n2️⃣ CONTENT ANALYSIS (Deep Read)")
            results["content"] = self.analyze_content(target)
            
            # 3. Graph Analysis (ACE's Cognitive Layer - The Nerves)
            logger.info("\n3️⃣ GRAPH ANALYSIS (Link Extraction)")
            results["graph"] = self.analyze_graph(target)
            
            # 4. Ritual Analysis (ACE's Cognitive Layer - The Arcane Eye)
            logger.info("\n4️⃣ RITUAL ANALYSIS (CodeCraft Detection)")
            results["rituals"] = self.analyze_rituals(target)
            
            # 5. Categorize (now uses content scanner)
            logger.info("\n5️⃣ CATEGORIZE (Taxonomy Classification)")
            results["categorize"] = self.categorize([], None)  # Uses content results
            
            # 6. Deduplicate
            logger.info("\n6️⃣ DEDUPLICATE (Hash Detection)")
            results["deduplicate"] = self.deduplicate(target)
            
            # 7. Organize
            logger.info("\n7️⃣ ORGANIZE (Cohesion Analysis)")
            results["organize"] = self.organize(target)
            
            # 8. Catalog
            logger.info("\n8️⃣ CATALOG (Metadata Index)")
            results["catalog"] = self.catalog(target)
            
            # 9. Archive
            logger.info("\n9️⃣ ARCHIVE (Empty Folders)")
            results["archive"] = self.archive(target)
            
            # 10. Validate
            logger.info("\n🔟 VALIDATE (Health Check)")
            results["validate"] = self.validate(target)
            
            logger.info("\n✨ Full pipeline complete!")
            logger.info("📊 Physical Layer: census, deduplicate, organize, catalog, archive, validate")
            logger.info("🧠 Cognitive Layer: content, graph, rituals, categorize")
            
            return {
                "success": True,
                "dry_run": False,
                "operation": "full_pipeline",
                "target": str(target),
                "workflows": results,
                "ace_architecture": {
                    "physical_layer": ["census", "deduplicate", "organize", "catalog", "archive", "validate"],
                    "cognitive_layer": ["content", "graph", "rituals", "categorize"],
                }
            }
            
        except Exception as e:
            logger.error(f"Full pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "full_pipeline",
            }
