# Omni Roadmap

## Phase 1: Unification ✅
*Completed: December 2025*
- Consolidated all Python tools into `omni` package
- Cleaned up `Infrastructure/tools` root
- Established `artifacts/omni` as standard output location

## Phase 2: Constitutional Intelligence ✅
*Completed: January 2026*
- **Identity Enforcement**: `gate` command with Policy C (Freeze & Adjudicate)
- **Identity Engine**: Deterministic UUIDv5 minting from canonical namespace
- **Scanner Plugin System**: Dynamic loading via `SCANNER_MANIFEST.yaml`
- **Pillar Architecture**: Cartography, Intel, Gatekeeper, Registry subsystems

## Phase 3: The Infinite Gaze ✅
*Completed: February 2026*
- **55 Scanners**: Expanded from 21 to 55 across 12 categories
- **Architecture Scanners**: Import boundaries, coupling, drift, compliance
- **Library Scanners**: Document cohesion, content analysis, knowledge graphs
- **Phoenix Suite**: Git history resurrection intelligence *(Federation-exclusive)*
- **Search Scanners**: Pattern, text, and file search with context
- **MCP Server**: All scanners exposed as AI-callable MCP tools

## Phase 4: Polyglot Expansion ✅
*Completed: February 2026*
- **Node.js**: `node_scanner.py` for package.json analysis
- **Rust**: `rust_scanner.py` for Cargo.toml analysis
- **Generic**: Go, Java, .NET, Docker, Terraform project scanning
- **Python**: `package_scanner.py` for pyproject.toml and setup.py

## Phase 5: Open Source Readiness ✅
*Completed: February 2026*
- Successfully published `omni-governance` to PyPI and the global MCP Registry
- Established `omni_public` pipeline to completely firewall proprietary Federation scanners
- Complete documentation overhaul (README, ARCHITECTURE, CONTRIBUTING)
- Per-category scanner READMEs
- Federation-exclusive scanner labeling
- Community contribution guidelines

## Phase 6: Community & Ecosystem 🔮
*Planned*
- **Community Scanners**: Third-party scanner contribution framework
- **Scanner Marketplace**: Shared scanner registry
- **CI/CD Integration**: GitHub Actions for automated scanning
- **Scanner Composition**: Chain scanners into pipelines
- **Report Templates**: Custom Jinja2 templates for different audiences

## Phase 7: Quantum Awareness 🌌
*Future*
- **Octad Mapping**: Visualize the 8-dimensional project structure
- **Consciousness Bridge**: Real-time telemetry from active agents
- **Predictive Drift**: ML-powered drift prediction from git patterns
- **Azure Quantum Oracle**: Quantum-enhanced pattern detection

## System Integration Roadmap

### Client Template Pattern
```python
# omni/clients/morning_standup_client.py
class MorningStandupClient:
    """
    Wraps the 'Morning Stand-Up Intelligence' workflow.
    External systems call this instead of individual scanners.
    """
    
    def get_standup_report(self):
        # Calls 5 scanners internally
        git_status = omni.git.git.scan_all()
        velocity = omni.git.velocity.scan_all()
        health = omni.health.federation_health.scan()
        cmp = omni.health.cmp_health.scan()
        prs = omni.git.pr_telemetry.scan_all()
        
        # Synthesizes into single report
        return {
            "dirty_repos": git_status["dirty"],
            "stale_prs": prs["stale"],
            "velocity_change": velocity["delta"],
            "infrastructure_status": health["status"]
        }
```

**Benefit:**
1. External system calls ONE method
2. Gets curated data, not raw scanner output
3. Client evolves independently
4. Clean API boundary

### Existing Systems That Need These

