# 🔍 Search Scanners

**Category**: `search`
**Scanners**: 3
**Dependencies**: None (stdlib only)

> *Pattern matching scanners — fast, targeted search instruments for finding files, text, and regex patterns across your codebase with contextual results.*

---

## Scanner Inventory

| Scanner            | File                | Description                                                            |
| :----------------- | :------------------ | :--------------------------------------------------------------------- |
| **pattern_search** | `pattern_search.py` | Fast pattern/regex search with context lines — the primary search tool |
| **file_search**    | `file_search.py`    | File search by name or glob pattern                                    |
| **text_search**    | `text_search.py`    | Text search across codebase files                                      |

## Key Features

### Pattern Search (The Primary Tool)
The `pattern_search` scanner is the powerhouse:
- Regex and literal pattern matching
- Configurable context lines (before/after matches)
- File type filtering
- Exclusion patterns for node_modules, .git, etc.

### File Search
Quick file discovery by name, extension, or glob pattern.

### Text Search
Full-text search across all files in a target directory.

## Usage

```bash
omni scan . --scanner pattern_search
omni scan . --scanner file_search
omni scan . --scanner text_search
```

## Contract
All scanners follow `C-TOOLS-OMNI-SCANNER-001` — read-only, safe failure, `scan(target: Path) → dict`.

---

*← Back to [Scanner Architecture Guide](../README.md)*
