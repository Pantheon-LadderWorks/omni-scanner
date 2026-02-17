"""
Test MCP Server Discovery v2.0.0 - AST + Classification Edition
"""
import sys
sys.path.insert(0, r'C:\Users\kryst\Infrastructure\tools\omni')

from omni.scanners.discovery.mcp_server_discovery import scan

results = scan(max_results=50)

print("=" * 80)
print("🌌 MCP SERVER DISCOVERY - LEVEL B: STRUCTURED INVENTORY 🌌")
print("=" * 80)
print()
print(results['summary'])
print()

# Classification breakdown
print("📊 CLASSIFICATION BREAKDOWN:")
for classification, count in sorted(results['results']['classification_breakdown'].items()):
    print(f"   {classification:15} : {count:2} servers")
print()

# Connectivity status
conn = results['results']['connectivity_status']
print(f"🔌 CONNECTIVITY: {conn['connected']} connected, {conn['disconnected']} disconnected")
print()

# Self-discovery
if results['results']['self_discovery']:
    print("🪞 SELF-AWARENESS: Omni found itself!")
    print()

# Show first 25 servers with classification tags
print("📋 DISCOVERED SERVERS (first 25):")
print()
for i, server in enumerate(results['results']['servers'][:25], 1):
    # Classification emoji
    class_emoji = {
        'connected': '🔌',
        'orphaned': '⚰️',
        'experimental': '🧪',
        'external': '🌐',
        'deployable': '🚀',
        'discovered': '🔍',
    }.get(server['classification'], '❓')
    
    # Self tag
    self_tag = ' 🪞' if server['is_self'] else ''
    
    # Location (first 3 path segments)
    rel_path = server['relative_path']
    parts = rel_path.split('/')[:3]
    location = '/'.join(parts) if len(parts) <= 3 else '/'.join(parts) + '/...'
    
    print(f"{i:2}. {class_emoji} {server['name']:30} | {server['tool_count']:2} tools | {server['classification']:12}{self_tag}")
    print(f"    {location}")

print()
print(f"📝 Scanned {results['results']['scanned_files']} Python files")
print(f"🎯 Showing first 25 of {results['results']['total_found']} servers")
print("=" * 80)
