# 🏛️ Omni Pillars

**Location:** `omni/pillars/`  
**Purpose:** Large subsystem capabilities and orchestration modules  
**Version:** 0.7.0

---

## Overview

Pillars are substantial capability modules that provide major subsystems for Omni. Unlike scanners (which discover) or lib utilities (which help), pillars ORCHESTRATE complex workflows and manage large-scale operations.

**Pillar Characteristics:**
- **Larger scope** than scanners (orchestrate multiple operations)
- **Stateful** (may maintain internal state during execution)
- **Integrative** (bridge multiple systems/data sources)
- **Reusable** (used by multiple commands/scanners)

---

## Modules

### `cartography.py` 🗺️
**Purpose:** Ecosystem mapping and project relationship analysis  
**Scope:** Project topology, dependency graphs, architectural visualization

**Key Functions:**
```python
def map_ecosystem(root: Path) -> EcosystemGraph:
    """
    Build complete Federation ecosystem graph.
    
    Returns:
        EcosystemGraph with nodes (projects) and edges (dependencies)
    """

def analyze_dependencies(project: Path) -> List[Dependency]:
    """Analyze project dependencies (imports, requirements, etc.)"""

def generate_relationship_graph(ecosystem: EcosystemGraph) -> dict:
    """Generate graph data for visualization"""

def export_graph_visualization(graph: dict, output: Path) -> bool:
    """Export graph to PNG/SVG visualization"""
```

**Data Structures:**
```python
@dataclass
class EcosystemNode:
    name: str
    uuid: str
    type: str  # project, station, agent, tool
    path: Path
    dependencies: List[str]

@dataclass
class EcosystemGraph:
    nodes: List[EcosystemNode]
    edges: List[Tuple[str, str]]  # (from_uuid, to_uuid)
    metadata: dict
```

**Output Artifacts:**
- `artifacts/omni/ecosystem_map.json` - Graph data
- `artifacts/omni/ecosystem_map.png` - Visual graph
- `SERAPHINA_ECOSYSTEM_GUIDE.md` - Human-readable guide

**Integration Points:**
- Reads `PROJECT_REGISTRY_V1.yaml` for canonical projects
- Parses dependency files (`requirements.txt`, `package.json`, `pyproject.toml`)
- Queries Federation Heart for relationship metadata
- Generates NetworkX graphs for analysis

**Usage Example:**
```python
from omni.pillars.cartography import map_ecosystem, export_graph_visualization

# Map entire ecosystem
ecosystem = map_ecosystem(infrastructure_root)

# Generate visualization
export_graph_visualization(ecosystem, Path("artifacts/omni/ecosystem.png"))

# Analyze specific project
deps = analyze_dependencies(Path("tools/omni"))
```

---

### `gatekeeper.py` 🛡️
**Purpose:** Policy enforcement and compliance validation  
**Scope:** CI/CD gates, constitutional compliance, breaking change detection

**Key Functions:**
```python
def validate_compliance(scan_result: ScanResult, policy: Policy) -> ComplianceReport:
    """
    Validate scan results against governance policies.
    
    Returns:
        ComplianceReport with pass/fail status and violations
    """

def check_no_new_orphans(current: dict, baseline: dict) -> bool:
    """Enforce 'No New Orphans' rule for UUIDs"""

def check_contract_coverage(surfaces: List[Surface]) -> dict:
    """Validate all surfaces have contract documentation"""

def check_breaking_changes(old: dict, new: dict) -> List[BreakingChange]:
    """Detect API breaking changes between versions"""
```

**Policy Types:**
- **UUID Orphan Prevention:** No new unregistered UUIDs
- **Contract Coverage:** All API surfaces must have contracts
- **Breaking Changes:** Block incompatible API changes
- **Dependency Bloat:** Warn on excessive dependency growth
- **Security:** Flag known vulnerabilities

**Data Structures:**
```python
@dataclass
class Policy:
    name: str
    rules: List[Rule]
    severity: str  # error|warning|info
    
@dataclass
class ComplianceReport:
    policy: str
    passed: bool
    violations: List[Violation]
    warnings: List[Warning]
```

