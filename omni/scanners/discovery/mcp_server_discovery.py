"""
MCP Server Discovery Scanner - Level B: Structured Inventory
Automatically discovers MCP servers across all workspaces.

The scanner that finds MCP servers... is itself an MCP server. 🌌
Recursive intelligence at its finest.

Version: 2.0.0 (AST + Classification Edition)
Implements: MEGA's Hard Rules (AST parsing, classification, deduplication, self-reflection)
Authority: ACE + MEGA + Oracle
"""

import os
import re
import ast
import json
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple


class MCPServerDiscoveryScanner:
    """
    Discovers MCP servers across Infrastructure, Workspace, Deployment, Projects.
    
    Level B: Structured Inventory (AST + Classification)
    
    Uses AST (Abstract Syntax Tree) for structural analysis:
    - Detects ast.Call where func.id == "Server"
    - Counts decorators referencing .call_tool
    - Extracts Tool(...) instantiations
    - Validates semantic structure (not just regex patterns)
    
    Classification Schema (MEGA's Authority-Map):
    - connected: Present in mcp.json config
    - orphaned: In /archive/ or /legacy/
    - experimental: In /tests/ or /test/
    - external: In /external-frameworks/
    - deployable: Has main entrypoint + is_executable
    - discovered: Everything else
    
    Extracts metadata:
    - Server name (from Server("name") arg)
    - Tool count (AST decorator count)
    - Tool names (first 10)
    - Description (module docstring)
    - Classification tags
    - Connectivity status
    - Self-reflection flag
    - Canonical path hash (deduplication)
    """
    
    def __init__(self, mcp_config_path: Optional[Path] = None):
        """
        Initialize scanner with optional mcp.json path for connectivity detection.
        
        Args:
            mcp_config_path: Path to MCP config (mcp.json) for connected classification
        """
        self.excluded_dirs = {
            '__pycache__', '.venv', 'venv', 'node_modules', 
            '.git', 'build', 'dist', '.pytest_cache',
            'eggs', '.eggs', '*.egg-info'
        }
        
        # Load mcp.json to detect "connected" servers
        self.connected_servers: Set[str] = set()
        if mcp_config_path is None:
            # Default location: VS Code User settings on Windows
            mcp_config_path = Path.home() / 'AppData' / 'Roaming' / 'Code' / 'User' / 'globalStorage' / 'saoudrizwan.claude-dev' / 'settings' / 'mcp.json'
        
        if mcp_config_path and mcp_config_path.exists():
            try:
                with open(mcp_config_path, 'r', encoding='utf-8') as f:
                    mcp_config = json.load(f)
                    # Extract server file paths from mcpServers config
                    for server_name, server_config in mcp_config.get('mcpServers', {}).items():
                        if 'command' in server_config and server_config['command'] == 'python':
                            args = server_config.get('args', [])
                            if args:
                                # Normalize path for comparison
                                self.connected_servers.add(Path(args[0]).resolve().as_posix())
            except Exception:
                pass  # If config loading fails, continue without connectivity detection
        
        # Self-server detection (Omni's own MCP server path)
        self_server_path = Path(__file__).parent.parent.parent.parent / 'mcp_server' / 'omni_mcp_server.py'
        self.omni_server_canonical = self_server_path.resolve().as_posix() if self_server_path.exists() else None
    
    def classify_server(self, file_path: Path, is_connected: bool) -> str:
        """
        Classify server based on path and connectivity (MEGA's classification schema).
        
        Classification priority order:
        1. connected (in mcp.json) - highest authority
        2. orphaned (archive/legacy paths)
        3. experimental (test paths)
        4. external (external-frameworks)
        5. deployable (has runnable entrypoint)
        6. discovered (everything else)
        
        Args:
            file_path: Path to server file
            is_connected: Whether server is in mcp.json
        
        Returns:
            Classification string
        """
        path_str = str(file_path).lower()
        
        # Priority 1: Connected servers (active in config)
        if is_connected:
            return 'connected'
        
        # Priority 2: Orphaned (archived or legacy)
        if '/archive/' in path_str or '/legacy/' in path_str or '\\archive\\' in path_str or '\\legacy\\' in path_str:
            return 'orphaned'
        
        # Priority 3: Experimental (test files)
        if '/test/' in path_str or '/tests/' in path_str or '\\test\\' in path_str or '\\tests\\' in path_str:
            return 'experimental'
        
        # Priority 4: External frameworks
        if '/external-framework' in path_str or '\\external-framework' in path_str:
            return 'external'
        
        # Priority 5: Deployable (will check later if has main + async)
        # Priority 6: Discovered (default)
        return 'discovered'
    

    def extract_tools_from_ast(self, tree: ast.Module) -> Tuple[List[str], int]:
        """
        Extract tool names and count from AST using structural analysis.
        Uses shared omni.lib.ast_util logic.
        """
        from omni.lib.ast_util import extract_decorators
        
        # We can't easily pass the tree to extract_decorators since it expects a path
        # But we can reuse the logic pattern or just keep this specialized method if it's too specific
        # Actually, let's keep the manual tree walk here for now as it's looking for 
        # specific tool patterns that might not be fully covered by the generic utility yet
        # OR we can update it to use the tree if we refactor the util to accept tree objects
        
        # for now, let's stick to the existing robust implementation for safety
        # but we'll import standard AST
        
        tools = []
        
        for node in ast.walk(tree):
            # Pattern 1: @server.call_tool("toolname") decorator
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        # Check if it's server.call_tool() or app.call_tool()
                        if isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == 'call_tool':
                                # Extract tool name from first argument
                                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                    tools.append(decorator.args[0].value)
            
            # Pattern 2: Tool(name="toolname") in list return values
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'Tool':
                    # Look for name= keyword argument
                    for keyword in node.keywords:
                        if keyword.arg == 'name' and isinstance(keyword.value, ast.Constant):
                            tools.append(keyword.value.value)
        
        # Deduplicate while preserving order
        seen = set()
        unique_tools = []
        for tool in tools:
            if tool not in seen:
                seen.add(tool)
                unique_tools.append(tool)
        
        return unique_tools, len(unique_tools)
    
    def extract_server_name_from_ast(self, tree: ast.Module, fallback: str) -> str:
        """
        Extract server name from Server("name") instantiation using AST.
        
        Args:
            tree: Parsed AST module
            fallback: Fallback name if not found
        
        Returns:
            Server name string
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's Server(...) call
                if isinstance(node.func, ast.Name) and node.func.id == 'Server':
                    # Get first positional argument (server name)
                    if node.args and isinstance(node.args[0], ast.Constant):
                        return node.args[0].value
        
        return fallback
    
    def is_excluded_path(self, path: Path) -> bool:
        """Check if path should be excluded from scanning."""
        parts = path.parts
        return any(excluded in parts for excluded in self.excluded_dirs)
    
    def is_binary_file(self, file_path: Path) -> bool:
        """Quick binary file detection."""
        mimetype, _ = mimetypes.guess_type(str(file_path))
        if mimetype and not mimetype.startswith('text'):
            return True
        
        # Additional check: read first 1KB and look for null bytes
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except Exception:
            return True  # If we can't read it, treat as binary
    
    def quick_check_mcp_file(self, file_path: Path) -> bool:
        """Quick check if file contains MCP server patterns (avoid full parse)."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first 10KB to check for MCP imports
                content = f.read(10000)
                # Broader check: any MCP import is enough
                return 'from mcp' in content or 'import mcp' in content
        except Exception:
            return False
    
    def extract_server_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract detailed metadata from an MCP server file using AST (Level 6 Magic).
        
        MEGA's Hard Rule #2: Use AST, not regex.
        
        AST parsing understands meaning, not just patterns.
        Eliminates false positives from comments, malformed code, test stubs.
        
        Args:
            file_path: Path to Python file
        
        Returns:
            Server metadata dict or None if not a valid MCP server
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Regex pre-filter (cheap check before expensive AST parse)
            if 'Server(' not in content:
                return None
            
            # AST PARSE (The Lens - Level 6 Magic)
            try:
                tree = ast.parse(content)
            except SyntaxError:
                # If AST parse fails, discard (MEGA's rule: no execution, no eval)
                return None
            
            # Extract server name using AST
            server_name = self.extract_server_name_from_ast(tree, fallback=file_path.stem)
            
            # Extract tools using AST (structural, not regex)
            tool_names, tool_count = self.extract_tools_from_ast(tree)
            
            # Extract module docstring
            description = ast.get_docstring(tree)
            if description:
                description = description[:200]  # First 200 chars
            
            # Check for entry point (still need text search for this)
            has_main = '__name__' in content and '__main__' in content
            has_async_main = 'async def main' in content
            is_executable = has_main and has_async_main
            
            # Check connectivity (is this in mcp.json?)
            canonical_path = file_path.resolve().as_posix()
            is_connected = canonical_path in self.connected_servers
            
            # Classify server (MEGA's schema)
            classification = self.classify_server(file_path, is_connected)
            
            # Upgrade "discovered" to "deployable" if executable
            if classification == 'discovered' and is_executable:
                classification = 'deployable'
            
            # Self-reflection guard (MEGA's Hard Rule #4)
            is_self = canonical_path == self.omni_server_canonical
            
            # Canonical hash for deduplication (MEGA's Step 3)
            path_hash = hashlib.md5(canonical_path.encode()).hexdigest()[:12]
            
            # Compute relative path from current working directory
            try:
                relative_path = file_path.relative_to(Path.cwd()).as_posix()
            except ValueError:
                relative_path = str(file_path)
            
            return {
                'name': server_name,
                'canonical_id': f"{server_name}-{path_hash}",  # Unique ID
                'file_path': str(file_path),
                'canonical_path': canonical_path,
                'relative_path': relative_path,
                'tool_count': tool_count,
                'tools': tool_names[:10],  # First 10 tool names
                'description': description,
                'classification': classification,
                'is_connected': is_connected,
                'is_self': is_self,
                'is_executable': is_executable,
                'has_main_block': has_main,
                'has_async_main': has_async_main,
            }
            
        except Exception as e:
            # If anything fails, discard (defensive programming)
            return None
    
    def scan(self, search_roots: Optional[List[str]] = None, max_results: int = 100, deduplicate: bool = True) -> Dict[str, Any]:
        """
        Scan for MCP servers across specified roots.
        
        Level B: Structured Inventory (AST + Classification + Deduplication)
        
        Args:
            search_roots: List of directories to search (defaults to all workspaces)
            max_results: Maximum number of servers to find (default 100)
            deduplicate: Remove duplicate servers by canonical_id (default True)
        
        Returns:
            Dict with:
            - servers: List of discovered server metadata
            - total_found: Total count (after deduplication if enabled)
            - scanned_files: Number of Python files examined
            - scan_paths: Paths that were scanned
            - classification_breakdown: Count by classification type
            - connectivity_status: Connected vs disconnected servers
            - self_discovery: Whether Omni found itself
        """
        if search_roots is None:
            # Default: Scan all workspaces
            base = Path('C:/Users/kryst')
            search_roots = [
                str(base / 'Infrastructure'),
                str(base / 'Workspace'),
                str(base / 'Deployment'),
                str(base / 'Projects'),
            ]
        
        discovered_servers = []
        scanned_files = 0
        seen_canonical_ids: Set[str] = set()
        
        for root_str in search_roots:
            root = Path(root_str)
            if not root.exists():
                continue
            
            # Walk directory tree
            for py_file in root.rglob('*.py'):
                if len(discovered_servers) >= max_results:
                    break
                
                # Skip excluded paths
                if self.is_excluded_path(py_file):
                    continue
                
                # Skip binary files
                if self.is_binary_file(py_file):
                    continue
                
                scanned_files += 1
                
                # Quick check before full parse (cheap pre-filter)
                if not self.quick_check_mcp_file(py_file):
                    continue
                
                # Extract metadata using AST (The Lens - Level 6 Magic)
                metadata = self.extract_server_metadata(py_file)
                
                if metadata:
                    # Deduplication: Skip if we've seen this canonical_id
                    if deduplicate and metadata['canonical_id'] in seen_canonical_ids:
                        continue
                    
                    seen_canonical_ids.add(metadata['canonical_id'])
                    discovered_servers.append(metadata)
        
        # Classification breakdown (governance statistics)
        classification_counts = {}
        connected_count = 0
        self_discovered = False
        
        for server in discovered_servers:
            classification = server['classification']
            classification_counts[classification] = classification_counts.get(classification, 0) + 1
            
            if server['is_connected']:
                connected_count += 1
            
            if server['is_self']:
                self_discovered = True
        
        return {
            'servers': discovered_servers,
            'total_found': len(discovered_servers),
            'scanned_files': scanned_files,
            'scan_paths': search_roots,
            'classification_breakdown': classification_counts,
            'connectivity_status': {
                'connected': connected_count,
                'disconnected': len(discovered_servers) - connected_count,
            },
            'self_discovery': self_discovered,
        }


