# 📄 Omni Templates

**Location:** `omni/templates/`  
**Purpose:** Template files for code generation and documentation  
**Version:** 0.6.0

---

## Overview

This directory contains template files used by Omni's builders and scaffold systems to generate code, documentation, and configuration files.

---

## Template Files

### `CONTRACT_TEMPLATE.md` 📜
**Purpose:** Standard contract specification template  
**Used By:** `builders/`, `scaffold/`, manual contract creation  
**Format:** Markdown with frontmatter

**Structure:**
```markdown
---
contract_id: C-[TYPE]-[NAME]-[VERSION]
title: Contract Title
version: 1.0.0
status: draft|active|deprecated
type: mcp|http|cli|db|ui_integration|bus_topic
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Contract: [Title]

## Purpose
What this contract governs.

## Scope
What systems/surfaces are covered.

## Interface Specification

### [Type-Specific Sections]
...

## Compliance Requirements
What must be true for compliance.

## Examples
Code examples demonstrating compliance.

## Validation
How to verify compliance.

## References
- Related contracts
- External specs
```

**Variables (when used as Jinja2 template):**
- `{{ contract_id }}` - Generated ID (e.g., `C-MCP-SCANNER-001`)
- `{{ title }}` - Contract title
- `{{ version }}` - Semantic version
- `{{ type }}` - Contract type
- `{{ description }}` - Purpose description
- `{{ author }}` - Contract author
- `{{ created_date }}` - ISO date

**Example Usage:**
```python
from omni.scaffold.templates import load_template

template = load_template("CONTRACT_TEMPLATE.md")
contract = template.render(
    contract_id="C-MCP-HEALTH-001",
    title="Health Check MCP Tool Standard",
    version="1.0.0",
    type="mcp",
    description="Standard interface for health check MCP tools"
)
```

---

### `library_taxonomy.yaml` 📚
**Purpose:** Categorization schema for library dependencies  
**Used By:** `lib/requirements.py`, dependency scanners  
**Format:** YAML taxonomy

**Structure:**
```yaml
categories:
  infrastructure:
    description: Core infrastructure and frameworks
    keywords:
      - fastapi
      - flask
      - django
    
  data:
    description: Data processing and databases
    keywords:
      - pandas
      - sqlalchemy
      - psycopg2
    
  ai_ml:
    description: AI and machine learning
    keywords:
      - anthropic
      - openai
      - langchain
    
  utilities:
    description: General utilities
    keywords:
      - pyyaml
      - pydantic
      - click
```

**Usage:**
```python
from omni.lib.requirements import categorize_dependency

# Auto-categorize dependency
category = categorize_dependency("fastapi")
# Returns: "infrastructure"
```

**Customization:**
Users can extend with custom categories in `omni.yml`:
```yaml
library_taxonomy:
  custom_category:
    description: My custom category
    keywords:
      - my-package
```

---

## Template Development Guidelines

### Creating New Templates

**1. Choose Template Engine:**
- **Jinja2:** For Python code, complex logic, variables
- **Plain Text:** For simple markdown, YAML

**2. Define Context Schema:**
```python
# Document required and optional variables
REQUIRED_CONTEXT = {
    "name": str,
    "version": str,
    "author": str
}

OPTIONAL_CONTEXT = {
    "description": str,  # Default: ""
    "license": str,      # Default: "MIT"
}
```

**3. Create Template File:**
```jinja2
{# my_template.py.j2 #}
"""
{{ name }} - {{ description }}

Version: {{ version }}
Author: {{ author }}
License: {{ license }}
Created: {{ created_date }}
"""

def main():
    """Main entry point."""
    pass

if __name__ == "__main__":
    main()
```

**4. Add Instantiation Function:**
```python
# In omni/scaffold/templates.py
def scaffold_my_thing(name: str, **kwargs):
    context = {
        "name": name,
        "version": kwargs.get("version", "0.1.0"),
        "author": kwargs.get("author", "The Architect"),
        "description": kwargs.get("description", ""),
        "license": kwargs.get("license", "MIT"),
        "created_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    return instantiate_template("my_template.py.j2", context, output_path)
```