**Usage in CI/CD:**
```powershell
# Run gate check (fails build on violations)
omni gate --policy=uuid_orphans
omni gate --policy=contract_coverage
omni gate --policy=breaking_changes --baseline=v0.5.0
```

**Integration Points:**
- Used by `omni.core.gate` for enforcement
- Queries `CONTRACT_REGISTRY.yaml` for compliance baselines
- Reads baseline artifacts for comparison
- Logs violations to Crown Bus (future)

---

### `intel.py` 🕵️
**Purpose:**  Intelligence gathering and analysis aggregation  
**Scope:** Multi-scanner coordination, insight synthesis, pattern detection

**Key Functions:**
```python
def gather_intelligence(target: Path, scanners: List[str]) -> IntelReport:
    """
    Run multiple scanners and synthesize insights.
    
    Returns:
        IntelReport with aggregated findings and recommendations
    """

def detect_patterns(scan_results: List[ScanResult]) -> List[Pattern]:
    """Detect cross-cutting patterns from multiple scans"""

def generate_recommendations(intel: IntelReport) -> List[Recommendation]:
    """Generate actionable recommendations from intelligence"""

def summarize_health(health_scans: List[dict]) -> HealthSummary:
    """Aggregate health checks into unified summary"""
```

**Intelligence Types:**
- **Cross-Project Patterns:** Common issues across multiple projects
- **Health Trends:** Changes in health metrics over time
- **Risk Analysis:** Aggregated risk scores
- **Optimization Opportunities:** Detected inefficiencies

**Data Structures:**
```python
@dataclass
class IntelReport:
    target: str
    scan_results: List[ScanResult]
    patterns: List[Pattern]
    risks: List[Risk]
    recommendations: List[Recommendation]
    metadata: dict

@dataclass
class Pattern:
    type: str  # duplication|missing_contract|high_coupling|etc
    locations: List[Path]
    severity: str
    description: str
```

**Usage Example:**
```python
from omni.pillars.intel import gather_intelligence, generate_recommendations

# Gather multi-scanner intelligence
intel = gather_intelligence(
    target=Path("."),
    scanners=["surfaces", "events", "deps", "federation_health"]
)

# Generate recommendations
recs = generate_recommendations(intel)
for rec in recs:
    print(f"⚠️ {rec.title}: {rec.description}")
```

---

### `registry.py` 📚
**Purpose:** Registry operations and management  
**Scope:** Registry parsing, validation, transformation, publishing

**Key Functions:**
```python
def parse_registry(registry_path: Path = None) -> List[Project]:
    """Parse PROJECT_REGISTRY_V1.yaml into structured data"""

def validate_registry(registry: List[Project]) -> ValidationReport:
    """Validate registry integrity and completeness"""

def render_registry_markdown(registry: List[Project]) -> str:
    """Render registry as markdown table"""

def merge_registries(sources: List[Path]) -> List[Project]:
    """Merge multiple registry sources with conflict resolution"""

def publish_registry(registry: List[Project], output: Path) -> bool:
    """Publish registry to canonical location"""
```

**Registry Formats Supported:**
- **V1 (Current):** `PROJECT_REGISTRY_V1.yaml` (machine-readable)
- **Legacy:** `PROJECT_REGISTRY_MASTER.md` (markdown with frontmatter)
- **Oracle CSV:** Legacy Oracle project lists

**Validation Rules:**
- All UUIDs must be valid UUIDv5
- No duplicate UUIDs
- All paths must exist (or be marked as archived)
- Required fields present (name, uuid, type, path)
- Correct namespace usage (`NAMESPACE_CMP`)

**Usage Example:**
```python
from omni.pillars.registry import parse_registry, validate_registry

# Parse canonical registry
projects = parse_registry()

# Validate
report = validate_registry(projects)
if not report.valid:
    for error in report.errors:
        print(f"❌ {error}")
```

