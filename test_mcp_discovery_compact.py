import sys
sys.path.insert(0, r'C:\Users\kryst\Infrastructure\tools\omni')

from omni.scanners.discovery.mcp_server_discovery import scan

results = scan(max_results=50)

print(f"🔍 FOUND {results['results']['total_found']} MCP SERVERS:")
print()

for i, server in enumerate(results['results']['servers'][:30], 1):
    loc = server['relative_path'].split('/')[0:3]  # First 3 path segments
    print(f"{i:2}. {server['name']:30} | {server['tool_count']:2} tools | {'/' .join(loc)}")

print()
print(f"📊 Scanned {results['results']['scanned_files']} Python files across 4 workspaces")
print(f"🎯 Full list truncated at 30 (max_results=50)")
