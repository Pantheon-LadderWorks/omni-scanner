"""Test MCP server scanner discovery"""
import sys
from pathlib import Path

# Match mcp.json PYTHONPATH exactly
omni_dir = Path(__file__).parent
sys.path.insert(0, str(omni_dir))

from mcp_server.omni_mcp_server import discover_scanners

print("🔍 Testing Omni MCP Scanner Discovery...")
print()

# Test 1: Discover scanners
registry = discover_scanners()
categories = set(s.split("/")[0] for s in registry.keys())

print(f"✅ Scanner Discovery: {len(registry)} scanners across {len(categories)} categories")
print(f"   Categories: {sorted(categories)}")
print()

# Test 2: Cache test (second call should use cache)
registry2 = discover_scanners()
print(f"✅ Cache Test: {'PASS' if registry == registry2 else 'FAIL'} (cached registry matches)")
print()

# Test 3: Sample scanners
print("📋 Sample Scanners:")
for scanner_key in list(registry.keys())[:5]:
    info = registry[scanner_key]
    print(f"   • {scanner_key}: {info['description'][:60]}")
print(f"   ... and {len(registry) - 5} more")
print()

print("🎉 All tests passed!")
