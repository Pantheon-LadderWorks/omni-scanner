"""
Omni Clients
============

High-level orchestrators for Omni workflows.
Use `TemplateClient` as a base for creating your own integration.
"""

from .template_client import TemplateClient

# Federation-Specific Clients (May not be present in all distributions)
try:
    from .genesis_client import GenesisClient
except ImportError:
    GenesisClient = None

try:
    from .librarian_client import LibrarianClient
except ImportError:
    LibrarianClient = None

try:
    from .github_ops_client import GitHubOpsClient
except ImportError:
    GitHubOpsClient = None

__all__ = [
    "TemplateClient",
    "GenesisClient",
    "LibrarianClient",
    "GitHubOpsClient",
]
