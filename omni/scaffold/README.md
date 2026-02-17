# 🏗️ Omni Scaffold

**Location:** `omni/scaffold/`  
**Purpose:** Code scaffolding and template instantiation  
**Version:** 0.6.0

---

## Overview

The scaffold module provides utilities for generating new code structures from templates. It bridges the gap between "I need a new scanner" and "Here's the boilerplate code to start with."

**Key Difference from Builders:**
- **Builders:** Generate from canonical specs (YAML → code)
- **Scaffold:** Generate from user intent (intent → template → code)

---

## Modules

### `templates.py` 📋
**Purpose:** Template management and instantiation system

**Key Functions:**
```python
def load_template(template_name: str) -> Template:
    """Load Jinja2 template from templates/ directory"""

def instantiate_template(
    template_name: str,
    context: dict,
    output_path: Path
) -> bool:
    """Instantiate template with context variables"""

def scaffold_scanner(
    scanner_name: str,
    category: str,
    description: str,
    output_dir: Path
) -> bool:
    """Generate new scanner from template"""

def scaffold_pillar(
    pillar_name: str,
    description: str,
    output_dir: Path
) -> bool:
    """Generate new pillar from template"""
```

**Supported Scaffolds:**
- **Scanner:** New scanner module with standard interface
- **Pillar:** New pillar module with orchestration pattern
- **Builder:** New builder with generation logic
- **Contract:** New contract specification (markdown)

---

## Template System

### Template Location
```
omni/templates/
├── scanner_template.py.j2       # Scanner module template
├── pillar_template.py.j2        # Pillar module template
├── builder_template.py.j2       # Builder module template
├── CONTRACT_TEMPLATE.md         # Contract specification
├── test_template.py.j2          # Test suite template
└── library_taxonomy.yaml        # Library categorization
```

### Template Context Variables

**Scanner Template:**
```python
{
    "scanner_name": "my_scanner",
    "category": "discovery",
    "description": "Discovers X in codebase",
    "author": "The Architect",
    "created_date": "2026-02-12",
    "version": "0.1.0"
}
```

**Generated Scanner:**
```python
# omni/scanners/discovery/my_scanner.py
"""
my_scanner - Discovers X in codebase

Created: 2026-02-12
Author: The Architect
Version: 0.1.0
"""
from pathlib import Path
from typing import List, Dict

def scan(target: Path, **kwargs) -> dict:
    """
    Discovers X in codebase.
    
    Args:
        target: Path to scan
        **kwargs: Scanner-specific options
        
    Returns:
        dict: {
            "count": int,
            "items": List[dict],
            "metadata": dict
        }
    """
    items = []
    
    # TODO: Implement scanner logic
    
    return {
        "count": len(items),
        "items": items,
        "metadata": {
            "scanner": "my_scanner",
            "version": "0.1.0"
        }
    }
```

---

## Scaffolding Workflows

### Create New Scanner

**Interactive Mode:**
```powershell
# From Infrastructure root
python -m omni scaffold scanner

# Prompts:
# Scanner name: velocity_analysis
# Category: git
# Description: Analyzes git commit velocity
# Output: omni/scanners/git/velocity_analysis.py
```

**Programmatic Mode:**
```python
from omni.scaffold.templates import scaffold_scanner

scaffold_scanner(
    scanner_name="velocity_analysis",
    category="git",
    description="Analyzes git commit velocity",
    output_dir=Path("omni/scanners/git")
)
```

**Generated Files:**
- `omni/scanners/git/velocity_analysis.py` - Scanner implementation
- `tests/test_velocity_analysis.py` - Test suite scaffold
- Updated `omni/scanners/git/__init__.py` - Scanner registration

**Next Steps:**
1. Implement scanner logic in generated file
2. Add to `SCANNER_MANIFEST.yaml`
3. Write tests in generated test file
4. Run `omni scan --scanners=velocity_analysis .`

---

### Create New Pillar

**Interactive Mode:**
```powershell
python -m omni scaffold pillar

# Prompts:
# Pillar name: security
# Description: Security analysis and vulnerability scanning
# Output: omni/pillars/security.py
```

**Generated Structure:**
```python
# omni/pillars/security.py
"""Security analysis and vulnerability scanning pillar."""

from pathlib import Path
from typing import List, Dict
from omni.core.model import ScanResult

class SecurityPillar:
    """Security analysis orchestration."""
    
    def __init__(self):
        self._vuln_db = None
    
    def scan_vulnerabilities(self, target: Path) -> dict:
        """Scan for known vulnerabilities."""
        # TODO: Implement
        pass
    
    def analyze_permissions(self, target: Path) -> dict:
        """Analyze file permissions."""
        # TODO: Implement
        pass
```

