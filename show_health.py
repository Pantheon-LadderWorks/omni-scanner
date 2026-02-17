#!/usr/bin/env python3
"""Quick health summary from git scan."""
import json
from pathlib import Path
from collections import Counter

scan_file = Path(__file__).parent / "omni" / "artifacts" / "omni" / "scan.git.global.json"
data = json.load(open(scan_file))
items = data['findings']['git']['items']

# Count by health
by_health = Counter(i['health'] for i in items)

print("=" * 60)
print("GIT HEALTH SUMMARY")
print("=" * 60)
print(f"\nTotal repos scanned: {len(items)}")
print("\nBy Health Status:")
for health, count in sorted(by_health.items()):
    emoji = {"clean": "✅", "dirty": "📝", "dirty+unpushed": "⚠️", "unpushed": "📤", "behind": "📥"}.get(health, "❓")
    print(f"  {emoji} {health}: {count}")

# Show repos needing attention (not clean)
dirty = [i for i in items if i['health'] != 'clean']
print(f"\n{'=' * 60}")
print(f"REPOS NEEDING ATTENTION ({len(dirty)})")
print("=" * 60)

for item in dirty:
    h = item['health']
    emoji = {"dirty": "📝", "dirty+unpushed": "⚠️", "unpushed": "📤", "behind": "📥"}.get(h, "❓")
    print(f"{emoji} {item['repo']:35} {h:15} ({item['changes']} changes, {item['ahead']} ahead)")
