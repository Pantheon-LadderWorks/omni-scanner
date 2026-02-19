# 🧰 Omni Library (Shared Utilities)

**Location:** `omni/lib/`  
**Purpose:** Reusable utility functions for I/O, rendering, and analysis  
**Version:** 0.7.0

---

## Overview

The library module provides foundational utilities used across Omni's core, pillars, and scanners. These are the "tools in the toolbox" that every component can safely depend on without circular dependencies.

---

## Modules

### `io.py` 📁
**Purpose:** Safe file I/O with emoji support and error handling

**Key Functions:**
```python
def safe_read_file(path: Path, encoding: str = 'utf-8') -> str | None:
    """
    Read file with emoji safety and error handling.
    Returns None on error (never raises).
    """

def safe_write_file(path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """
    Write file with directory creation and error handling.
    Returns True on success, False on failure.
    """

def ensure_dir(path: Path) -> bool:
    """Create directory if not exists (idempotent)."""

def list_files(path: Path, pattern: str = "*", recursive: bool = True) -> List[Path]:
    """List files matching glob pattern with safe error handling."""
```

**Features:**
- **Emoji-safe UTF-8 handling:** Won't crash on Unicode symbols (🌌, 📜, etc.)
- **Windows-safe:** Properly handles Windows paths and encoding
- **Error resilience:** Returns None/False on errors instead of raising
- **Directory auto-creation:** `safe_write_file()` creates parent directories

**Usage Example:**
```python
from omni.lib.io import safe_read_file, safe_write_file

# Safe read (returns None on error)
content = safe_read_file(Path("config.yaml"))
if content:
    process(content)

# Safe write (creates dirs if needed)
success = safe_write_file(
    Path("artifacts/omni/scan.json"),
    json.dumps(data, indent=2)
)
```

---

### `renderer.py` 🎨
**Purpose:** Output formatting for console and file reports

**Key Functions:**
```python
def render_table(headers: List[str], rows: List[List[str]]) -> str:
    """Render ASCII table with aligned columns."""

def render_tree(root: Path, exclude: List[str] = None) -> str:
    """Render directory tree visualization."""

def render_json(data: dict, pretty: bool = True) -> str:
    """Render JSON with optional pretty printing."""

def render_yaml(data: dict) -> str:
    """Render YAML with safe dumping."""

def colorize(text: str, color: str) -> str:
    """Add ANSI color codes (for terminal output)."""
```

**Features:**
- **Multi-format support:** JSON, YAML, tables, trees
- **Pretty printing:** Human-readable formatting
- **Color support:** ANSI colors for terminal output
- **Width-aware:** Respects terminal width for tables

**Usage Example:**
```python
from omni.lib.renderer import render_table, render_json

# Render scan results as table
headers = ["Project", "UUID", "Status"]
rows = [
    ["omni", "abc-123", "✅"],
    ["codecraft", "def-456", "⚠️"]
]
print(render_table(headers, rows))

# Render JSON report
report = {"count": 42, "items": [...]}
json_output = render_json(report, pretty=True)
```

---

### `reporting.py` 📊
**Purpose:** Generate structured reports from scan results

**Key Functions:**
```python
def generate_summary(scan_result: ScanResult) -> dict:
    """Generate executive summary from scan results."""

def generate_findings_report(findings: List[ScanFinding]) -> str:
    """Generate detailed findings report (markdown)."""

def generate_compliance_report(scan_result: ScanResult, gate: Gate) -> dict:
    """Generate gate compliance report with pass/fail status."""

def export_to_markdown(scan_result: ScanResult, output_path: Path) -> bool:
    """Export scan results to markdown file."""
```

**Report Formats:**
- **Summary:** High-level metrics (count, risk, health)
- **Findings:** Detailed per-item analysis
- **Compliance:** Gate validation results
- **Markdown:** Human-readable documentation export

