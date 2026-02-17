"""
Census Analyzer - Infrastructure Documentation Intelligence
Analyzes the library census to provide organization insights
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def analyze_census(census_path: str = "infrastructure_docs_census.json"):
    """Analyze census data and generate insights"""
    
    with open(census_path, encoding='utf-8') as f:
        census = json.load(f)
    
    files = census['files']
    summary = census['summary']
    
    print("=" * 80)
    print("📊 INFRASTRUCTURE DOCUMENTATION CENSUS ANALYSIS")
    print("=" * 80)
    print(f"\n🕐 Generated: {census['generated_at']}")
    print(f"📁 Target: {census['target']}")
    print(f"🔍 Pattern: {census['pattern']}")
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total Files: {summary['total_files']:,}")
    print(f"   Fresh (<90 days): {summary['fresh_count']:,} ({summary['fresh_count']/summary['total_files']*100:.1f}%)")
    print(f"   Stale (>=90 days): {summary['stale_count']:,} ({summary['stale_count']/summary['total_files']*100:.1f}%)")
    print(f"   Total Size: {summary['total_bytes']:,} bytes ({summary['total_bytes']/1024/1024:.1f} MB)")
    
    # Directory distribution
    print(f"\n📂 TOP DIRECTORIES BY FILE COUNT:")
    dir_counts = defaultdict(int)
    dir_fresh = defaultdict(int)
    dir_stale = defaultdict(int)
    
    for f in files:
        try:
            relative = f['path'].split('Infrastructure\\')[1]
            top_dir = relative.split('\\')[0]
            dir_counts[top_dir] += 1
            if f['stale']:
                dir_stale[top_dir] += 1
            else:
                dir_fresh[top_dir] += 1
        except:
            pass
    
    sorted_dirs = sorted(dir_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (dir_name, count) in enumerate(sorted_dirs[:15], 1):
        fresh = dir_fresh[dir_name]
        stale = dir_stale[dir_name]
        stale_pct = (stale / count * 100) if count > 0 else 0
        print(f"   {i:2}. {dir_name:30} {count:5,} files ({stale:4,} stale = {stale_pct:5.1f}%)")
    
    # Size analysis
    print(f"\n📏 SIZE DISTRIBUTION:")
    sizes = [f['size'] for f in files]
    avg_size = sum(sizes) // len(sizes)
    print(f"   Average: {avg_size:,} bytes")
    print(f"   Largest: {max(sizes):,} bytes")
    print(f"   Smallest: {min(sizes):,} bytes")
    
    # Large files
    large_files = [f for f in files if f['size'] > 100000]
    print(f"\n📦 LARGE FILES (>100KB): {len(large_files)} files")
    for f in sorted(large_files, key=lambda x: x['size'], reverse=True)[:10]:
        relative = f['path'].split('Infrastructure\\')[1] if 'Infrastructure\\' in f['path'] else f['path']
        print(f"   {f['size']:>10,} bytes - {relative[:70]}")
    
    # Staleness hotspots
    print(f"\n🕰️  STALENESS HOTSPOTS (directories with most stale files):")
    sorted_stale_dirs = sorted(dir_stale.items(), key=lambda x: x[1], reverse=True)
    for i, (dir_name, stale_count) in enumerate(sorted_stale_dirs[:10], 1):
        total = dir_counts[dir_name]
        pct = (stale_count / total * 100) if total > 0 else 0
        print(f"   {i:2}. {dir_name:30} {stale_count:5,} / {total:5,} stale ({pct:5.1f}%)")
    
    # Zero-byte files (potential issues)
    zero_files = [f for f in files if f['size'] == 0]
    if zero_files:
        print(f"\n⚠️  ZERO-BYTE FILES (potential corrupted/placeholder): {len(zero_files)}")
        for f in zero_files[:10]:
            relative = f['path'].split('Infrastructure\\')[1] if 'Infrastructure\\' in f['path'] else f['path']
            print(f"   - {relative}")
    
    # Recent activity
    print(f"\n🔥 RECENT ACTIVITY (last 7 days):")
    recent = [f for f in files if f['age_days'] < 7]
    print(f"   Files modified in last 7 days: {len(recent):,}")
    
    recent_dirs = defaultdict(int)
    for f in recent:
        try:
            relative = f['path'].split('Infrastructure\\')[1]
            top_dir = relative.split('\\')[0]
            recent_dirs[top_dir] += 1
        except:
            pass
    
    sorted_recent = sorted(recent_dirs.items(), key=lambda x: x[1], reverse=True)
    for dir_name, count in sorted_recent[:10]:
        print(f"   - {dir_name}: {count} files")
    
    # Pattern detection
    print(f"\n🔍 PATTERN DETECTION:")
    
    # Duplicates by name
    basenames = defaultdict(list)
    for f in files:
        basename = Path(f['path']).name
        basenames[basename].append(f)
    
    potential_dups = {k: v for k, v in basenames.items() if len(v) > 1}
    print(f"   Files with same name (potential duplicates): {len(potential_dups):,}")
    
    # Top duplicate names
    sorted_dups = sorted(potential_dups.items(), key=lambda x: len(x[1]), reverse=True)
    print(f"\n   Top duplicate filenames:")
    for name, instances in sorted_dups[:10]:
        print(f"   - {name}: {len(instances)} instances")
    
    print("\n" + "=" * 80)
    print("📝 ORGANIZATION RECOMMENDATIONS:")
    print("=" * 80)
    
    print("\n1. 🎯 PRIORITY TARGETS (high stale %, high file count):")
    priority_dirs = [(d, dir_stale[d], dir_counts[d]) for d in dir_counts 
                     if dir_stale[d] > 100 and (dir_stale[d] / dir_counts[d]) > 0.7]
    sorted_priority = sorted(priority_dirs, key=lambda x: x[1], reverse=True)
    for dir_name, stale, total in sorted_priority[:5]:
        pct = (stale / total * 100)
        print(f"   - {dir_name}: {stale:,} stale / {total:,} total ({pct:.1f}% stale)")
    
    print("\n2. 📦 LARGE FILE STRATEGY:")
    print(f"   - {len(large_files)} files >100KB need special handling")
    print(f"   - Consider compression/archival for historical docs")
    
    print("\n3. 🔄 DEDUPLICATION CANDIDATES:")
    high_dup_count = sum(1 for instances in potential_dups.values() if len(instances) > 2)
    print(f"   - {high_dup_count:,} filenames with 3+ instances")
    print(f"   - Run semantic deduplication on these first")
    
    print("\n4. 🧹 CLEANUP CANDIDATES:")
    if zero_files:
        print(f"   - {len(zero_files)} zero-byte files need inspection")
    old_files = [f for f in files if f['age_days'] > 365]
    print(f"   - {len(old_files):,} files >1 year old (consider archival)")
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")
    print("=" * 80)

if __name__ == "__main__":
    analyze_census()
