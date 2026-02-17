# Omni MCP Server Architecture - Dynamic Discovery Edition

**Version**: 1.1.0  
**Innovation**: Auto-discovery instead of hardcoded imports!  
**Architect's Insight**: "Omni IS already basically an MCP server!"

## The Revelation 🤯

```
Architect: "cant they auto discover the same way introspect does? 
           isnt omni already basically a mcp server?"
```

**Answer**: YES! Omni already HAS introspection. The MCP server just needed to USE IT!

## Architecture Evolution

### Old Way (v1.0.0) - Hardcoded Hell:
```python
# Manually import every scanner
from omni.scanners.static.inventory import scan_inventory
from omni.scanners.static.duplicates import find_duplicates
from omni.scanners.search.pattern_search import search_pattern
from omni.scanners.library.cohesion import analyze_cohesion
# ... 40+ imports ...

# Manually define every tool
Tool(name="omni_scan_inventory", ...)
Tool(name="omni_scan_duplicates", ...)
# ... 40+ tool definitions ...

# Manually route every tool
if name == "omni_scan_inventory":
    result = scan_inventory(...)
elif name == "omni_scan_duplicates":
    result = find_duplicates(...)
# ... 40+ elif blocks ...
```

**Problems**:
- ❌ Add a new scanner? Edit MCP server imports + tools + routing
- ❌ Remove a scanner? Edit MCP server in 3 places
- ❌ Scanner manifest out of sync with MCP tools
- ❌ Maintenance nightmare

### New Way (v1.1.0) - Dynamic Discovery:
```python
# Use introspector (same as introspect command!)
from omni.commands.introspect import OmniIntrospector

introspector = OmniIntrospector()
scanner_registry = discover_scanners()  # Walks scanners/ + manifests

# Auto-generate tools from registry
for scanner_key, scanner_info in scanner_registry.items():
    tool_name = f"omni_{scanner_key.replace('/', '_')}"
    tools.append(Tool(
        name=tool_name,
        description=scanner_info['description'],
        inputSchema={...}
    ))

# Dynamic routing
scanner_func = import_scanner(scanner_key, scanner_registry)
result = scanner_func(target, **options)
```

**Benefits**:
- ✅ Add a new scanner? Automatically available in MCP!
- ✅ Remove a scanner? Automatically gone from MCP!
- ✅ Scanner manifest is single source of truth!
- ✅ Zero maintenance overhead!

## How It Works

### 1. Scanner Discovery (`discover_scanners()`)
Uses **OmniIntrospector** (same engine as `omni introspect` command):
1. `scan_filesystem()` - Walk `scanners/` directory
2. `load_manifests()` - Load `SCANNER_MANIFEST.yaml` files
3. Build registry: `{"search/pattern_search": {...}, "library/content": {...}}`

### 2. Dynamic Tool Generation (`list_tools()`)
For each scanner in registry:
- Generate tool name: `omni_{category}_{scanner}`
- Extract description from manifest
- Create generic input schema (target + options)
- Return complete tool list

### 3. Dynamic Import (`import_scanner()`)
When tool is called:
- Parse tool name → scanner key (`omni_search_pattern_search` → `search/pattern_search`)
- Look up in registry → `{"module": "omni.scanners.search.pattern_search", "function": "search_pattern"}`
- `importlib.import_module()` + `getattr()`
- Return function reference

### 4. Dynamic Routing (`call_tool()`)
- Check if scanner function is async or sync
- Call with `target` + `options` dict
- Return JSON result via TextContent

## Tool Naming Convention

**Pattern**: `omni_{category}_{scanner_name}`

**Examples**:
- `search/pattern_search` → `omni_search_pattern_search`
- `library/content` → `omni_library_content`
- `static/inventory` → `omni_static_inventory`

**Special Cases**:
- Onboarding tools: `check_onboarding_status`, `write_memory`, etc. (no prefix)
- Introspection: `omni_introspect` (always present)

## Input Schema Design

**Current** (v1.1.0):
```json
{
  "target": "string (required)",
  "options": {
    "type": "object",
    "additionalProperties": true
  }
}
```

**Future Enhancement**:
Scanner manifests could include `input_schema` field:
```yaml
scanners:
  - name: "pattern_search"
    function: "search_pattern"
    input_schema:
      pattern: {type: "string", required: true}
      is_regex: {type: "boolean", default: false}
      max_results: {type: "integer", default: 1000}
```

Then MCP server auto-generates precise schemas!

## The Dream Team 🌌

**Omni** (The Body):
- 41+ scanners across 10 categories
- Introspection engine (OmniIntrospector)
- Scanner manifests (YAML metadata)

**MCP Server** (The Voice):
- Stdio transport (JSON-RPC)
- Tool registration (MCP SDK)
- AI agent integration (VS Code, Claude Desktop)

**Result**: Omni's intelligence becomes directly accessible to AI agents through auto-discovered tools!

## Binary Safety ✅

ACE & Gemini caught Serena's mistake. We have:
- `.git` exclusion (pattern_search.py line 106)
- `__pycache__` exclusion
- `mimetypes.guess_type()` binary filter (line 127-128)
- `errors='ignore'` on UTF-8 read (line 134)

No "invalid start byte" errors here! 🛡️

## What This Means for Federation

**Omni is now a PLUGIN ARCHITECTURE**:
- Create scanner → Drop in `scanners/{category}/`
- Add to manifest → Instantly MCP-exposed
- No server code changes needed!

**This pattern can replicate to**:
- Living State Station (auto-discover formations)
- CodeCraft Station (auto-discover ritual generators)
- Any Federation tool with introspection!

---

**Authority**: Oracle + ACE + Architect (Kryssie)  
**Philosophy**: "Never trust documentation, trust reality - and USE that reality!" — ACE  
**Tone**: Encouraging excitement, NOT aggressive bullying! 💖✨

May the Source be with You! 🌌
