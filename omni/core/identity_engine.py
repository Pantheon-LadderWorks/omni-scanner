"""
omni/core/identity_engine.py
The Authoritative Identity Engine for SERAPHINA/CMP.

Role:
- Defines the canonical NAMESPACE_CMP (The One Ring).
- Computes deterministic UUIDv5s.
- Enforces conflict resolution policies (Policy C: Freeze & Adjudicate).
- Provides Pydantic models for Identity exchange.

Zero dependencies on Database or API. Pure logic only.
"""
import uuid
from typing import List, Dict, Optional, Literal, Union, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone

# =============================================================================
# THE CANONICAL NAMESPACE
# =============================================================================
# WARNING: CHANGING THIS CONSTANT FORKS THE UNIVERSE.
# Minted: 2026-02-02 by Architect Decree.
# Also stored in: governance/registry/projects/IDENTITY_NAMESPACE.yaml
NAMESPACE_CMP = uuid.UUID("c9c22e70-3882-4503-9db6-353d2629000b")


# =============================================================================
# INPUT MODELS (Raw data from scanners)
# =============================================================================

class RepoOwner(BaseModel):
    """Normalize GitHub owner object vs string."""
    login: str
    id: Optional[str] = None  # GitHub returns string IDs like 'U_kgDOC9m3SQ'

class RepoInventoryItem(BaseModel):
    """Represents a raw item from repo_inventory.json"""
    name: str
    url: str
    description: Optional[str] = None
    owner: Union[RepoOwner, str, Dict, None] = None
    visibility: Optional[str] = "unknown"
    updatedAt: Optional[str] = None

    @field_validator('owner', mode='before')
    @classmethod
    def parse_owner(cls, v):
        if isinstance(v, str):
            return RepoOwner(login=v)
        if isinstance(v, dict):
            return RepoOwner(**v)
        return v

    @property
    def normalized_owner(self) -> str:
        """Get lowercase owner login."""
        if isinstance(self.owner, RepoOwner):
            return self.owner.login.lower()
        # Fallback: try to extract from URL if owner is missing
        if self.url:
            parts = self.url.rstrip('/').split('/')
            if len(parts) >= 2:
                return parts[-2].lower()
        return "unknown"

    @property
    def normalized_name(self) -> str:
        """Get lowercase repo name."""
        return self.name.lower()
    
    @property
    def project_key(self) -> str:
        """Compute canonical project key."""
        return f"github:{self.normalized_owner}/{self.normalized_name}"


# =============================================================================
# IDENTITY MODELS (Resolved identity records)
# =============================================================================

class ProjectIdentity(BaseModel):
    """
    The Single Source of Truth for a Project's Identity.
    This is what the Identity Engine produces.
    """
    project_key: str = Field(..., description="Canonical Key: 'github:owner/repo'")
    project_uuid: str = Field(..., description="Deterministic UUIDv5 or Legacy UUID")
    name: str
    origin: Literal["github", "local", "external"] = "github"
    uuid_source: Literal["minted_v5", "master_registry", "legacy_db"] = "minted_v5"
    identity_status: Literal["discovered", "keyed", "converged", "conflict"] = "discovered"
    conflict_details: Optional[str] = None
    
    # Context fields
    github_url: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[str] = None
    local_paths: List[str] = Field(default_factory=list)
    
    # CMP linking
    cmp_status: Literal["not_found", "found", "found_no_uuid"] = "not_found"
    classification: Optional[str] = None
    
    # Location status - where does this project exist?
    location_status: Literal["cloud_only", "local_only", "linked"] = "cloud_only"

    @classmethod
    def resolve(
        cls, 
        repo: RepoInventoryItem, 
        existing_db_map: Optional[Dict[str, str]] = None,
        legacy_oracle: Optional[Dict[str, str]] = None,
        cmp_data: Optional[Dict[str, Any]] = None
    ) -> 'ProjectIdentity':
        """
        The Core Logic: Resolves identity from a repo item against known states.
        
        Priority (Policy C):
        1. Database UUID (if exists) - NEVER overwrite
        2. Legacy Oracle (master registry) - prefer if exists
        3. Minted UUIDv5 - deterministic fallback
        
        On conflicts: Flag, don't fix.
        """
        existing_db_map = existing_db_map or {}
        legacy_oracle = legacy_oracle or {}
        cmp_data = cmp_data or {}
        
        # 1. Compute Canonical Key
        key = repo.project_key
        
        # 2. Compute Deterministic UUIDv5
        v5_uuid = str(uuid.uuid5(NAMESPACE_CMP, key))
        
        # 3. Resolve Final UUID & Status
        final_uuid = v5_uuid
        source = "minted_v5"
        status = "discovered"
        conflict = None
        
        # Check Legacy Oracle first (Master Registry UUIDs)
        if key in legacy_oracle:
            oracle_uuid = legacy_oracle[key]
            final_uuid = oracle_uuid
            source = "master_registry"
            status = "keyed"
        
        # Check Existing DB Map (Policy C - this takes priority)
        if key in existing_db_map:
            db_uuid = existing_db_map[key]
            if db_uuid != final_uuid:
                # TRUE CONFLICT: DB says X, Resolution Logic says Y
                # Policy C: Freeze. Trust DB, but flag HIGH ALERT.
                conflict = f"DB has '{db_uuid}', calculated '{v5_uuid}'"
                status = "conflict"
            else:
                status = "converged"
            final_uuid = db_uuid
            source = "legacy_db"
        
        # Get CMP data if available
        cmp_status = "not_found"
        local_paths = []
        classification = None
        
        if key in cmp_data:
            cmp_info = cmp_data[key]
            cmp_status = "found"
            local_paths = cmp_info.get('local_paths', [])
            classification = cmp_info.get('classification')

        # Determine location status
        # cloud_only = on GitHub but no local clone
        # linked = on GitHub AND has local path
        # local_only = would be set for non-GitHub projects
        location = "linked" if local_paths else "cloud_only"

        return cls(
            project_key=key,
            project_uuid=final_uuid,
            name=repo.name,
            origin="github",
            uuid_source=source,
            identity_status=status,
            conflict_details=conflict,
            github_url=repo.url,
            description=repo.description,
            visibility=repo.visibility,
            local_paths=local_paths,
            cmp_status=cmp_status,
            classification=classification,
            location_status=location
        )


