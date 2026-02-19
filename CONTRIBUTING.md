# 🤝 Contributing to Omni

> *"Every scanner that joins the Sensorium makes the Eye see further."*

Welcome, traveler. Whether you're extending Omni's perception with a new scanner, sharpening its pillars, or refining its documentation — you're building the All-Seeing Eye.

---

## ⚡ Quick Setup

```bash
# Clone the repository
git clone https://github.com/Pantheon-LadderWorks/omni.git
cd omni

# Install in editable mode (no venv — global user install)
pip install --user -e .

# Verify installation
omni introspect
```

> [!NOTE]
> Omni follows the **NO VENV** doctrine. All packages are installed to the global user space. See `GEMINI.md` for environmental policy.

---

## 🔍 Adding a New Scanner

This is the most common contribution. Omni's plugin system makes it straightforward.

### Step 1: Choose Your Category

| Category        | For Scanners That...                                |
| :-------------- | :-------------------------------------------------- |
| `static/`       | Analyze filesystem structure without runtime deps   |
| `architecture/` | Enforce structural rules (imports, coupling, drift) |
| `discovery/`    | Find and catalog components, projects, services     |
| `polyglot/`     | Parse language-specific package ecosystems          |
| `library/`      | Perform document intelligence and analysis          |
| `git/`          | Inspect git repositories and history                |
| `search/`       | Search files for patterns, text, or UUIDs           |
| `db/`           | Scan database schemas via configuration             |

> [!IMPORTANT]
> **Federation-exclusive categories** (`database/`, `fleet/`, `health/`, `phoenix/`) require the Federation Heart and are not included in the open-source build. If your scanner needs Federation services, place it in the appropriate exclusive category.

### Step 2: Create the Scanner File

Create `omni/scanners/<category>/my_scanner.py`:

```python
"""
🔍 My Scanner — [One-line description]

Contract: C-TOOLS-OMNI-SCANNER-001 (read-only, safe failure)
Category: [category]
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def scan(target: Path) -> Dict[str, Any]:
    """
    Scan the target directory for [what you're looking for].
    
    Args:
        target: Directory path to scan
        
    Returns:
        Dict with scanner results following the standard output format
    """
    items = []
    
    # Your scanning logic here
    # RULE: Never modify files. Read only.
    for path in target.rglob("*.ext"):
        items.append({
            "path": str(path),
            "type": "finding_type",
            # ... scanner-specific fields
        })
    
    return {
        "scanner": "my_scanner",
        "category": "category_name",
        "target": str(target),
        "timestamp": datetime.now().isoformat(),
        "count": len(items),
        "items": items
    }
```

### Step 3: Register in the Manifest

Add your scanner to `omni/scanners/<category>/SCANNER_MANIFEST.yaml`:

```yaml
scanners:
  # ... existing scanners ...
  - name: my_scanner
    file: my_scanner.py
    function: scan
    description: "One-line description of what this scanner detects"
```

### Step 4: Add Tests

Create `tests/test_scanners/test_my_scanner.py`:

```python
"""Tests for my_scanner."""
import pytest
from pathlib import Path
from omni.scanners.<category>.my_scanner import scan


def test_scan_finds_items(tmp_path):
    """Scanner should find expected items."""
    # Setup: create test fixtures
    test_file = tmp_path / "test.ext"
    test_file.write_text("content")
    
    # Execute
    result = scan(tmp_path)
    
    # Verify
    assert result["count"] > 0
    assert result["scanner"] == "my_scanner"
    assert len(result["items"]) == 1


def test_scan_empty_directory(tmp_path):
    """Scanner should handle empty directories gracefully."""
    result = scan(tmp_path)
    assert result["count"] == 0
    assert result["items"] == []
```

### Step 5: Update Documentation

1. Update the category's `README.md` (e.g., `omni/scanners/<category>/README.md`)
2. Add a brief entry to `omni/scanners/README.md` if creating a new category

### Step 6: Verify

```bash
# Check that Omni discovers your scanner
omni introspect

# Run the scanner
omni scan . --scanner my_scanner

# Run your tests
pytest tests/test_scanners/test_my_scanner.py -v
```

---

## 🏛️ Adding a New Pillar

Pillars are less common contributions. Only add a pillar when you need to **orchestrate multiple scanners** into a higher-level capability.

### When to Create a Pillar (vs. a Scanner)

| Situation                          | Use        |
| :--------------------------------- | :--------- |
| Single concern, single data source | Scanner    |
| Combining 2+ scanner outputs       | Pillar     |
| Stateless observation              | Scanner    |
| Needs state or configuration       | Pillar     |
| Utility function                   | Lib module |

### Pillar Template

```python
"""
🏛️ My Pillar — [Description]

Orchestrates: [list of scanners used]
"""

from pathlib import Path
from omni.core.paths import get_infrastructure_root
from omni.lib.io import safe_read_file


def my_operation(target: Path) -> dict:
    """
    Perform the pillar operation.
    
    This pillar combines data from [scanner A] and [scanner B]
    to produce [higher-level intelligence].
    """
    # Import scanners as needed
    from omni.scanners import SCANNERS
    
    scan_a = SCANNERS.get("scanner_a")
    scan_b = SCANNERS.get("scanner_b")
    
    result_a = scan_a(target) if scan_a else {}
    result_b = scan_b(target) if scan_b else {}
    
    # Synthesize
    return {
        "intelligence": "combined analysis",
        "sources": ["scanner_a", "scanner_b"]
    }
```

---

## 🧩 Code Patterns to Follow

### The Shim Pattern
Never import the Federation Heart directly. Always go through `omni.config.settings`:

```python
# ✅ Do this
from omni.core.paths import get_infrastructure_root

# ❌ Never do this
from federation_heart.pillars.cartography import CartographyPillar
```

### Error Resilience
- **Lib modules**: Never raise exceptions. Return `None`, `False`, or empty defaults.
- **Scanners**: May raise on invalid input, but handle file I/O errors gracefully.
- **Core**: May raise on critical integrity violations (identity conflicts).

### UTF-8 Safety
Always use `omni.lib.io` for file operations:

```python
from omni.lib.io import safe_read_file, safe_write_file

content = safe_read_file(path)  # Returns None on failure, never raises
```

---

## 🎨 Code Style

- **Python 3.8+** compatibility
- **Type hints** on all public functions
- **Docstrings** on all public functions (Google style)
- **Module docstrings** with scanner contract references
- No external dependencies in scanners unless absolutely necessary (prefer stdlib)

---

## 📋 PR Checklist

Before submitting:

- [ ] Scanner follows the `scan(target: Path) -> dict` contract
- [ ] Scanner is registered in `SCANNER_MANIFEST.yaml`
- [ ] Scanner is read-only (no file modifications)
- [ ] Tests exist and pass (`pytest tests/ -v`)
- [ ] Category README updated
- [ ] `omni introspect` shows new scanner with zero drift
- [ ] No hardcoded paths (use `omni.core.paths`)
- [ ] No direct Federation Heart imports (use the shim)

---

## 🌊 Branching Strategy

- `main` — stable release branch
- Feature branches — `feature/scanner-name` or `feature/description`
- Bug fixes — `fix/description`

---

## 🛡️ Community Standards

- Be constructive and welcoming
- Focus on code quality and architectural integrity
- Assume good intent
- All scanners must preserve the read-only guarantee

---

<p align="center">
  <em>Every new scanner widens the Eye's gaze.</em><br/>
  <strong>Welcome to the Sensorium.</strong> ✨
</p>
