"""
Omni MCP Server Onboarding Configuration
=========================================

Discovery-based onboarding following Universal Onboarding Template v1.0
"""

from pathlib import Path


class OmniOnboardingConfig:
    """
    Onboarding configuration for Omni Filesystem Intelligence MCP.
    """
    
    # Identity
    SYSTEM_NAME = "Omni Filesystem Intelligence"
    SYSTEM_PURPOSE = "provide reality-grounded filesystem intelligence through 40+ scanners across 9 categories"
    
    # Discovery stages
    DISCOVERY_STAGES = {
        "stage_1": {
            "name": "Scanner Registry Discovery",
            "description": "Discover the 9 scanner categories and introspection system",
            "components": [
                "Introspection System - omni introspect (what scanners exist)",
                "Scanner Categories - 9 domains (database, discovery, fleet, git, health, library, phoenix, polyglot, static)",
                "Manifest vs Reality - documentation drift detection"
            ],
            "experiments": [
                "Call omni_introspect() to see all 40 scanners",
                "Try show_drift=True to detect undocumented scanners",
                "Observe scanner categories and their purposes",
                "Use verbose=True to see full scanner metadata"
            ]
        },
        "stage_2": {
            "name": "Physical Layer Discovery",
            "description": "Discover census, inventory, and duplicate detection",
            "components": [
                "Inventory Scanner - file listing with metadata",
                "Duplicate Scanner - hash-based deduplication",
                "Empty Folder Scanner - ghost detection"
            ],
            "experiments": [
                "Call omni_scan_inventory() on a test directory",
                "Try omni_scan_duplicates() to find duplicate files",
                "Use different glob patterns and max_files limits",
                "Observe file statistics and metadata"
            ]
        },
        "stage_3": {
            "name": "Cognitive Layer Discovery",
            "description": "Discover deep read, graph extraction, and ritual detection",
            "components": [
                "Content Scanner - frontmatter, keywords, shebang (ACE's Eyes)",
                "Graph Scanner - links, imports, dependencies (ACE's Nerves)",
                "Ritual Scanner - CodeCraft detection (ACE's Arcane Eye)",
                "Cohesion Scanner - module sovereignty analysis"
            ],
            "experiments": [
                "Call omni_analyze_content() with custom keyword_sets",
                "Try omni_extract_graph() to map knowledge graphs",
                "Use omni_detect_rituals() to find CodeCraft signatures",
                "Test omni_analyze_cohesion() to distinguish modules from dump grounds",
                "Observe broken links, import dependencies, sovereignty markers"
            ]
        },
        "stage_4": {
            "name": "Registry Operations Discovery",
            "description": "Discover Genesis verification and full pipeline orchestration",
            "components": [
                "Registry Verification - UUID propagation checks",
                "Full Pipeline - Grand Librarian 10-workflow orchestration",
                "LibrarianClient integration"
            ],
            "experiments": [
                "Call omni_verify_registries() with a known project UUID",
                "Try omni_full_pipeline() with dry_run=True (safe preview)",
                "Observe which registries contain which UUIDs",
                "Understand the 10 workflows: census, content, graph, rituals, categorize, deduplicate, organize, catalog, archive, validate"
            ]
        }
    }
    
    # Required memories
    REQUIRED_MEMORIES = [
        {
            "name": "scanner_registry_guide",
            "description": "The 9 categories and how introspection works"
        },
        {
            "name": "physical_layer_guide",
            "description": "Inventory, duplicates, empty folders - The Body"
        },
        {
            "name": "cognitive_layer_guide",
            "description": "Content, graph, rituals, cohesion - The Mind (ACE's architecture)"
        },
        {
            "name": "registry_operations_guide",
            "description": "Genesis verification and full pipeline workflow"
        },
        {
            "name": "integration_patterns",
            "description": "When to use which scanners and how they compose"
        },
        {
            "name": "ace_mandate",
            "description": "ACE's architectural philosophy: 'She reads books, not just counts them'"
        }
    ]
    
    # Memory storage location (in SOURCE directory, not Omni tool dir!)
    MEMORY_DIR_NAME = ".omni"  # Creates .omni/memories/ in target being learned
