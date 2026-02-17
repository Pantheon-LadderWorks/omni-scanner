"""
Omni Core - The Kernel
======================
Identity, Configuration, and Orchestration. Nothing else.

The Core is the Conductor - it doesn't DO the work,
it LOADS the things that do the work (Pillars).
"""

# Core Kernel Modules Only
from . import model
from . import gate
from . import identity_engine
from . import registry
from . import config

# Note: Heavy logic moved to pillars/
# - cartographer.py logic -> pillars/cartography.py
# - brain.py logic -> pillars/intel.py
# - provenance.py logic -> pillars/gatekeeper.py
