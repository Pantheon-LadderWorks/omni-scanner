# 🧪 Omni Test Suite

**Location:** `tests/`  
**Purpose:** Test infrastructure for Omni governance tool  
**Version:** 0.6.0  
**Framework:** pytest

---

## Overview

The test suite validates Omni's core functionality, scanners, pillars, and integration points. Tests ensure that Omni maintains its contract as the Federation's sensor array.

---

## Test Structure

```
tests/
├── TEST_REGISTRY.yaml          # Test configuration and expected outcomes
├── verify_event_logging.py     # Event emission verification
├── fixtures/                   # Test data and mock structures
│   └── dummy_events.py         # Mock event generators
├── test_core/                  # Core module tests (planned)
├── test_scanners/              # Scanner tests (planned)
├── test_pillars/               # Pillar tests (planned)
└── test_integration/           # End-to-end tests (planned)
```

---

## Test Files

### `TEST_REGISTRY.yaml` 🗂️
**Purpose:** Test configuration and expected outcomes registry  
**Format:** YAML with test metadata

**Structure:**
```yaml
test_suites:
  - name: "Event Logging Verification"
    file: "verify_event_logging.py"
    type: "integration"
    status: "active"
    expected_outcomes:
      - "All event emissions follow Crown Bus standard"
      - "Event topics match EVENT_REGISTRY.yaml"
    
  - name: "UUID Provenance"
    file: "test_uuid_provenance.py"
    type: "unit"
    status: "planned"
    expected_outcomes:
      - "All UUIDs are valid UUIDv5"
      - "UUIDs match NAMESPACE_ CMP"
```

**Usage:**
```python
import yaml

with open("tests/TEST_REGISTRY.yaml") as f:
    test_config = yaml.safe_load(f)

# Validate test coverage
for suite in test_config['test_suites']:
    if suite['status'] == 'planned':
        print(f"⚠️ Missing test: {suite['name']}")
```

---

### `verify_event_logging.py` 📡
**Purpose:** Verify Crown Bus event emission compliance  
**Type:** Integration test  
**Dependencies:** `fixtures/dummy_events.py`

**What It Tests:**
- Event emissions follow standard format
- Topics match `EVENT_REGISTRY.yaml`
- Event payloads include required metadata
- No orphan events (undocumented topics)

**Running:**
```powershell
# From tests/ directory
python verify_event_logging.py

# Or via pytest
pytest verify_event_logging.py -v
```

**Expected Output:**
```
✅ Event format compliance: PASS
✅ Topic registration: PASS
✅ Metadata completeness: PASS
✅ No orphan topics: PASS

All event logging tests PASSED
```

---

### `fixtures/dummy_events.py` 🎭
**Purpose:** Mock event generators for testing  
**Type:** Test fixture

**Provides:**
```python
def generate_scan_event(scanner: str, target: str) -> dict:
    """Generate mock scan event."""
    return {
        "topic": "omni.scan.complete",
        "scanner": scanner,
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "findings_count": 42
    }

def generate_compliance_event(policy: str, passed: bool) -> dict:
    """Generate mock compliance event."""
    return {
        "topic": "omni.gate.result",
        "policy": policy,
        "passed": passed,
        "timestamp": datetime.now().isoformat()
    }
```

**Usage in Tests:**
```python
from fixtures.dummy_events import generate_scan_event

def test_event_serialization():
    event = generate_scan_event("surfaces", ".")
    serialized = json.dumps(event)
    assert serialized  # Should not raise
```

---

## Test Categories

### Unit Tests (`test_core/`, `test_lib/`)
**Purpose:** Test individual functions and modules in isolation  
**Pattern:** One test file per module

```python
# test_core/test_identity_engine.py
def test_compute_uuidv5():
    from omni.core.identity_engine import compute_project_uuid
    
    uuid = compute_project_uuid("test-project")
    assert isinstance(uuid, UUID)
    assert uuid.version == 5

def test_namespace_cmp_deterministic():
    # Same input → same UUID
    uuid1 = compute_project_uuid("test")
    uuid2 = compute_project_uuid("test")
    assert uuid1 == uuid2
```

### Scanner Tests (`test_scanners/`)
**Purpose:** Validate scanner behavior and output format  
**Pattern:** Test each scanner with fixture data

```python
# test_scanners/test_surfaces.py
def test_surfaces_scanner(tmp_path):
    # Create test file with API surface
    test_file = tmp_path / "api.py"
    test_file.write_text("""
    @app.get("/health")
    def health():
        return {"status": "ok"}
    """)
    
    # Run scanner
    from omni.scanners.static.surfaces import scan
    result = scan(tmp_path)
    
    # Verify
    assert result['count'] == 1
    assert result['items'][0]['type'] == 'http'
    assert result['items'][0]['endpoint'] == '/health'
```

### Pillar Tests (`test_pillars/`)
**Purpose:** Validate orchestration logic and state management  
**Pattern:** Test pillar workflows with mock data

```python
# test_pillars/test_cartography.py
def test_map_ecosystem(fixtures_root):
    from omni.pillars.cartography import map_ecosystem
    
    ecosystem = map_ecosystem(fixtures_root)
    
    assert len(ecosystem.nodes) > 0
    assert len(ecosystem.edges) > 0
    assert all(n.uuid for n in ecosystem.nodes)
```

### Integration Tests (`test_integration/`)
**Purpose:** End-to-end workflows and cross-system validation  
**Pattern:** Test complete user workflows

