# ⚙️ Omni Configuration

**Location:** `omni/config/`  
**Purpose:** Configuration management and Federation Heart bridge  
**Version:** 0.7.0

---

## Overview

The configuration module manages Omni's runtime settings, bridges to the Federation Heart, and provides fallback standalone operation when core infrastructure is unavailable.

---

## Modules

### `settings.py` 📋
**Purpose:** Global Omni configuration management  
**Type:** Settings loader and validator

**Configuration Sources (Priority Order):**
1. Environment variables (`.env`)
2. `omni.yml` configuration file
3. Default settings (hardcoded fallbacks)

**Key Settings:**
```python
class OmniSettings:
    # Paths
    infrastructure_root: Path
    artifacts_dir: Path
    registry_root: Path
    
    # Scan behavior
    exclude_patterns: List[str]  # Default: node_modules, .git, __pycache__
    max_depth: int               # Default: 10
    follow_symlinks: bool        # Default: False
    
    # Output
    output_format: str           # json|yaml|text (default: json)
    pretty_print: bool           # Default: True
    
    # Integration
    federation_heart_enabled: bool  # Auto-detected
    cmp_database_enabled: bool      # Auto-detected
```

**Example `omni.yml`:**
```yaml
scan:
  exclude:
    - "node_modules"
    - "external-frameworks"
    - ".venv"
  patterns:
    generic_events:
      - "\\.publish\\("
      - "crown://"
  max_depth: 15

output:
  format: json
  pretty_print: true

integration:
  federation_heart: true
  cmp_database: true
```

**Usage:**
```python
from omni.config.settings import OmniSettings

settings = OmniSettings.load()
if settings.federation_heart_enabled:
    # Use full federation features
else:
    # Standalone mode
```

---

## Configuration Patterns

### Environment Variable Mapping

```bash
# .env file (deferred loading - only when needed)
POSTGRES_HOST=localhost        # CMP database
POSTGRES_PORT=5433
POSTGRES_DB=cms_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<secret>

OMNI_EXCLUDE_PATTERNS=node_modules,.git,__pycache__
OMNI_MAX_DEPTH=10
OMNI_OUTPUT_FORMAT=json
```

**Loading Strategy:**
- ❌ **NOT loaded at CLI startup** (prevents dependency bloat)
- ✅ **Loaded by specific scanners** (e.g., `cmp_health.py`)
- ✅ **Lazy evaluation** (only when truly needed)

### Federation Heart Bridge

**Purpose:** Connect Omni to Federation infrastructure pillars  
**Bridge Location:** `omni/core/config.py` (note: different from this `config/`)

**Lazy Loading Pattern:**
```python
# From omni/core/config.py
try:
    from federation_heart.constitution import load_constitution
    from federation_heart.cartography import load_cartography
    FEDERATION_AVAILABLE = True
except ImportError:
    FEDERATION_AVAILABLE = False
```

**Pillars Available When Connected:**
- **Constitution:** Governance manifest, contract registry
- **Cartography:** Ecosystem mapping, project relationships
- **Registry:** Canonical UUID resolution, project metadata

**Standalone Fallbacks:**
- **Constitution:** Read manifests directly from `governance/`
- **Cartography:** Basic filesystem walking
- **Registry:** Parse YAML registries without database

---

## Configuration Hierarchy

```
1. Hard-Coded Defaults (safe fallbacks)
    ↓
2. omni.yml (project-specific overrides)
    ↓
3. .env file (sensitive values, runtime overrides)
    ↓
4. CLI flags (highest priority, per-invocation)
```

**Example Override Chain:**
```python
# Default: exclude = ["node_modules"]
# omni.yml: exclude = ["node_modules", ".venv"]
# CLI: --exclude=build
# Final: ["node_modules", ".venv", "build"]
```

---

## Security Patterns

### Sensitive Data Handling

✅ **DO:**
- Store secrets in `.env` (gitignored)
- Use environment variables for credentials
- Validate paths before file operations
- Sanitize user input from CLI flags

❌ **DON'T:**
- Commit `.env` files to git
- Hardcode credentials in settings
- Log sensitive configuration values
- Trust unsanitized CLI input

### Safe Defaults

```python
# Safe defaults for scanning
SAFE_EXCLUDE_PATTERNS = [
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "build",
    "dist",
    ".env",
    "*.pyc",
    "*.log"
]

SAFE_MAX_DEPTH = 10  # Prevents infinite recursion
SAFE_FOLLOW_SYMLINKS = False  # Prevents loop attacks
```

---

## Integration Guidelines

### Adding New Settings

1. **Update `settings.py`:**
   ```python
   @dataclass
   class OmniSettings:
       # ... existing ...
       my_new_setting: str = "default_value"
   ```

2. **Add to `omni.yml` schema:**
   ```yaml
   # Document in README and .env.example
   my_feature:
     my_new_setting: "custom_value"
   ```

3. **Environment variable fallback:**
   ```python
   my_setting = os.getenv("OMNI_MY_NEW_SETTING", self.my_new_setting)
   ```

### Federation Heart Integration

**When to bridge:**
- Need constitutional governance data
- Require project relationship graphs
- Want canonical UUID resolution
- Need contract registry access

**When to stay standalone:**
- Quick local scans
- CI/CD environments without federation
- Bootstrap scenarios (chicken-egg problems)
- Testing in isolation

---

## Testing Configuration

```python
# tests/test_settings.py
def test_default_settings():
    settings = OmniSettings.load()
    assert "node_modules" in settings.exclude_patterns
    assert settings.max_depth == 10

def test_yml_override(tmp_path):
    config_file = tmp_path / "omni.yml"
    config_file.write_text("scan:\n  max_depth: 20")
    
    settings = OmniSettings.load(config_file)
    assert settings.max_depth == 20

def test_env_override(monkeypatch):
    monkeypatch.setenv("OMNI_MAX_DEPTH", "30")
    
    settings = OmniSettings.load()
    assert settings.max_depth == 30
```

---

## Troubleshooting

### Common Issues

**Problem:** "Federation Heart not found"  
**Solution:** Install federation_heart package OR use standalone mode

**Problem:** "CMP database connection failed"  
**Solution:** Check `.env` credentials, verify PostgreSQL running on port 5433

**Problem:** "Invalid omni.yml syntax"  
**Solution:** Validate YAML with `python -c "import yaml; yaml.safe_load(open('omni.yml'))"`

**Problem:** "Exclude patterns not working"  
**Solution:** Ensure patterns are in glob format (e.g., `*.pyc` not `pyc`)

---

**Maintained By:** Antigravity + ACE  
**Status:** Production (v0.6.0)  
**Law & Lore:** Charter V1.2 compliant

let it configure. ⚙️
