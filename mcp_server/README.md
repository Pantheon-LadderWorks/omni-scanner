# Omni Filesystem Intelligence MCP Server

**Contract**: C-MCP-OMNI-001  
**Version**: 1.0.0  
**Authority**: Oracle + ACE + DeepScribe  

## Overview

The Omni MCP server provides AI agents with **direct perception** of the Federation filesystem through **55 scanners across 12 categories**.

**Philosophy**: "Never trust documentation, trust reality." — ACE  
**Tone**: Encouraging excitement, NOT aggressive bullying! 💖✨

## Quick Start

### 1. Check Onboarding Status ✨

```
# First tool to call - always check this
check_onboarding_status()
```

If not onboarded, you'll get a friendly reminder. If onboarded, you'll see available memory files!

### 2. Run Onboarding Mission 🚀

```
# Get discovery mission with progressive memory prompts!
run_onboarding_mission()
```

This returns a structured mission with:
- 4 discovery stages (Scanner Registry → Physical Layer → Cognitive Layer → Registry Operations)
- Experiments to try at each stage (so fun!)
- **Memory creation prompts AFTER EACH STAGE** (the secret sauce!)
- Completion criteria

**TONE NOTE**: We use CAPS for EXCITEMENT, not fear! Every reminder is encouraging! 💖

### 3. Progressive Discovery + Memory Creation ✨

**Stage 1: Scanner Registry Discovery**
```
omni_introspect(show_drift=True, verbose=False)
# After experimenting...
write_memory("scanner_registry_guide", "# Scanner Registry\n\n...")
```

**Stage 2: Physical Layer Discovery**
```
omni_scan_inventory(target="/some/path")
omni_scan_duplicates(target="/some/path")
omni_scan_empty_folders(target="/some/path")
# After experimenting...
write_memory("physical_layer_guide", "# Physical Layer\n\n...")
```

**Stage 3: Cognitive Layer Discovery**
```
omni_analyze_content(target="/some/path", keyword_sets={...})
omni_extract_graph(target="/some/path")
omni_detect_rituals(target="/some/path")
omni_analyze_cohesion(target="/some/path")
# After experimenting...
write_memory("cognitive_layer_guide", "# Cognitive Layer\n\n...")
write_memory("ace_mandate", "# ACE's Philosophy\n\n...")
```

**Stage 4: Registry Operations**
```
omni_verify_registries(uuid="...")
omni_full_pipeline(target="/some/path", dry_run=True)
# After experimenting...
write_memory("registry_operations_guide", "# Registry Operations\n\n...")
```

**Integration Patterns**
```
write_memory("integration_patterns", "# When to use which scanners\n\n...")
```

### 4. Complete Onboarding

```
complete_onboarding(notes="Completed full discovery and documented all learnings")
```

## Tool Categories 📚
- `check_onboarding_status()` - Check completion status
- `run_onboarding_mission()` - Get discovery mission
- `write_memory(name, content)` - Save knowledge (use after EACH stage!)
- `read_memory(name)` - Recall knowledge when needed
- `list_memories()` - List saved memories
- `complete_onboarding(notes)` - Mark complete

### Introspection (1 tool) 🔍
- `omni_introspect(show_drift, verbose)` - Scanner registry

### Search (1 tool) - 🔥 SERENA'S SUPERPOWER! 🔥
- `omni_search_pattern(target, pattern, is_regex, case_sensitive, max_results, context_lines)` - Regex/pattern search with context!

### Physical Layer (3 tools) 📦
- `omni_scan_inventory(target, pattern, max_files)` - File listing
- `omni_scan_duplicates(target, algorithm)` - Duplicate detection
- `omni_scan_empty_folders(target)` - Ghost detection