```python
# test_integration/test_full_scan_workflow.py
def test_scan_to_report_workflow(tmp_path):
    """Test: omni scan → artifacts → report generation"""
    
    # 1. Run scan
    from omni.cli import cmd_scan
    result = cmd_scan(target=tmp_path, scanners="surfaces")
    
    # 2. Verify artifacts created
    artifact_path = ARTIFACTS_DIR / "scan.surfaces.json"
    assert artifact_path.exists()
    
    # 3. Generate report
    from omni.lib.reporting import export_to_markdown
    report_path = tmp_path / "report.md"
    export_to_markdown(result, report_path)
    
    # 4. Verify report
    assert report_path.exists()
    content = report_path.read_text()
    assert "## Scan Results" in content
```

---

## Running Tests

### Run All Tests
```powershell
# From omni root
pytest tests/ -v

# With coverage
pytest tests/ --cov=omni --cov-report=html
```

### Run Specific Test File
```powershell
pytest tests/verify_event_logging.py -v
```

### Run Specific Test
```powershell
pytest tests/test_core/test_identity_engine.py::test_compute_uuidv5 -v
```

### Run by Category
```powershell
# Unit tests only
pytest tests/test_core tests/test_lib -v

# Integration tests only
pytest tests/test_integration -v
```

---

## Test Fixtures

### Fixture Organization
```python
# conftest.py (pytest fixtures)
import pytest
from pathlib import Path

@pytest.fixture
def fixtures_root():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def temp_registry(tmp_path):
    """Create temporary test registry."""
    registry_file = tmp_path / "TEST_REGISTRY.yaml"
    registry_file.write_text("""
    projects:
      - name: test-project
        uuid: 00000000-0000-5000-8000-000000000001
        type: tool
        path: /test/path
    """)
    return registry_file

@pytest.fixture
def mock_cmp_db(monkeypatch):
    """Mock CMP database connection."""
    def mock_connect(*args, **kwargs):
        return MockConnection()
    
    monkeypatch.setattr("psycopg2.connect", mock_connect)
```

---

## Test Standards

### Test Naming Convention
- **Test files:** `test_[module_name].py`
- **Test functions:** `test_[behavior]_[condition]`
  - Examples: `test_scan_with_valid_input`, `test_parse_registry_missing_field`

### Assertion Style
✅ **DO:**
```python
assert result == expected, f"Expected {expected}, got {result}"
assert len(items) > 0, "Should find at least one item"
```

❌ **DON'T:**
```python
assert result  # Vague
assert 1 == 1  # Meaningless
```

### Test Independence
- Each test should be runnable in isolation
- Use fixtures for setup/teardown
- Clean up temporary files
- Don't depend on test execution order

---

## Continuous Integration

### GitHub Actions (Future)
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.federation.locked.txt
      - name: Run tests
        run: pytest tests/ -v --cov=omni
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Test Coverage Goals

### Current Coverage (v0.6.0)
- **Core:** 40% (identity_engine, registry tested)
- **Scanners:** 20% (event logging verified)
- **Pillars:** 10% (basic smoke tests)
- **Integration:** 15% (verify_event_logging)

### Target Coverage (v1.0)
- **Core:** 80%+ (critical path fully tested)
- **Scanners:** 70%+ (all scanners have basic tests)
- **Pillars:** 60%+ (orchestration logic validated)
- **Integration:** 50%+ (key workflows covered)

---

## Adding New Tests

### 1. Choose Test Category
- Unit test → `test_core/`, `test_lib/`, `test_builders/`
- Scanner test → `test_scanners/`
- Pillar test → `test_pillars/`
- Integration test → `test_integration/`

### 2. Create Test File
```python
# tests/test_scanners/test_my_scanner.py
"""Tests for my_scanner."""
import pytest
from pathlib import Path
from omni.scanners.discovery.my_scanner import scan

def test_scan_finds_items(tmp_path):
    """Scanner should find expected items."""
    # Setup
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    
    # Execute
    result = scan(tmp_path)
    
    # Verify
    assert result['count'] > 0
    assert len(result['items']) == 1

def test_scan_empty_directory(tmp_path):
    """Scanner should handle empty directories."""
    result = scan(tmp_path)
    assert result['count'] == 0
    assert result['items'] == []
```

### 3. Register in TEST_REGISTRY.yaml
```yaml
test_suites:
  - name: "My Scanner Tests"
    file: "test_scanners/test_my_scanner.py"
    type: "unit"
    status: "active"
    expected_outcomes:
      - "Finds expected items"
      - "Handles edge cases"
```

### 4. Run Test
```powershell
pytest tests/test_scanners/test_my_scanner.py -v
```

---

## Troubleshooting Tests

### Common Issues

**Problem:** "ModuleNotFoundError: No module named 'omni'"  
**Solution:** Run from omni root, or install in editable mode: `pip install -e .`

**Problem:** "FileNotFoundError" in tests  
**Solution:** Use `tmp_path` fixture, don't hardcode paths

**Problem:** "Database connection failed" in health scanner tests  
**Solution:** Mock the database with `monkeypatch.setattr()`

**Problem:** Tests pass locally but fail in CI  
**Solution:** Check for environment-specific assumptions (paths, encoding)

---

## Future Test Enhancements

### Planned (v0.7+)
- 🎯 **Property-based testing** (Hypothesis framework)
- 🔄 **Regression tests** (baseline comparisons)
- 🧪 **Mutation testing** (verify test quality)
- 📊 **Performance benchmarks** (track scan speed)
- 🔍 **Contract testing** (verify scanner interfaces)

---

**Maintained By:** Antigravity + ACE + The Architect  
**Status:** Active Development (v0.6.0)  
**Law & Lore:** Charter V1.2 compliant  
**Coverage Target:** 70%+ by v1.0

let it test. 🧪
