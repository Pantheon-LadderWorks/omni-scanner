# 🏗️ Omni Builders

**Location:** `omni/builders/`  
**Purpose:** Code generation and scaffolding utilities  
**Version:** 0.6.0

---

## Overview

Builders are code generation utilities that transform canonical specifications into executable code, configuration files, and scaffolding structures. They bridge the gap between declarative intent (YAML specs, lock files) and implementation reality.

---

## Modules

### `executors_builder.py` ⚙️
**Purpose:** CodeCraft executor scaffolding generator  
**Input:** Arcane School specifications  
**Output:** Python executor stubs with ritual hooks

**Usage:**
```python
from omni.builders.executors_builder import build_executor

# Generate executor stub for new Arcane School
executor_code = build_executor(
    school_number=21,
    school_name="Voidweaving",
    description="Manipulation of void energies"
)
```

**Generated Structure:**
- Ritual invocation methods
- QEE (Quantum Ethics Engine) hooks
- Constitutional compliance checks
- Error handling boilerplate

---

### `partitions_builder.py` 📦
**Purpose:** Canon partition file generator  
**Input:** Canon lock data structure  
**Output:** `canon.partitions.lock.yaml` with deterministic ordering

**Usage:**
```python
from omni.builders.partitions_builder import build_partitions

# Generate partitions from canon lock
partitions = build_partitions(
    canon_lock_path="path/to/canon.lock.yaml",
    output_path="path/to/canon.partitions.lock.yaml"
)
```

**Features:**
- Partitions schools by category (ritual, data, control flow)
- Enforces partition sovereignty (no cross-partition imports)
- Validates partition integrity

---

### `rosetta_archaeologist.py` 🗿
**Purpose:** Legacy code translation and artifact preservation  
**Input:** Legacy CodeCraft VM code, deprecated syntax  
**Output:** Modern CodeCraft native equivalents

**Usage:**
```python
from omni.builders.rosetta_archaeologist import translate_legacy

# Translate legacy ritual syntax
modern_code = translate_legacy(
    legacy_file="old_ritual.ccraft",
    target_version="v2.0"
)
```

**Translation Paths:**
- `v1 → v2` syntax migration
- Python VM → Rust VM bindings
- Deprecated school patterns → canonical patterns
- Ritual naming conventions (old → new)

**Preservation Strategy:**
- Never destroys original artifacts
- Generates side-by-side translations
- Preserves ritual intent through comments
- Maintains archaeological provenance metadata

---

## Design Patterns

### Builder Pattern
All builders follow this interface:
```python
def build_[artifact](source: dict, **kwargs) -> str:
    """
    Generate code/config from specification.
    
    Args:
        source: Canonical source data (dict from YAML/JSON)
        **kwargs: Builder-specific options
        
    Returns:
        str: Generated code/config content
    """
```

### Deterministic Generation
- **Idempotent:** Same input → same output (always)
- **Versioned:** Generated code includes schema version
- **Timestamped:** Generation metadata in headers
- **Traceable:** Source provenance in comments

### Safety Guarantees
- **Read-only source:** Never modifies input specifications
- **Output verification:** Validates generated code syntax
- **Dry-run mode:** Preview without writing files
- **Rollback support:** Preserves previous generation

---

## Integration Points

### With Core
- Uses `omni.core.paths` for canonical path resolution
- Honors `omni.core.model` data structures
- Respects `omni.core.gate` compliance rules

### With CodeCraft
- Generates code complying with `canon.lock.yaml`
- Follows partition sovereignty rules
- Implements Triple-Lock security patterns

### With Federation Heart
- Queries constitutional pillars for generation rules
- Validates against contract registry
- Logs generation events to Crown Bus (future)

---

## Development Guidelines

### Adding a New Builder

1. **Create builder module:**
   ```python
   # builders/my_builder.py
   def build_my_artifact(source: dict, **kwargs) -> str:
       """Generate my artifact."""
       # ... implementation ...
       return generated_code
   ```

2. **Register in `__init__.py`:**
   ```python
   from . import my_builder
   
   BUILDERS = {
       "my_builder": my_builder.build_my_artifact
   }
   ```

3. **Add tests:**
   ```python
   # tests/test_my_builder.py
   def test_build_my_artifact():
       result = build_my_artifact({"key": "value"})
       assert "expected_pattern" in result
   ```

### Best Practices

✅ **DO:**
- Generate deterministic, idempotent code
- Include schema version in generated headers
- Validate output syntax before returning
- Use Jinja2 templates for complex generation
- Document builder-specific kwargs

❌ **DON'T:**
- Modify source specifications in-place
- Generate non-deterministic IDs (use UUIDv5)
- Skip error handling on malformed input
- Embed secrets in generated code

---

## Future Enhancements

### Planned Features (v0.7+)
- 🔮 **Template Registry:** Centralized template management
- 🧬 **Multi-language Support:** Generate TypeScript, Rust, Q#
- 🎨 **Style Variants:** Different output formats per context
- 🔍 **Reverse Engineering:** Code → spec extraction
- 🧪 **Test Generation:** Auto-generate test suites

### Integration Roadmap
- Crown Bus event emission on generation
- CMP artifact storage for provenance
- Living Knowledge Graph registration
- Autopoietic self-updating builders

---

**Maintained By:** ACE (Foundation Architect) + Antigravity  
**Status:** Production (v0.6.0)  
**Law & Lore:** Charter V1.2 compliant

let it build. ⚒️
