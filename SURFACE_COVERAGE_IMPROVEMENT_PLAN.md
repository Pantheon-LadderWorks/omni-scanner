# 🎯 Surface Coverage Improvement Plan

**Current State:** 970 surfaces, 98.7% partial, 1.3% exists  
**Goal:** Move high-value surfaces from "partial" to "exists"  
**Strategy:** Targeted contract creation + schema documentation

---

## 📊 The Partial Problem

**What "Partial" Means:**
- Surface is **recognized** (covered by base contract family)
- Surface **lacks specific schema/OpenAPI** documentation
- Function exists, but inputs/outputs not formally defined

**Why It's Gnarly:**
- 662 CLI tools without `--json` schemas
- 131 MCP tools without `inputSchema`/`outputSchema`
- 29 HTTP endpoints without OpenAPI specs

---

## 🎯 Three-Tier Upgrade Strategy

### Tier 1: High-Value Wins (Target: 50 surfaces → exists)
**Focus:** Public-facing, frequently used, or dangerous surfaces

**CLI Tools (10-15 surfaces):**
1. `federation status` - Add JSON output schema
2. `federation nexus` - Add operation schemas
3. `omni scan` - Already has JSON! (upgrade to exists)
4. `federation verify` - Add validation result schema

**MCP Tools (20-25 surfaces):**
1. **CMP Knowledge Graph** (11 tools) - Add inputSchema/outputSchema to all
2. **Awakening Engine** (5 tools) - Add schemas
3. **Thought Engine** (7 tools) - Add schemas
4. **CodeCraft Embassy** - Add ritual execution schema

**HTTP APIs (10-15 surfaces):**
1. Living Knowledge Graph Flask API - Generate OpenAPI spec
2. Living Memory Engine endpoints - Add OpenAPI
3. CMP REST endpoints (if any) - Document

---

### Tier 2: Safety-Critical (Target: 30 surfaces → exists)
**Focus:** Surfaces that modify state, deploy, or involve money/data

**DB Surfaces (15-20):**
- CMP schema migrations (Alembic) - Document schema versions
- Agent state persistence - Add JSON schemas
- Chronicle storage - Define event schemas

**Bus Topics (10-15):**
- Crown Bus events - Add event payload schemas
- Federation Bus messages - Document message formats
- Agent testimony events - Schema for oracle.emergent_insights

---

### Tier 3: Package Distribution (NEW CONTRACT NEEDED)
**Problem:** No contract for pip packages, but we have:
- `seraphina-federation` v1.0.0
- `omni` (planned pip package)
- `federation_heart` (core library)

**Proposed Contract: C-PKG-BASE-001 (Python Package Standard)**

```yaml
contract_id: C-PKG-BASE-001
title: Python Package Distribution Standard
scope: All Federation pip packages
requirements:
  - pyproject.toml with semantic versioning
  - README.md with installation/usage
  - CHANGELOG.md with version history
  - LICENSE file (MIT or Apache 2.0)
  - Entry points defined for CLI tools
  - Dependencies locked in requirements.txt
  - Editable install supported (pip install -e .)
  - Tests included (pytest)
schema_location: governance/contracts/packages/schemas/
status: PROPOSED
```

**Surfaces this would cover:**
- `seraphina-federation` package (federation CLI)
- `omni` package (Tricorder tool)
- `federation_heart` library
- Future pip packages

---

## 🚀 Quick Wins (Next 2 Hours)

1. **Create C-PKG-BASE-001 contract** (30 min)
   - Add package standard requirements
   - Create schema template
   - Register in CONTRACT_REGISTRY.yaml

2. **Upgrade Omni scanner** (30 min)
   - Detect `pyproject.toml` files
   - Check for package distribution markers
   - Add "package" surface kind

3. **Document top 5 CLI tools** (60 min)
   - Add `--json` flag to federation CLI commands
   - Create schemas/cli/federation.v1.json
   - Upgrade 5 surfaces to "exists"

**Expected Result:** 957 partial → 950 partial, 13 exists → 20 exists

---

## 📋 Long-Term Roadmap

### Phase 1 (Week 1): Foundation
- [ ] Create C-PKG-BASE-001 contract
- [ ] Add package scanner to Omni
- [ ] Document federation CLI JSON schemas
- [ ] Target: 20 exists

### Phase 2 (Week 2): MCP Schemas
- [ ] Add inputSchema to all CMP MCP tools
- [ ] Add inputSchema to Awakening Engine
- [ ] Add inputSchema to CodeCraft Embassy
- [ ] Target: 45 exists

### Phase 3 (Week 3): API Documentation
- [ ] Generate OpenAPI for Living Knowledge Graph
- [ ] Generate OpenAPI for Living Memory Engine
- [ ] Document all HTTP endpoints
- [ ] Target: 60 exists

### Phase 4 (Month 2): DB & Events
- [ ] Schema versioning for CMP migrations
- [ ] Event payload schemas for Crown Bus
- [ ] State persistence schemas
- [ ] Target: 90 exists

---

## 🔥 Immediate Action Items

**For You (Kryssie):**
1. Approve C-PKG-BASE-001 contract proposal
2. Prioritize which CLI tools need JSON output first
3. Decide if 98.7% partial is acceptable or if we push to 10% exists

**For Oracle (me):**
1. Create C-PKG-BASE-001.md contract file
2. Add package detection to surfaces scanner
3. Generate JSON schemas for top 5 CLI tools
4. Update CONTRACT_REGISTRY.yaml

---

## 💡 Philosophy Question

**Should we aim for 100% exists coverage?**

**Pros:**
- Perfect contract compliance
- Every surface fully documented
- Zero ambiguity

**Cons:**
- 970 schemas to maintain
- Bureaucratic overhead
- Some surfaces change rapidly (schemas go stale)

**Oracle's Recommendation:**
- **80/20 Rule**: Focus on 20% of surfaces (194) that represent 80% of usage
- Keep base contract families for low-value/internal surfaces
- Move only **public-facing, frequently-used, or dangerous** surfaces to "exists"
- Target: 15-20% exists (150-200 surfaces), 80-85% partial

---

## 📈 Success Metrics

| Metric | Current | Target (Phase 1) | Target (End State) |
|--------|---------|------------------|-------------------|
| **Total Surfaces** | 970 | 970 | 970 |
| **Exists** | 13 (1.3%) | 50 (5%) | 150-200 (15-20%) |
| **Partial** | 957 (98.7%) | 920 (95%) | 770-820 (80-85%) |
| **Missing** | 0 (0%) | 0 (0%) | 0 (0%) |
| **Contracts** | 15 base | 16 (+ C-PKG-BASE-001) | 25-30 specific |

---

**Next Step:** Should I create C-PKG-BASE-001 and add package scanning to Omni?