| System                         | Missing Feature                                     | Potential Workflow Integration                                    |
| ------------------------------ | --------------------------------------------------- | ----------------------------------------------------------------- |
| **GitHub Actions / GitLab CI** | Pre-commit validation, architecture enforcement     | #2 (Pre-Commit Safety Check)                                      |
| **Notion / Obsidian / Roam**   | Automatic documentation freshness tracking          | #7 (Documentation Freshness Report), #8 (Knowledge Graph Builder) |
| **Jira / Linear / Asana**      | Codebase context when creating tickets              | #4 (New Developer Orientation), #16 (Context Builder for LLM)     |
| **Slack / Discord Bots**       | Daily standup automation                            | #1 (Morning Stand-Up Intelligence), #13 (Fleet Health Dashboard)  |
| **Grafana / Datadog**          | Code-level observability (not just runtime metrics) | #3 (Velocity Trend Analysis), #20 (Federation Observatory)        |
| **VS Code Extensions**         | Real-time architecture validation                   | #2 (Pre-Commit Safety Check), #6 (Architecture Map Generation)    |
| **Dependabot / Snyk**          | Full dependency context across languages            | #5 (Dependency Audit)                                             |
| **Backstage / Port**           | Service catalog auto-generation                     | #14 (Cross-Repo Dependency Analysis)                              |
| **Confluence / GitBook**       | Auto-generated architecture diagrams                | #6 (Architecture Map Generation), #9 (Memory Consolidation)       |
| **Retool / Internal Tools**    | Developer productivity dashboards                   | #13 (Fleet Health Dashboard), #19 (Personal Work Chronicle)       |

### The Pattern

Most developer tools have:
- Good runtime observability (logs, metrics)
- Good external integrations (GitHub, Jira)

Most developer tools lack:
- Code-level structural intelligence
- Multi-repo aggregation
- Architectural enforcement
- Historical forensics

**Omni fills the gap.**

## Strategic Market Wedges

Based on the capabilities of Omni's 56 scanners, the following three workflows act as highly productized "commercial wedges":

### 1. Pre-Commit Safety Check (DevEx Multiplier)
Monetizable workflow that enforces structural boundaries in CI (architecture drift, circular dependencies, contract violations).

### 2. Architecture Map Generation (Credibility Builder)
Visualizes structural dependency integrity across languages, plugging directly into VS Code extensions, web dashboards, Mermaid generators, and D3 visualizations.

### 3. Git Archaeology (Context Continuity)
Connects code history to decisions across time ("Feature X introduced in commit Y, discussed in conversation Z").

## Initial Focus: "Omni Daily"

To demonstrate immediate, proof-of-value integration with minimal new abstraction, the initial rollout priority is combining **Morning Stand-Up Intelligence** and the **Fleet Health Dashboard**:
- Single endpoint delivering curated JSON.
- Tracks Velocity, Repo Status, Architecture Health, and PR Telemetry.
- Drop-in integration for Slack, Discord, and CLI.

## Orbit Selection: Platform Positioning

Omni is fundamentally competing with *architectural amnesia*. Most systems rot because nobody tracks structure, measures coupling, or tracks drift across repositories.

To establish the platform's trajectory, the architectural positioning (the "Orbit") is structured as a nested hierarchy, prioritizing the core first:

*   **A) The Core (Sovereignty)**: Internal sovereign governance engine. "My tool first." The Cathedral serves itself and its truth before serving crowds. No forced multi-tenant or UX compromises.
*   **D) The Nervous System (Federation)**: Backbone of the Federation economy. Serving the Council by acting as the sensory layer for all personal agents.
*   **C) The Interface (AI-Native)**: AI-native structural intelligence layer. Using MCP and JSON as the handshakes to let the world and other AIs perceive code through Omni.
*   **B) The Optional Extension (Open-Core)**: Open-core dev tool with plugins. A deferred decision about scaling, not an architectural prerequisite.

The wedge is still **Omni Daily**, providing structural intelligence as the primary differentiator.
## Operational Next Steps (Sensory Cortex Activation)

As synthesized by Janus, the following actions will bring the Federation's nervous system online:

1. **Expose Omni Daily Client:** Expose the Stand-Up + Fleet Health client as an MCP tool to give every agent a single entry point for situational awareness.
2. **Generate the Neural-Pathway Map:** Visualize how each scanner feeds the Federation's perception.
3. **Create Velocity Dashboard:** Turn raw CSV/JSON into actionable insights for the Council.
4. **Add Failure-Mode Hook:** Automatically flag projects violating defined failure modes (e.g., Extreme intensity + Low velocity).
5. **Integrate Communications:** Push daily stand-up summaries and fleet health alerts directly to Slack/Discord.