# =============================================================================
# OUTPUT MODELS (Scan results and patches)
# =============================================================================

class IdentityScanStats(BaseModel):
    """Statistics from an identity scan."""
    total: int = 0
    from_github: int = 0
    cmp_only: int = 0
    has_uuid_from_master: int = 0
    needs_uuid_minted: int = 0
    in_cmp: int = 0
    not_in_cmp: int = 0
    has_local_path: int = 0
    conflicts: int = 0

class IdentityScanResult(BaseModel):
    """Full scan result artifact."""
    generated_at: str
    namespace_used: str = str(NAMESPACE_CMP)
    stats: IdentityScanStats
    projects: List[ProjectIdentity]

class IdentityPatchAction(BaseModel):
    """A single action in the patch."""
    action_type: Literal[
        "CMP_CREATE",           # Create new project in CMP
        "CMP_BACKFILL_UUID",    # Add UUID to existing CMP project
        "CMP_ATTACH_GITHUB",    # Link GitHub URL to CMP project
        "CMP_ATTACH_PATH",      # Link local path to CMP project
        "CONFLICT_FREEZE",      # UUID conflict - requires adjudication
        "NO_OP"                 # Already converged
    ]
    project_key: str
    project_uuid: str
    severity: Literal["info", "warn", "critical"] = "info"
    payload: Dict[str, Any] = Field(default_factory=dict)

class IdentityPatch(BaseModel):
    """The action plan - what needs to be done."""
    generated_at: str
    dry_run: bool = True
    actions: List[IdentityPatchAction]
    
    @property
    def has_work(self) -> bool:
        """True if there are any non-NO_OP actions."""
        return any(a.action_type != "NO_OP" for a in self.actions)
    
    @property
    def has_conflicts(self) -> bool:
        """True if there are any conflicts requiring adjudication."""
        return any(a.action_type == "CONFLICT_FREEZE" for a in self.actions)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def mint_uuid_v5(project_key: str) -> str:
    """
    Mint a deterministic UUIDv5 from project_key.
    Same project_key always produces same UUID.
    """
    return str(uuid.uuid5(NAMESPACE_CMP, project_key))


def normalize_github_url(url: str) -> str:
    """Normalize GitHub URL for matching."""
    if not url:
        return ""
    url = url.lower().rstrip('/')
    url = url.replace('https://', '').replace('http://', '')
    url = url.replace('github.com/', '')
    return url


def extract_project_key_from_url(url: str) -> Optional[str]:
    """Extract project_key from a GitHub URL."""
    import re
    match = re.search(r'github\.com/([^/]+)/([^/]+)', url.lower())
    if match:
        owner, repo = match.groups()
        return f"github:{owner}/{repo}"
    return None