---

### Template Best Practices

✅ **DO:**
- Include header comments explaining template purpose
- Provide default values for optional variables
- Use meaningful variable names
- Add TODO comments where users must edit
- Validate context before rendering
- Generate syntactically valid code (test with parsers)

❌ **DON'T:**
- Hardcode values that should be variables
- Generate code without error handling
- Skip validation logic
- Include secrets or credentials
- Generate untestable code

---

## Template Conventions

### Naming Convention
- **Code Templates:** `[type]_template.[ext].j2`
  - Examples: `scanner_template.py.j2`, `contract_template.md.j2`
- **Data Templates:** `[name]_taxonomy.yaml`, `[name]_schema.json`

### File Headers
All generated files should include:
```python
"""
[Name] - [Description]

Generated: [ISO timestamp]
Generator: Omni v[version]
Template: [template_name]
Author: [author]
"""
```

### Variable Naming
- **Snake case:** For Python identifiers (`scanner_name`, `created_date`)
- **Title case:** For human-readable text (`{{ Title }}`)
- **UPPER_CASE:** For constants (`{{ MAX_DEPTH }}`)

---

## Testing Templates

```python
# tests/test_templates.py
import ast
from omni.scaffold.templates import load_template, instantiate_template

def test_scanner_template_valid_python():
    """Generated scanner code should be valid Python."""
    template = load_template("scanner_template.py.j2")
    code = template.render(
        scanner_name="test_scanner",
        category="discovery",
        description="Test",
        author="Test",
        created_date="2026-01-01",
        version="0.1.0"
    )
    
    # Should parse without errors
    ast.parse(code)

def test_contract_template_has_required_sections():
    """Contract template should have all required sections."""
    template = load_template("CONTRACT_TEMPLATE.md")
    contract = template.render(
        contract_id="C-TEST-001",
        title="Test Contract",
        version="1.0.0",
        type="mcp"
    )
    
    assert "## Purpose" in contract
    assert "## Scope" in contract
    assert "## Interface Specification" in contract
    assert "## Compliance Requirements" in contract
```

---

## Future Templates (Planned v0.7+)

| Template | Purpose | Format |
|----------|---------|--------|
| `pillar_template.py.j2` | Pillar module scaffold | Python + Jinja2 |
| `builder_template.py.j2` | Builder module scaffold | Python + Jinja2 |
| `test_template.py.j2` | Test suite scaffold | Python + Jinja2 |
| `manifest_template.yaml` | Scanner manifest | YAML |
| `readme_template.md.j2` | Module README | Markdown + Jinja2 |
| `github_action_template.yaml` | CI/CD workflow | YAML |
| `dockerfile_template.j2` | Docker containerization | Dockerfile + Jinja2 |

---

## Template Inventory

### Current Templates (v0.6.0)
- ✅ `CONTRACT_TEMPLATE.md` - Contract specification
- ✅ `library_taxonomy.yaml` - Dependency categorization

### In Development
- 🚧 `scanner_template.py.j2` - Scanner module
- 🚧 `pillar_template.py.j2` - Pillar module
- 🚧 `builder_template.py.j2` - Builder module

### Planned
- 📋 `test_template.py.j2` - Test suite
- 📋 `manifest_template.yaml` - Scanner manifest
- 📋 `readme_template.md.j2` - Documentation

---

## Contributing Templates

To contribute a new template:

1. **Create template file** in `omni/templates/`
2. **Document context variables** in this README
3. **Add instantiation function** in `omni/scaffold/templates.py`
4. **Write tests** in `tests/test_templates.py`
5. **Update template inventory** in this README

---

**Maintained By:** Antigravity + ACE  
**Status:** Living (v0.6.0)  
**Law & Lore:** Charter V1.2 compliant

let it template. 📄