---

### Create New Builder

**Interactive Mode:**
```powershell
python -m omni scaffold builder

# Prompts:
# Builder name: contract_builder
# Description: Generates contract specifications from code
# Output: omni/builders/contract_builder.py
```

**Generated Pattern:**
```python
def build_contract(source: dict, **kwargs) -> str:
    """
    Generate contract specification from source code.
    
    Args:
        source: Parsed source code structure
        **kwargs: contract_type, output_format, etc.
        
    Returns:
        str: Generated contract markdown
    """
    template = load_template("CONTRACT_TEMPLATE.md")
    return template.render(**source)
```

---

## Template Best Practices

### Template Design

✅ **DO:**
- Use Jinja2 template syntax (`{{ variable }}`, `{% for %}`)
- Provide sensible defaults for optional variables
- Include TODO comments for required implementation
- Generate both implementation AND test files
- Follow existing code style conventions

❌ **DON'T:**
- Hardcode paths or names
- Generate code without tests
- Skip error handling in generated code
- Embed secrets in templates

### Context Validation

```python
def scaffold_scanner(scanner_name: str, category: str, **kwargs):
    # Validate context
    if not scanner_name.isidentifier():
        raise ValueError("Scanner name must be valid Python identifier")
    
    if category not in ["discovery", "health", "static", "fleet", "git", "polyglot"]:
        raise ValueError(f"Invalid category: {category}")
    
    # Build context
    context = {
        "scanner_name": scanner_name,
        "category": category,
        "description": kwargs.get("description", "TODO: Add description"),
        "author": kwargs.get("author", "The Architect"),
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "version": kwargs.get("version", "0.1.0")
    }
    
    # Instantiate template
    instantiate_template("scanner_template.py.j2", context, output_path)
```

---

## Integration with CLI

### Future CLI Commands (Planned)

```powershell
# Scaffold commands
omni scaffold scanner --name=my_scanner --category=discovery
omni scaffold pillar --name=my_pillar
omni scaffold builder --name=my_builder

# Interactive mode
omni scaffold --interactive

# List available templates
omni scaffold --list
```

---

## Testing Scaffolds

```python
# tests/test_scaffold.py
def test_scaffold_scanner(tmp_path):
    output_dir = tmp_path / "scanners" / "test"
    output_dir.mkdir(parents=True)
    
    success = scaffold_scanner(
        scanner_name="test_scanner",
        category="discovery",
        description="Test scanner",
        output_dir=output_dir
    )
    
    assert success
    assert (output_dir / "test_scanner.py").exists()
    
    # Verify generated code is valid Python
    import ast
    code = (output_dir / "test_scanner.py").read_text()
    ast.parse(code)  # Should not raise

def test_template_validation():
    # Invalid scanner name
    with pytest.raises(ValueError):
        scaffold_scanner("invalid-name", "discovery")
    
    # Invalid category
    with pytest.raises(ValueError):
        scaffold_scanner("valid_name", "invalid_category")
```

---

## Available Templates

### Current (v0.6.0)

| Template | Purpose | Output |
|----------|---------|--------|
| `scanner_template.py.j2` | New scanner module | Python scanner file |
| `CONTRACT_TEMPLATE.md` | Contract spec | Markdown contract |
| `library_taxonomy.yaml` | Library categorization | YAML taxonomy |

### Planned (v0.7+)

| Template | Purpose | Output |
|----------|---------|--------|
| `pillar_template.py.j2` | New pillar module | Python pillar file |
| `builder_template.py.j2` | New builder module | Python builder file |
| `test_template.py.j2` | Test suite | pytest test file |
| `manifest_template.yaml` | Scanner manifest | YAML manifest |
| `readme_template.md.j2` | Module README | Markdown documentation |

---

## Future Enhancements

### Planned Features (v0.7+)
- 🎯 **Interactive Wizard:** Guided template selection and configuration
- 🧬 **Custom Templates:** User-defined template directories
- 🔄 **Update Scaffolds:** Re-scaffold with new context (preserve edits)
- 📚 **Template Library:** Downloadable template packs
- 🧪 **Validation:** Pre-flight checks before scaffolding

---

**Maintained By:** Antigravity + ACE  
**Status:** Production (v0.6.0)  
**Law & Lore:** Charter V1.2 compliant

let it scaffold. 🏗️