**Usage Example:**
```python
from omni.lib.reporting import generate_summary, export_to_markdown

# Generate summary
summary = generate_summary(scan_result)
print(f"Risk: {summary['risk']}, Total: {summary['total']}")

# Export to markdown
export_to_markdown(scan_result, Path("artifacts/omni/report.md"))
```

---

### `requirements.py` 📦
**Purpose:** Python dependency parsing and analysis

**Key Functions:**
```python
def parse_requirements_txt(path: Path) -> List[Requirement]:
    """Parse requirements.txt into structured format."""

def parse_pyproject_toml(path: Path) -> dict:
    """Parse pyproject.toml dependencies."""

def merge_requirements(sources: List[Path]) -> List[Requirement]:
    """Merge multiple requirement sources with deduplication."""

def lock_requirements(requirements: List[Requirement]) -> str:
    """Generate locked requirements with exact versions."""
```

**Features:**
- **Multi-format:** `requirements.txt`, `pyproject.toml`, `setup.py`
- **Version resolution:** Handle `>=`, `~=`, `==` operators
- **Deduplication:** Merge requirements from multiple files
- **Lock file generation:** Create `requirements.federation.locked.txt`

**Usage Example:**
```python
from omni.lib.requirements import parse_requirements_txt, lock_requirements

# Parse requirements
reqs = parse_requirements_txt(Path("requirements.txt"))

# Generate lock file
locked = lock_requirements(reqs)
safe_write_file(Path("requirements.locked.txt"), locked)
```

---

### `tap.py` ✅
**Purpose:** TAP (Test Anything Protocol) verification utilities

**Key Functions:**
```python
def verify_tap_output(output: str) -> dict:
    """
    Parse and verify TAP output.
    
    Returns:
        dict: {
            "valid": bool,
            "plan": tuple,  # (first, last)
            "tests": int,
            "passed": int,
            "failed": int,
            "skipped": int
        }
    """

def generate_tap_report(test_results: List[dict]) -> str:
    """Generate TAP-formatted output from test results."""
```

**TAP Format Support:**
```
1..42              # Test plan
ok 1 - Test passed
not ok 2 - Test failed
  ---
  message: 'Expected 5, got 3'
  severity: fail
  ...
ok 3 # SKIP Reason
```

**Usage Example:**
```python
from omni.lib.tap import verify_tap_output

tap_output = """
1..3
ok 1 - Federation health
ok 2 - Station health
not ok 3 - CMP health
"""

result = verify_tap_output(tap_output)
print(f"Passed: {result['passed']}/{result['tests']}")
```

---

### `tree.py` 🌳
**Purpose:** Directory tree generation with smart exclusions

**Key Functions:**
```python
def generate_tree(
    root: Path,
    exclude: List[str] = None,
    max_depth: int = 10,
    show_hidden: bool = False
) -> str:
    """Generate clean directory tree visualization."""

def tree_to_markdown(root: Path, **kwargs) -> str:
    """Generate tree in markdown format with code fence."""
```

**Features:**
- **Smart exclusions:** Auto-ignores `node_modules`, `.git`, `__pycache__`
- **Depth limiting:** Prevents infinite recursion
- **Hidden file handling:** Configurable `.dotfile` visibility
- **Markdown export:** Tree wrapped in markdown code fence

**Default Exclusions:**
```python
DEFAULT_EXCLUDE = [
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "build",
    "dist",
    ".egg-info",
    "*.pyc",
    "*.log"
]
```

**Usage Example:**
```python
from omni.lib.tree import generate_tree, tree_to_markdown

# Generate tree
tree = generate_tree(
    Path("omni"),
    exclude=["__pycache__", "*.pyc"],
    max_depth=3
)
print(tree)

# Export to markdown
md_tree = tree_to_markdown(Path("omni"))
safe_write_file(Path("STRUCTURE.md"), md_tree)
```

---

## Design Patterns

### Error Handling Philosophy