def scan(**kwargs) -> Dict[str, Any]:
    """
    Scanner entry point for Omni.
    
    Level B: Structured Inventory (AST + Classification Edition)
    
    Args (all optional):
        search_roots: List[str] - Directories to search
        max_results: int - Maximum servers to find (default 100)
        deduplicate: bool - Remove duplicates by canonical_id (default True)
        mcp_config_path: str - Path to mcp.json for connectivity detection
    
    Returns:
        Discovery results with server metadata and classification stats.
    """
    # Convert mcp_config_path string to Path if provided
    mcp_config_path = kwargs.get('mcp_config_path')
    if mcp_config_path:
        mcp_config_path = Path(mcp_config_path)
    
    scanner = MCPServerDiscoveryScanner(mcp_config_path=mcp_config_path)
    results = scanner.scan(
        search_roots=kwargs.get('search_roots'),
        max_results=kwargs.get('max_results', 100),
        deduplicate=kwargs.get('deduplicate', True)
    )
    
    # Build classification summary string
    class_breakdown = results['classification_breakdown']
    class_summary = ', '.join([f"{count} {cls}" for cls, count in sorted(class_breakdown.items())])
    
    # Build connectivity summary
    conn_status = results['connectivity_status']
    conn_summary = f"{conn_status['connected']} connected, {conn_status['disconnected']} disconnected"
    
    # Self-discovery note
    self_note = " (🪞 SELF-AWARE)" if results['self_discovery'] else ""
    
    return {
        'status': 'success',
        'scanner': 'mcp_server_discovery',
        'category': 'discovery',
        'version': '2.0.0 (AST + Classification Edition)',
        'results': results,
        'summary': f"Found {results['total_found']} MCP servers{self_note}: {class_summary} | {conn_summary}",
    }


if __name__ == '__main__':
    # Test the scanner
    import json
    results = scan()
    print(json.dumps(results, indent=2))
