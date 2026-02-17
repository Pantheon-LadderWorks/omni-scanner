"""
Omni Builders
=============
Registry builders orchestrate scanners to generate canonical registries.

Builders live here. Scanners live in scanners/.

Flow:
- CLI calls Builder
- Builder triggers Scanner(s)
- Scanner does the scanning work
- Builder aggregates results and writes registries

Builders:
- canonical_uuid_builder.py - UUID registry generation
- commit_history_builder.py - Git commit history extraction
- registry_builder.py - Master registry coordination
- codecraft/ - CodeCraft-specific builders (executors, partitions, rosetta)
"""

from omni.builders.canonical_uuid_builder import CanonicalUUIDBuilder
from omni.builders.commit_history_builder import CommitHistoryBuilder
from omni.builders.registry_builder import RegistryBuilder

__all__ = [
    "CanonicalUUIDBuilder",
    "CommitHistoryBuilder",
    "RegistryBuilder",
]