✅ **Lib modules NEVER raise exceptions** (return None/False instead)  
❌ **Core/Scanners MAY raise** (caller's responsibility)

**Rationale:** Libraries are defensive infrastructure. They should gracefully degrade, not crash the system.

```python
# Good: Returns None on error
content = safe_read_file(path)
if content is None:
    return {"error": "file not found"}

# Bad: Raises exception
content = open(path).read()  # Would crash on missing file
```

### Unicode Safety

All file I/O enforces UTF-8 encoding and handles emoji gracefully:

```python
# Windows console UTF-8 enforcement
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# File operations with explicit UTF-8
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
```

### Idempotent Operations

All write operations are idempotent (safe to call multiple times):

```python
# ensure_dir() is idempotent
ensure_dir(Path("artifacts/omni"))
ensure_dir(Path("artifacts/omni"))  # Safe, no-op

# safe_write_file() creates dirs if needed
safe_write_file(Path("new/path/file.txt"), "content")  # Creates new/, new/path/
```

---

### `artifacts.py` 📦
**Purpose:** Central logic for naming, locating, and managing Omni scan artifacts

**Key Functions:**
```python
def get_artifacts_root() -> Path:
    """Get the root directory for Omni artifacts."""

def get_scan_path(scanner: str, scope: str = "default", extension: str = "json") -> Path:
    """
    Generate the standard path for a scan artifact.
    Standard: scan.<scanner>.<scope>.json
    """

def get_latest_scan(scanner: str, scope: str = "*") -> Optional[Path]:
    """Find the most recent scan for a given scanner."""
```

**Features:**
- **Standard naming convention:** `scan.<scanner>.<scope>.json`
- **Auto-creates directories:** Parent directories created on-demand
- **Latest scan lookup:** Find most recent scan by timestamp

---

### `ast_util.py` 🌳
**Purpose:** Shared AST parsing and extraction logic for Python code analysis

**Key Functions:**
```python
def extract_imports(filepath: Path) -> List[Dict[str, Any]]:
    """Parse a Python file and extract all import statements."""

def extract_decorators(filepath: Path) -> List[Dict[str, Any]]:
    """Extract all decorators and their arguments."""
```

**Features:**
- **Import extraction:** Captures `import` and `from ... import` with line numbers
- **Decorator extraction:** Captures decorator names, arguments, and target functions
- **Error resilience:** Returns empty list on SyntaxError or encoding issues

---

### `files.py` 📂
**Purpose:** Standard logic for file system traversal and exclusion patterns

**Key Functions:**
```python
DEFAULT_EXCLUDES = {
    '__pycache__', '.git', '.venv', 'venv', 'node_modules',
    'dist', 'build', 'eggs', '.eggs', '*.egg-info',
    'archive', '.pytest_cache', '.vscode', '.idea'
}

def is_excluded(path: Path, excludes: Optional[Set[str]] = None) -> bool:
    """Check if a path matches exclusion patterns."""

def walk_project(
    root: Path,
    extensions: Optional[List[str]] = None,
    excludes: Optional[Set[str]] = None
) -> Generator[Path, None, None]:
    """Walk a directory tree yielding paths that match criteria."""
```

**Features:**
- **Smart exclusions:** Default excludes for common non-source directories
- **Extension filtering:** Include only specific file types
- **Generator-based:** Memory efficient for large codebases

---

## Testing Utilities

```python
# tests/test_io.py
def test_safe_read_nonexistent(tmp_path):
    result = safe_read_file(tmp_path / "missing.txt")
    assert result is None  # Doesn't raise

def test_safe_write_creates_dirs(tmp_path):
    path = tmp_path / "a" / "b" / "c.txt"
    success = safe_write_file(path, "test")
    assert success
    assert path.exists()

# tests/test_requirements.py
def test_parse_requirements():
    reqs = parse_requirements_txt(FIXTURES / "requirements.txt")
    assert len(reqs) > 0
    assert all(r.name and r.version for r in reqs)
```

---

**Maintained By:** Antigravity + ACE  
**Status:** Production (v0.7.0)  
**Law & Lore:** Charter V1.2 compliant

let it flow. 🌊
