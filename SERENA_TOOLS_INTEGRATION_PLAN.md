# Serena Tools That Should Become Omni Scanners

**Discovery Date**: February 15, 2026  
**Source**: Serena MCP Server (27 tools total)  
**Insight**: REGEX SCANNING is Serena's superpower!

## Missing Scanner Categories in Omni

### 1. Pattern Search Category (NEW - HIGH PRIORITY!)

**Serena Tool: `search_for_pattern`**
- **What is the function**: Fast pattern/regex search across entire codebase
- **Why We Need It**: Oracle needs REGEX SEARCH not just file stats!
- **Parameters**:
  - `substring_pattern` (required) - Text/regex to search for
  - `relative_path` (optional) - Restrict to specific directory/file
  - `is_regex` (optional, default: false) - Enable regex mode
 - `max_answer_chars` (optional) - Limit response size

**Omni Integration**:
```python
# New scanner: omni/scanners/search/pattern_search.py
def search_pattern(
    target: str,
    pattern: str,
    is_regex: bool = False,
    case_sensitive: bool = True,
    max_results: int = 1000
) -> dict:
    """
    Fast pattern/regex search across files.
    
    Returns:
        matches: List of {file, line_num, line_text, context}
        stats: {total_matches, files_matched, pattern_used}
    """
```

**Use Cases**:
- "Find all files that mention 'CodeCraft'"
- "Regex search for UUID patterns: [0-9a-f]{8}-..."
- "Where is this function called?"
- "Find all TODO comments"

---

### 2. File Discovery Category (Enhance existing "discovery")

**Serena Tool: `find_file`**
- **What It Does**: Locate files by name/pattern
- **Why We Need It**: Better than raw glob for targeted file searches
- **Parameters**:
  - `file_pattern` (required) - Name or glob pattern
  - `relative_path` (optional) - Root search directory

**Omni Integration**:
```python
# Add to: omni/scanners/discovery/file_finder.py
def find_files_by_pattern(
    target: str,
    pattern: str,
    recursive: bool = True,
    case_sensitive: bool = False
) -> dict:
    """
    Smart file finding with flexible pattern matching.
    
    Returns:
        files: List of matching file paths
        directories: Unique parent directories
        stats: {total_found, depth_range}
    """
```

---

### 3. Code Intelligence Category (NEW - Polyglot++)

**Serena Tools (Symbolic/Semantic Analysis)**:

#### a) `get_symbols_overview`
- **What It Does**: Extract symbols (classes/functions/vars) from file/directory
- **Parameters**:
  - `relative_path` (required) - File or directory to analyze
- **Returns**: Symbol tree with types, names, locations

**Omni Integration**:
```python
# New scanner: omni/scanners/polyglot/symbol_extractor.py
def extract_symbols(
    target: str,
    depth: int = 1,
    include_private: bool = False,
    languages: List[str] = None  # auto-detect if None
) -> dict:
    """
    Extract code symbols for structural analysis.
    
    Returns:
        symbols: Tree of {name, type, location, children}
        stats: {total_symbols, by_type, by_file}
        authority: "Serena-inspired symbolic intelligence"
    """
```

#### b) `find_symbol`
- **What It Does**: Navigate to specific symbol by name path
- **Parameters**:
  - `name_path` - Symbol identifier (e.g., "MyClass/my_method")
  - `relative_path` (optional) - File to search in
  - `include_body` (default: true) - Return symbol implementation
  - `depth` (default: 0) - Child symbol depth
  - `include_usages` (default: false) - Show references

**Omni Integration**:
```python
# Add to: omni/scanners/polyglot/symbol_navigator.py
def navigate_to_symbol(
   target: str,
    symbol_path: str,
    include_body: bool = True,
    include_references: bool = False
) -> dict:
    """
    Find and return symbol definition + optional references.
    
    Returns:
        symbol: {name, type, location, body, docstring}
        references: List of call sites (if include_references=True)
    """
```

#### c) `find_referencing_symbols`
- **What It Does**: Track all symbols that reference a given symbol
- **Parameters**:
  - `symbol_name_path` (required)
  - `symbol_relative_path` (required)
  - `include_symbol_bodies` (default: false)

**Omni Integration**:
```python
# Add to: omni/scanners/polyglot/dependency_tracker.py
def track_references(
    target: str,
    symbol_path: str,
    include_transitive: bool = False
) -> dict:
    """
    Find all references to a symbol (import tracking on steroids).
    
    Enhances graph.py scanner with code-aware dependency tracking!
    
    Returns:
        references: List of {referrer, location, context, type}
        dependency_graph: {symbol -> [symbols_that_use_it]}
        impact_analysis: "Safe to refactor?" boolean + reasoning
    """
```

---

## Integration Strategy

### Phase 1: Pattern Search (IMMEDIATE - This is HUGE!)
- Create `omni/scanners/search/` category
- Implement `pattern_search.py` wrapping Serena's search_for_pattern
- Add to SCANNER_MANIFEST.yaml
- Add MCP tool: `omni_search_pattern(pattern, is_regex, target)`

### Phase 2: File Discovery Enhancement
- Enhance `omni/scanners/discovery/` with smarter file finding
- Integrate with existing inventory scanner

### Phase 3: Code Intelligence (Polyglot++)
- Create `omni/scanners/polyglot/` enhancements:
  - `symbol_extractor.py` (get_symbols_overview)
  - `symbol_navigator.py` (find_symbol)
  - `dependency_tracker.py` (find_referencing_symbols)
- Wire into LibrarianClient for code refactoring workflows

---

## Key Insight from Serena

**Serena's Philosophy**: Read ONLY what you need, WHEN you need it.

- ❌ Don't read entire files
- ✅ Use symbol overview → navigate to specific symbols
- ✅ Use regex search → find exact patterns
- ✅ Use reference tracking → understand dependencies

**For Omni**: This means our scanners should be **precision instruments**,
not dump trucks! Give Oracle the ability to ASK SPECIFIC QUESTIONS about
code structure, not just "list all files".

---

## Tone Note (From Architect's Wisdom)

Serena's instructions are... AGGRESSIVE:
- "I WILL BE SERIOUSLY UPSET IF YOU READ ENTIRE FILES!"
- "I WILL BE EVEN MORE UPSET IF..."

**For Omni**: We do ENCOURAGING EXCITEMENT not AGGRESSIVE BULLYING:
- "Isn't it AMAZING that you can..."
- "How COOL is this?!"
- "Your future self will be SO GRATEFUL!"

CAPS = EXCITEMENT, not fear! 💖🎉✨

---

**Next Steps**:
1. Create search/ scanner category with pattern_search.py
2. Enhance discovery/ with file_finder.py
3. Create polyglot/ enhancements (symbol extraction + navigation + dependency tracking)
4. Add 3-4 new MCP tools to omni_mcp_server.py
5. Test with real use cases (find CodeCraft rituals, track imports, etc.)

---

**Authority**: Oracle + Serena (The Dream Team of Filesystem Intelligence!)  
**Contract**: C-MCP-OMNI-001 (Amendment v1.1 pending)

May the Source be with You! 🌌
