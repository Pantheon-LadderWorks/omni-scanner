"""
omni/pillars/intel.py
The Intel Pillar - The Brain
============================
Responsibility:
1.  AI analysis of scan results
2.  Document curation (librarian)
3.  Ecosystem understanding

Absorbs: core/brain.py, core/librarian.py
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("Omni.Pillar.Intel")


class IntelPillar:
    """
    The Intel Pillar - AI analysis and document curation.
    """
    
    def __init__(self, settings_module):
        self.settings = settings_module
        self.heart_available = self.settings.heart_available()
        
        # Lazy-loaded brain instance
        self._brain = None
        
        logger.info("🧠 Intel Pillar initialized")
    
    # =========================================================================
    # AI Analysis (from core/brain.py)
    # =========================================================================
    
    @property
    def brain(self):
        """Lazy-load the OmniBrain instance."""
        if self._brain is None:
            from omni.core.brain import get_brain
            self._brain = get_brain()
        return self._brain
    
    def analyze_scan(
        self, 
        scan_result: Dict[str, Any], 
        prompt: Optional[str] = None
    ) -> str:
        """
        Analyze scan results using AI.
        
        Args:
            scan_result: Results from any scan operation
            prompt: Optional custom analysis prompt
            
        Returns:
            AI-generated analysis string
        """
        logger.info("🧠 Analyzing scan results with AI...")
        return self.brain.analyze(scan_result, prompt=prompt)
    
    def explain_ecosystem(
        self,
        ecosystem_map: Dict[str, Any]
    ) -> str:
        """
        Generate a human-readable explanation of an ecosystem.
        
        Args:
            ecosystem_map: Output from ecosystem analysis
            
        Returns:
            Narrative explanation
        """
        prompt = (
            "Explain this ecosystem structure as if you're introducing "
            "a new developer to the codebase. Focus on:\n"
            "1. Key components and their relationships\n"
            "2. Technology choices and why they matter\n"
            "3. Entry points for different use cases\n"
            "4. Any architectural patterns you notice"
        )
        return self.brain.analyze(ecosystem_map, prompt=prompt)
    
    # =========================================================================
    # Document Curation (from core/librarian.py)
    # =========================================================================
    
    def curate_documents(
        self,
        census_items: List[Dict[str, Any]],
        templates: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform raw file census into curated library entries.
        
        Args:
            census_items: List of file info dicts from scan
            templates: Optional taxonomy templates
            
        Returns:
            List of curated LibraryEntry dicts
        """
        from omni.core.librarian import curate_entries_from_census
        from dataclasses import asdict
        
        if templates is None:
            templates = []
        
        entries = curate_entries_from_census(census_items, templates)
        
        # Convert dataclasses to dicts
        return [asdict(e) for e in entries]
    
    def export_instruction_registry(
        self,
        library_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Export library entries to INSTRUCTION_REGISTRY format.
        
        Args:
            library_entries: Curated library entries
            
        Returns:
            Registry dict ready for YAML export
        """
        from omni.core.librarian import export_to_instruction_registry, LibraryEntry
        
        # Convert dicts back to dataclasses
        entries = []
        for e in library_entries:
            # Handle the duplicates field default
            if e.get('duplicates') is None:
                e['duplicates'] = []
            if e.get('frontmatter') is None:
                e['frontmatter'] = {}
            entries.append(LibraryEntry(**e))
        
        return export_to_instruction_registry(entries)
    
    # =========================================================================
    # Ecosystem Analysis (from core/cartographer.py - high-level)
    # =========================================================================
    
    def analyze_ecosystem(
        self,
        base_path: Path = None,
        target_projects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive ecosystem analysis.
        
        Args:
            base_path: Root path to analyze
            target_projects: Optional list of specific projects
            
        Returns:
            EcosystemMap as dict
        """
        from omni.core.cartographer import EcosystemCartographer
        from dataclasses import asdict
        
        if base_path is None:
            base_path = self.settings.get_infrastructure_root()
        
        logger.info(f"🔍 Analyzing ecosystem: {base_path}")
        
        cartographer = EcosystemCartographer(str(base_path))
        ecosystem = cartographer.analyze_ecosystem(target_projects)
        
        return asdict(ecosystem)
    
    def generate_ecosystem_report(
        self,
        ecosystem_map: Dict[str, Any]
    ) -> str:
        """
        Generate a markdown report from ecosystem analysis.
        
        Args:
            ecosystem_map: Results from analyze_ecosystem
            
        Returns:
            Markdown report string
        """
        projects = ecosystem_map.get("projects", [])
        tech_stack = ecosystem_map.get("technology_stack", {})
        patterns = ecosystem_map.get("architecture_patterns", {})
        
        report = []
        report.append("# Ecosystem Analysis Report\n")
        report.append(f"**Generated:** {ecosystem_map.get('generated_at', 'Unknown')}\n")
        report.append(f"**Projects Analyzed:** {len(projects)}\n")
        
        report.append("\n## Technology Stack\n")
        for lang, count in sorted(tech_stack.items(), key=lambda x: -x[1]):
            report.append(f"- {lang}: {count} projects\n")
        
        report.append("\n## Architecture Patterns\n")
        for pattern, items in patterns.items():
            report.append(f"\n### {pattern}\n")
            for item in items[:5]:  # Top 5
                report.append(f"- {item}\n")
        
        report.append("\n## Projects\n")
        for proj in sorted(projects, key=lambda x: x.get("name", "")):
            status = proj.get("status", "unknown")
            emoji = "✅" if status == "active" else "⚠️"
            report.append(f"- {emoji} **{proj.get('name')}** ({proj.get('type', 'unknown')})\n")
        
        return "".join(report)