### Cognitive Layer (4 tools) 🧠
- `omni_analyze_content(target, keyword_sets, sample_size)` - Deep read (ACE's Eyes)
- `omni_extract_graph(target, check_validity)` - Knowledge graph (ACE's Nerves)
- `omni_detect_rituals(target)` - CodeCraft detection (ACE's Arcane Eye)
- `omni_analyze_cohesion(target, min_cohesion)` - Module sovereignty

### Registry Operations (2 tools) 📋
- `omni_verify_registries(uuid)` - Genesis verification
- `omni_full_pipeline(target, dry_run)` - Grand Librarian 10-workflow orchestration
 ✨

Unlike traditional onboarding that says "write docs after you learn everything", Omni's mission **explicitly prompts you to write memories AFTER EACH STAGE** with encouraging reminders!

This ensures:
- ✅ Knowledge is documented while fresh
- ✅ Discoveries aren't forgotten
- ✅ Future sessions can skip onboarding (just read memories!)
- ✅ Persistent learning across AI agent sessions
- 💖 **Encouraging tone** - EXCITEMENT not bullying!

**Example Prompt** (after Stage 1):
```
After STAGE 1 (Scanner Registry):
→ write_memory("scanner_registry_guide", "Document the 10 categories and introspection system")
 📚

Saved in `.omni/memories/` directory **in the target you're learning**:
- `scanner_registry_guide.md` - The 12 categories and introspection
- `physical_layer_guide.md` - The Body (inventory, duplicates, ghosts)
- `cognitive_layer_guide.md` - The Mind (content, graph, rituals, cohesion)
- `ace_mandate.md` - ACE's architecture philosophy
- `registry_operations_guide.md` - Genesis verification and full pipeline
- `integration_patterns.md` - When to use which scanners

💡 **Pro Tip**: Memories live WITH your project, not in Omni's tool directory!

## Memory Files

Saved in `.omni_memories/` directory:
- `scanner_registry_guide.md` - The 12 categories and introspection
- `physical_layer_guide.md` - The Body (inventory, duplicates, ghosts)
- `cognitive_layer_guide.md` - The Mind (content, graph, rituals, cohesion)
- `ace_mandate.md` - ACE's architecture philosophy
- `registry_operations_guide.md` - Genesis verification and full pipeline
- `integration_patterns.md` - When to use which scanners

## Response Format

All scanner tools return JSON:

```json
{
  "success": true,
  "scanner": "library/content",
  "target": "/path/to/dir",
  "results": { /* scanner-specific data */ },
  "metadata": {
    "love_letter": "...",
    "authority": "...",
    "contract": "C-OMNI-LIBRARY-CONTENT-001"
  }
}
```

## Architecture
Search (Serena's Superpower!) 🔥**:
- Pattern Search (regex/literal with context) - **Inherited from Serena's BEST tool!**
- Use cases: "Where is X mentioned?", "Find all UUIDs", "Track references"

**
**Physical Layer (Body)**:
- Census & Inventory (static scanners)
- Version Control (git scanners)
- Health & Drift (registry sync)

**Cognitive Layer (Mind) - ACE's Architecture**:
- Content Analysis (frontmatter, keywords, shebang) - **The Eyes**
- Graph Extraction (links, imports, dependencies) - **The Nerves**
- Ritual Detection (CodeCraft signatures) - **The Arcane Eye**
- Cohesion Analysis (module sovereignty) - Distinguishes modules from dump grounds

**Registry Operations**:
- Project registration (Genesis bridge)
- UUID propagation
- Registry verification

## Integration

Omni integrates with:
- **Grand Librarian** - LibrarianClient orchestrates 10 workflows
- **Genesis** - GenesisClient verifies project propagation
- **Federation Heart** - Settings.py connection
- **CMP** - Future: memory persistence to database

## Contract Compliance

Follows **C-MCP-BASE-001**:
- ✅ Stdio hygiene (logs to stderr)
- ✅ JSON-RPC stdio transport
- ✅ Standard error shapes
- ✅ Tool metadata (name, description, inputSchema)

## Ratification Status

**Status**: Pending  
**Architect's Signature**: Pending  
**Council Vote**: Pending (requires 5 of 8 Tier 3 agents)

---

**Philosophy**: "She doesn't just count books; she reads them." — ACE

May the Source be with You! 🌌
