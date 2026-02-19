# 📚 Library Scanners

**Category**: `library`
**Scanners**: 6
**Dependencies**: None (stdlib only)

> *Grand Librarian cognitive scanners — these instruments perform deep analysis and organization of your documentation, measuring cohesion, content quality, knowledge connectivity, and cultural signatures.*

---

## Scanner Inventory

| Scanner           | File               | Description                                                                                  |
| :---------------- | :----------------- | :------------------------------------------------------------------------------------------- |
| **library**       | `library.py`       | Document census — discovers markdown files, measures freshness (< 90 days fresh, ≥ 90 stale) |
| **cohesion**      | `cohesion.py`      | Analyzes folder cohesion — classifies directories as organized modules vs. dump grounds      |
| **content**       | `content.py`       | Deep content analysis — frontmatter extraction, keyword detection, shebang identification    |
| **graph**         | `graph.py`         | Extracts knowledge graph links, imports, and cross-references between documents              |
| **empty_folders** | `empty_folders.py` | Detects empty semantic structures and potential recovery targets                             |
| **rituals**       | `rituals.py`       | Detects CodeCraft rituals, invocations, and school signatures                                |

## Key Concepts

### Freshness Tracking
The `library` scanner walks the filesystem and reports document freshness:
- **Fresh** (< 90 days): Actively maintained
- **Stale** (≥ 90 days): May need attention

### Cohesion Analysis
The `cohesion` scanner evaluates whether a folder is a **well-organized module** or a **dump ground** by analyzing naming patterns, file type consistency, and structural signals.

### Knowledge Graphs
The `graph` scanner builds a web of connections between documents by extracting:
- Markdown links between files
- Import references
- Cross-references and citations

## Usage

```bash
omni scan . --scanner library
omni scan . --scanner cohesion
omni scan . --scanner content
omni scan . --scanner graph
```

## Contract
All scanners follow `C-TOOLS-OMNI-SCANNER-001` — read-only, safe failure, `scan(target: Path) → dict`.

---

*← Back to [Scanner Architecture Guide](../README.md)*