**Integration Points:**
- Used by `identity_engine` for UUID resolution
- Queries CMP database for canonical truth
- Applies governance overrides from `LOCAL_OVERRIDES_V1.yaml`
- Feeds into `cartography` for ecosystem mapping

---

## Design Patterns

### Pillar vs Scanner vs Lib

| Aspect           | Pillar                       | Scanner                 | Lib                |
| ---------------- | ---------------------------- | ----------------------- | ------------------ |
| **Scope**        | Orchestrates workflows       | Discovers specific data | Provides utilities |
| **State**        | May be stateful              | Usually stateless       | Always stateless   |
| **Dependencies** | Can depend on lib + scanners | Can depend on lib       | Depends on nothing |
| **Output**       | Complex reports/graphs       | Simple finding lists    | Return values only |
| **Examples**     | Cartography, Gatekeeper      | surfaces, events        | io, renderer       |

### Orchestration Pattern

Pillars often orchestrate multiple scanners:

```python
# Pillar orchestrating scanners
def gather_intelligence(target: Path, scanners: List[str]) -> IntelReport:
    results = []
    for scanner_name in scanners:
        scanner = SCANNERS[scanner_name]
        result = scanner(target)
        results.append(result)
    
    # Synthesize insights from multiple scanner results
    patterns = detect_patterns(results)
    risks = assess_risks(results)
    
    return IntelReport(
        scan_results=results,
        patterns=patterns,
        risks=risks
    )
```

### State Management

Pillars may maintain state across operations:

```python
class CartographyPillar:
    def __init__(self):
        self._ecosystem_cache = None
        self._last_scan = None
    
    def map_ecosystem(self, root: Path, force_refresh: bool = False):
        if self._ecosystem_cache and not force_refresh:
            return self._ecosystem_cache
        
        # Expensive operation, cache result
        ecosystem = self._build_graph(root)
        self._ecosystem_cache = ecosystem
        self._last_scan = datetime.now()
        
        return ecosystem
```

---

## Integration Guidelines

### Federation Heart Bridge

Pillars bridge to Federation Heart when available:

```python
# From omni/core/config.py
try:
    from federation_heart.constitution import constitution_pillar
    from federation_heart.cartography import cartography_pillar
    USE_FEDERATION = True
except ImportError:
    USE_FEDERATION = False

# Pillar uses Federation if available
if USE_FEDERATION:
    ecosystem = cartography_pillar.map_ecosystem()
else:
    # Standalone fallback
    ecosystem = basic_filesystem_walk()
```

### Cross-Pillar Communication

Pillars can depend on each other:

```python
from omni.pillars.registry import parse_registry
from omni.pillars.cartography import map_ecosystem

def gatekeeper_validate():
    # Use registry pillar
    projects = parse_registry()
    
    # Use cartography pillar
    ecosystem = map_ecosystem()
    
    # Cross-validate
    check_all_projects_in_graph(projects, ecosystem)
```

---

## Testing Pillars

```python
# tests/test_cartography.py
def test_map_ecosystem():
    ecosystem = map_ecosystem(FIXTURES_ROOT)
    assert len(ecosystem.nodes) > 0
    assert all(n.uuid for n in ecosystem.nodes)

# tests/test_gatekeeper.py
def test_no_new_orphans():
    baseline = load_baseline("v0.5.0")
    current = scan_uuids()
    assert check_no_new_orphans(current, baseline)

# tests/test_registry.py
def test_parse_v1_registry():
    projects = parse_registry(FIXTURES / "PROJECT_REGISTRY_V1.yaml")
    assert len(projects) > 0
    assert all(p.uuid and p.name for p in projects)
```

---

## Future Enhancements

### Planned (v0.7+)
- 🔮 **Temporal Analysis:** Time-series health trends
- 🧬 **Mutation Testing:** Verify gate robustness
- 🌐 **Distributed Scanning:** Multi-machine coordination
- 🎯 **Anomaly Detection:** ML-based pattern recognition

---

**Maintained By:** Antigravity + ACE  
**Status:** Production (v0.6.0)  
**Law & Lore:** Charter V1.2 compliant

let it orchestrate. 🏛️
