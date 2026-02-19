"""
🔍 Omni Introspection Command
=============================
Self-scan capability - Omni examines its own scanners and commands.

Pattern stolen from: federation_heart/cli/commands/utility/tools.py
Authority: "Never trust documentation, trust reality" - ACE

Contract: C-CLI-OMNI-INTROSPECT-001
"""
from pathlib import Path
from typing import Dict, List
import yaml


class OmniIntrospector:
    """
    Omni's self-awareness engine.
    Scans its own scanners/ directory and manifests.
    """
    
    def __init__(self):
        self.omni_root = Path(__file__).parent.parent.resolve()
        self.scanners_root = self.omni_root / "scanners"
        
    def scan_filesystem(self) -> Dict[str, List[str]]:
        """Walk scanners/ and count actual .py files by category."""
        categories = {}
        
        for category_dir in self.scanners_root.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith(('_', '.')):
                continue
                
            scanners = []
            for file in category_dir.glob("*.py"):
                if file.name.startswith('__') or file.name in ['README.md', 'base_db_scanner.py']:
                    continue
                scanners.append(file.stem)
            
            if scanners:
                categories[category_dir.name] = sorted(scanners)
        
        return categories
    
    def load_manifests(self) -> Dict[str, dict]:
        """Load SCANNER_MANIFEST.yaml from each category."""
        manifests = {}
        
        for category_dir in self.scanners_root.iterdir():
            if not category_dir.is_dir():
                continue
                
            manifest_path = category_dir / "SCANNER_MANIFEST.yaml"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifests[category_dir.name] = yaml.safe_load(f)
                except Exception as e:
                    manifests[category_dir.name] = {"error": str(e)}
        
        return manifests
    
    def detect_drift(self, filesystem: dict, manifests: dict) -> Dict[str, dict]:
        """Compare filesystem reality vs manifest claims."""
        drift = {}
        
        for category, fs_scanners in filesystem.items():
            manifest = manifests.get(category, {})
            manifest_scanners = [s['name'] for s in manifest.get('scanners', [])]
            
            in_fs_not_manifest = set(fs_scanners) - set(manifest_scanners)
            in_manifest_not_fs = set(manifest_scanners) - set(fs_scanners)
            
            if in_fs_not_manifest or in_manifest_not_fs:
                drift[category] = {
                    "undocumented": sorted(in_fs_not_manifest),
                    "missing_files": sorted(in_manifest_not_fs)
                }
        
        return drift
    
    def count_commands(self) -> int:
        """Count available CLI commands."""
        # Check cli.py for command definitions
        cli_path = self.omni_root / "cli.py"
        if cli_path.exists():
            # Count subparsers.add_parser calls (rough estimate)
            content = cli_path.read_text(encoding='utf-8')
            return content.count('subparsers.add_parser(')
        return 0
    
    def introspect(self, show_drift: bool = True, show_scanners: bool = True) -> bool:
        """Execute full introspection."""
        print("\n🔍 OMNI SELF-INTROSPECTION")
        print("=" * 70)
        print("\"Never trust documentation, trust reality\" - ACE")
        print("=" * 70)
        
        # 1. Filesystem scan
        filesystem = self.scan_filesystem()
        total_scanners = sum(len(scanners) for scanners in filesystem.values())
        
        # 2. Manifest scan
        manifests = self.load_manifests()
        
        # 3. Command count
        command_count = self.count_commands()
        
        # 4. Summary
        print(f"\n📊 OMNI CAPABILITIES")
        print("-" * 70)
        print(f"   📋 CLI Commands:       {command_count}")
        print(f"   🔍 Scanner Categories: {len(filesystem)}")
        print(f"   📦 Total Scanners:     {total_scanners}")
        print(f"   📜 Manifest Files:     {len(manifests)}")
        
        # 5. Scanner breakdown by category
        if show_scanners:
            print(f"\n🗂️  SCANNER INVENTORY")
            print("-" * 70)
            
            category_emojis = {
                "static": "📄",
                "discovery": "🔎",
                "database": "💾",
                "runtime": "⚡",
                "health": "💊",
                "phoenix": "🔥",
                "polyglot": "🌐",
                "git": "🔀",
                "fleet": "🛰️",
            }
            
            for category in sorted(filesystem.keys()):
                scanners = filesystem[category]
                emoji = category_emojis.get(category, "📦")
                manifest = manifests.get(category, {})
                desc = manifest.get('description', 'No description')
                
                print(f"\n{emoji} {category}/ ({len(scanners)} scanners)")
                print(f"   {desc}")
                for scanner in scanners:
                    print(f"      • {scanner}.py")
        
        # 6. Drift detection
        if show_drift:
            drift = self.detect_drift(filesystem, manifests)
            
            if drift:
                print(f"\n⚠️  DRIFT DETECTED (Manifest vs Reality)")
                print("-" * 70)
                
                for category, issues in drift.items():
                    if issues["undocumented"]:
                        print(f"\n❌ {category}/ - UNDOCUMENTED SCANNERS:")
                        for scanner in issues["undocumented"]:
                            print(f"      • {scanner}.py (exists but not in manifest)")
                    
                    if issues["missing_files"]:
                        print(f"\n❌ {category}/ - MANIFEST PHANTOMS:")
                        for scanner in issues["missing_files"]:
                            print(f"      • {scanner}.py (in manifest but file missing)")
            else:
                print(f"\n✅ NO DRIFT DETECTED")
                print("   All scanner manifests match filesystem reality!")
        
        # 7. Documentation drift check (scans per-category READMEs)
        documented_scanners = set()
        undocumented_scanners = []
        
        for category, scanners in filesystem.items():
            category_readme = self.scanners_root / category / "README.md"
            if category_readme.exists():
                try:
                    readme_text = category_readme.read_text(encoding='utf-8')
                    for scanner_name in scanners:
                        # Check if scanner name appears in the category README
                        if scanner_name in readme_text:
                            documented_scanners.add(f"{category}/{scanner_name}")
                        else:
                            undocumented_scanners.append(f"{category}/{scanner_name}")
                except Exception:
                    # If we can't read the README, all scanners in this category are undocumented
                    for scanner_name in scanners:
                        undocumented_scanners.append(f"{category}/{scanner_name}")
            else:
                # No README at all for this category
                for scanner_name in scanners:
                    undocumented_scanners.append(f"{category}/{scanner_name}")
        
        documented_count = len(documented_scanners)
        if undocumented_scanners:
            print(f"\n📚 DOCUMENTATION DRIFT")
            print("-" * 70)
            print(f"   Documented scanners:   {documented_count}")
            print(f"   Actual scanners:       {total_scanners}")
            print(f"   Undocumented:          {len(undocumented_scanners)} 🚨")
            for scanner in sorted(undocumented_scanners):
                print(f"      • {scanner}")
        else:
            print(f"\n📚 DOCUMENTATION: {documented_count}/{total_scanners} SCANNERS COVERED ✅")
        
        print(f"\n{'=' * 70}")
        print(f"✨ Introspection complete")
        print(f"   Omni knows itself.")
        
        return True


def cmd_introspect(args):
    """
    Execute Omni introspection.
    
    Usage:
        omni introspect                # Full report
        omni introspect --scanners     # Scanner inventory only
        omni introspect --drift        # Drift detection only
    """
    show_drift = getattr(args, 'drift', False) or not (hasattr(args, 'scanners_only'))
    show_scanners = getattr(args, 'scanners_only', False) or show_drift
    
    inspector = OmniIntrospector()
    return inspector.introspect(show_drift=show_drift, show_scanners=show_scanners)
