"""
omni/core/system.py
The Omni Instrument Core
========================
This is the "Conductor" of the Omni Tool.
It initializes the Pillars and holds the configuration state.

Pattern: The Heart-style loader.
- CLI imports this
- This loads Pillars
- Pillars do the work
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# 1. Import the Golden Key (Federation Heart wiring)
from omni.config import settings

logger = logging.getLogger("Omni.Core")


class OmniInstrument:
    """
    The Federation Instrument for Truth & Reconciliation.
    
    This is the "Conductor" - it doesn't DO the work,
    it LOADS the things that do the work (Pillars).
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.root_dir = settings.get_infrastructure_root()
        self._pillars_loaded = False
        
        # Lazy pillar initialization
        self._cartography = None
        self._registry = None
        self._gatekeeper = None
        self._intel = None
        
        logger.info(f"🎻 Omni Instrument Initialized")
        logger.info(f"   - Infrastructure: {self.root_dir}")
        logger.info(f"   - Heart Available: {settings.heart_available()}")
        logger.info(f"   - Dry Run: {dry_run}")
    
    # =========================================================================
    # Pillar Accessors (Lazy Loading)
    # =========================================================================
    
    @property
    def cartography(self):
        """The Cartography Pillar - manages paths, identity, fetcher."""
        if self._cartography is None:
            from omni.pillars.cartography import CartographyPillar
            self._cartography = CartographyPillar(settings)
        return self._cartography
    
    @property
    def registry(self):
        """The Registry Pillar - manages manifest parsing."""
        if self._registry is None:
            from omni.pillars.registry import RegistryPillar
            self._registry = RegistryPillar(settings)
        return self._registry
    
    @property
    def gatekeeper(self):
        """The Gatekeeper Pillar - manages policy and provenance."""
        if self._gatekeeper is None:
            from omni.pillars.gatekeeper import GatekeeperPillar
            self._gatekeeper = GatekeeperPillar(settings)
        return self._gatekeeper
    
    @property
    def intel(self):
        """The Intel Pillar - manages AI analysis and librarian."""
        if self._intel is None:
            from omni.pillars.intel import IntelPillar
            self._intel = IntelPillar(settings)
        return self._intel
    
    # =========================================================================
    # Status & Health
    # =========================================================================
    
    def status(self) -> Dict[str, Any]:
        """Report health of the Instrument."""
        return {
            "version": "0.6.0",
            "heart_connected": settings.heart_available(),
            "infrastructure_root": str(self.root_dir),
            "dry_run": self.dry_run,
            "pillars": {
                "cartography": "available",
                "registry": "available",
                "gatekeeper": "available",
                "intel": "available",
            }
        }
    
    # =========================================================================
    # High-Level Operations (Orchestration)
    # =========================================================================
    
    def reconcile_identity(self) -> Dict[str, Any]:
        """
        The Master Operation: Reconcile project identities.
        
        Delegates to Cartography Pillar.
        """
        return self.cartography.scan_ecosystem_identity()
    
    def audit_provenance(self) -> Dict[str, Any]:
        """
        Audit UUID provenance across the federation.
        
        Delegates to Gatekeeper Pillar.
        """
        return self.gatekeeper.audit_provenance()


# =============================================================================
# Singleton Factory
# =============================================================================

_instrument: Optional[OmniInstrument] = None


def get_instrument(dry_run: bool = False) -> OmniInstrument:
    """Get the singleton OmniInstrument instance."""
    global _instrument
    if _instrument is None:
        _instrument = OmniInstrument(dry_run=dry_run)
    return _instrument
