"""
Omni CLI - Federation Governance & Introspection Tool
v0.1 - The Tricorder
"""
import argparse
import sys
import os
import json
import yaml # Added for report dumping
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# NO .env loading at CLI startup!
# Env is loaded by:
# 1. federation_heart/constitution/env_client.py (for federation env)
# 2. fetcher.py (ONLY when actually scanning CMP database)

from omni.lib import io
from omni.core import gate
from omni.scanners import SCANNERS
from omni.core.model import ScanResult

__version__ = "0.5.0"
__author__ = "Kode_Animator"

# Resolve Artifacts Root relative to this script
OMNI_ROOT = Path(__file__).parent.resolve()
ARTIFACTS_DIR = OMNI_ROOT.parent / "artifacts" / "omni"

# Governance Registry paths (where registries should be output)
INFRA_ROOT = OMNI_ROOT.parent.parent  # Infrastructure root
REGISTRY_ROOT = INFRA_ROOT / "governance" / "registry"

def cmd_scan(args):
    """Run scanners on a target."""
    results = {}
    targets = []
    
    # SMART DETECTION: If target looks like a scanner name, treat it as --scanners
    if args.target and args.target in SCANNERS and not Path(args.target).exists():
        # User ran: omni scan federation_health
        # Treat as: omni scan --scanners=federation_health .
        if not args.scanners:
            args.scanners = args.target
            args.target = "."

    if args.all:
        print("[INFO] Loading Registry for Global Scan...")
        from omni.core import registry
        projects = registry.parse_registry()
        targets = [Path(p['path']) for p in projects]
        target_label = "REGISTRY (Global)"
    else:
        targets = [Path(args.target).resolve()]
        target_label = str(targets[0])

    # Initialize aggregators
    # For v0.1, we only aggregate surfaces for global scan to match V8 Atlas
    # For single target, we run all active scanners
    
    # Combined Execution Logic
    
    # Safety Check: Do not allow running ALL scanners on ALL targets
    if len(targets) > 1 and not args.scanners:
        print("⚠️  SAFETY INTERLOCK: Scanning multiple targets requires explicit --scanners")
        print("   Usage: omni scan --all --scanners=surfaces")
        return

    # Determine Active Scanners
    if args.scanners:
        wanted = args.scanners.split(',')
        active_scanners = []
        for k, v in SCANNERS.items():
            if k in wanted:
                active_scanners.append((k, v))
    else:
        active_scanners = list(SCANNERS.items())

    print(f"[SCAN] Targeting: {target_label}")
    print(f"[CTRL] Active Scanners: {', '.join([k for k,v in active_scanners])}")
    
    # Run Scanners
    for name, scanner_func in active_scanners:
        print(f"  > Running {name}...", end="\n") # Newline for progress
        
        aggregated_items = []
        aggregated_metrics = {}
        failed_targets = 0
        
        # Build kwargs once
        scanner_kwargs = {}
        if name == "canon":
            if hasattr(args, 'canon_source') and args.canon_source: scanner_kwargs['source'] = True
            if hasattr(args, 'canon_verify') and args.canon_verify: scanner_kwargs['verify'] = True
            if hasattr(args, 'canon_school') and args.canon_school: scanner_kwargs['school'] = args.canon_school
        if name == "git":
            if hasattr(args, 'github') and args.github: scanner_kwargs['github'] = True
            if hasattr(args, 'no_update_registry') and args.no_update_registry: scanner_kwargs['update_registry'] = False
        if name == "velocity":
            if hasattr(args, 'since') and args.since: scanner_kwargs['since'] = args.since

        # Loop Targets
        count = 0
        for t in targets:
            if not t.exists(): continue
            try:
                # Simple progress for multi-target
                if len(targets) > 1 and count % 5 == 0:
                    print(f"    Scanning [{count}/{len(targets)}]: {t.name}", end="\r")
                
                res = scanner_func(t, **scanner_kwargs)
                
                # Aggregation Logic
                if isinstance(res, dict):
                    if 'items' in res:
                        # Append source metadata to items if not present?
                        # Surfaces scanner likely handles its own context, but for global aggregation it helps.
                        # For now, just extend.
                        aggregated_items.extend(res['items'])
                    if 'metrics' in res:
                        # naive merge for now - last one wins or we implement bespoke aggregation later
                        aggregated_metrics.update(res['metrics'])
                    else:
                        # Treat the dict as a single finding/report? 
                        # Or maybe it has other keys. 
                        # Fallback: wrap in item
                        aggregated_items.append(res)
                elif isinstance(res, list):
                    aggregated_items.extend(res)
                    
            except Exception as e:
                failed_targets += 1
                # print(f"    [ERR] {t.name}: {e}") # Too noisy for global?
            
            count += 1
            
        print(f"  [OK] {name} complete. Found {len(aggregated_items)} items.        ")
        
        results[name] = {
            "count": len(aggregated_items),
            "items": aggregated_items,
            "metrics": aggregated_metrics
        }

    # Aggregation & Summary logic
    summary = {}
    if 'surfaces' in results:
        items = results['surfaces'].get('items', [])
        missing = sum(1 for s in items if s.get('status') == 'missing' and s.get('scope') != 'external_reference')
        partial = sum(1 for s in items if s.get('status') == 'partial')
        exists = sum(1 for s in items if s.get('status') == 'exists')
        
        summary['surfaces'] = {
            "total": len(items),
            "missing": missing,
            "partial": partial,
            "exists": exists
        }
        
        # Aggregated risk score (simplified)
        risk = "low"
        if missing > 0: risk = "high"
        elif partial > len(items) * 0.9: risk = "medium" # If almost everything is partial
        summary['risk'] = risk

    scan_data = ScanResult(
        target=target_label,
        findings=results,
        summary=summary
    )

    # Output filename logic
    scanner_name = "global"
    scope = "default"

    # Special handling for canon scanner
    if args.scanners == "canon":
        scanner_name = "canon"
        canon_result = results.get("canon", {})
        
        # Check mode
        if hasattr(args, 'canon_source') and args.canon_source:
            # Scanning source YAML front matter
            if hasattr(args, 'canon_school') and args.canon_school:
                # Single school from source
                school_name = None
                for school in canon_result.get('schools', []):
                    school_name = school.get('name', '').lower().replace(' ', '_').replace('&', 'and')
                    break
                
                # Fallback: try to map filter value to school name
                if not school_name:
                    school_map = {
                        "1": "cantrips", "2": "invocations", "3": "bindings", "4": "conjurations",
                        "5": "abjurations", "6": "divinations", "7": "enchantments", "8": "transmutations",
                        "9": "illusioncraft", "10": "necromancy", "11": "chronomancy", "12": "summoning",
                        "13": "runeweaving", "14": "wardcrafting", "15": "soulshaping", "16": "apotheosis",
                        "17": "dreamweaving", "18": "voidcalling", "19": "cosmic_harmonics", "20": "reality_weaving"
                    }
                    filter_val = str(args.canon_school)
                    school_name = school_map.get(filter_val) or filter_val.lower()
                
                scope = school_name
            else:
                # All schools from source
                scope = "arcaneschools"
        elif hasattr(args, 'canon_verify') and args.canon_verify:
            # Verification mode
            scope = "verification"
        else:
            # Scanning built canon.lock.yaml
            if hasattr(args, 'canon_school') and args.canon_school:
                # Single school from canon
                school_name = None
                for school in canon_result.get('schools', []):
                    school_name = school.get('name', '').lower().replace(' ', '_').replace('&', 'and')
                    break
                scope = f"{school_name or 'school'}" if school_name else "school"
            else:
                # Full canon scan
                scope = "lock" # specific usage for lock file scan
    elif args.scanners:
        scanner_name = "_".join(sorted(wanted))
        if args.all:
            scope = "global"
        else:
            scope = "default" # Was "infrastructure", changed to allow target inference
    elif args.all:
        scanner_name = "global"
        scope = "snapshot"
    elif args.target != ".":
         active_keys = sorted([k for k,v in active_scanners])
         scanner_name = "_".join(active_keys)
         scope = target_label.replace("\\", "_").replace("/", "_").replace(":", "")

    # Clean scope
    if scope == "default" and args.target == ".":
        # Resolve "." to folder name (e.g. "omni")
        scope = Path.cwd().name.lower()

    from omni.lib import artifacts
    output_path = artifacts.get_scan_path(scanner=scanner_name, scope=scope)
    
    io.save_scan(scan_data, output_path)
    print(f"\n[REPORT] Saved to: {output_path}")
    
    save_log(scan_data, output_path.with_name("scan_debug.log"))
    
    # 4. Final Summary
    _print_summary(scan_data, args.top, verbosity=args.verbosity)

def save_log(scan_data: ScanResult, path: Path):
    """Save full debug log."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(scan_data.to_dict(), indent=2))

def _print_summary(scan_data: ScanResult, top: int = None, verbosity: str = "default"):
    """Print a human-readable summary to stdout."""
    data = scan_data.to_dict()
    findings = data.get("findings", {})
    
    print("\n" + "="*40)
    print("  OMNI SCAN REPORT")
    print("="*40)

    # Surfaces
    surfaces = findings.get("surfaces", {})
    if surfaces.get('count', 0) > 0:
        print(f"⚡ SURFACES: {surfaces.get('count', 0)} found")
        
        # Semantic Organization (if available)
        organized = surfaces.get('organized', {})
        if organized:
            insights = organized.get('insights', {})
            by_kind = organized.get('by_kind', {}).get('summary', {})
            by_status = organized.get('by_status', {}).get('summary', {})
            
            # Kind breakdown
            if by_kind:
                print(f"\n   📊 By Kind:")
                kind_order = ['mcp', 'http', 'cli', 'db', 'bus_topic', 'ui_integration', 'doc']
                for kind in kind_order:
                    if kind in by_kind:
                        print(f"      • {kind.upper()}: {by_kind[kind]}")
            
            # Status breakdown
            if by_status:
                total = sum(by_status.values())
                exists = by_status.get('exists', 0)
                partial = by_status.get('partial', 0)
                missing = by_status.get('missing', 0)
                coverage = round((exists / total * 100), 1) if total > 0 else 0
                
                print(f"\n   🎯 Coverage:")
                print(f"      ✅ Exists: {exists} ({round(exists/total*100, 1)}%)")
                print(f"      🟡 Partial: {partial} ({round(partial/total*100, 1)}%)")
                print(f"      ❌ Missing: {missing} ({round(missing/total*100, 1)}%)")
            
            # Top components
            if insights.get('top_5_components'):
                print(f"\n   🔥 Top 5 Components:")
                component_details = organized.get('by_component', {}).get('summary', {})
                for comp in insights['top_5_components']:
                    count = component_details.get(comp, 0)
                    print(f"      • {comp}: {count} surfaces")
    
    # Events
    events = findings.get("events", {})
    if events.get('count', 0) > 0:
        print(f"📡 EVENTS:   {events.get('count', 0)} found")
        if verbosity in ["verbose", "debug"] or top:
             count = 0
             for item in events.get('items', []):
                if top and count >= top: break
                print(f"   - {item.get('event_guess')} ({item.get('lane')})")
                count += 1
    
    # Packages
    packages = findings.get("packages", {})
    if packages.get('count', 0) > 0:
        summary = packages.get('summary', {})
        print(f"📦 PACKAGES: {packages.get('count', 0)} found")
        if summary:
            print(f"   • CLI: {summary.get('with_cli', 0)}")
            print(f"   • MCP: {summary.get('with_mcp', 0)}")
            print(f"   • HTTP: {summary.get('with_http', 0)}")
            print(f"   • Triple Interface: {summary.get('triple_interface', 0)} ⭐")

    
    # UUIDs
    uuids = findings.get("uuids", {})
    if uuids.get('count', 0) > 0:
        print(f"🔗 UUIDS:    {uuids.get('count', 0)} unique IDs found")
        items = uuids.get("items", [])
        if items:
            limit = top if top else (10 if verbosity == "default" else 50)
            print(f"   (Top {limit} by frequency)")
            
            for item in items[:limit]:
                # Canonical shape: uuid, count, locations (list), counts_by_location (dict)
                u = item.get("uuid")
                c = item.get("count")
                locs = item.get("locations", [])
                primary_loc = Path(locs[0]).name if locs else "??"
                
                # If multiple locations, show how many files
                suffix = ""
                if len(locs) > 1:
                    suffix = f" in {len(locs)} files (e.g. {primary_loc})"
                else:
                    suffix = f" in {primary_loc}"
                    
                print(f"   {u} : {c:<3} refs {suffix}")
    
    # Canon (CodeCraft Schools)
    canon_data = findings.get("canon", {})
    if canon_data.get('count', 0) > 0:
        print(f"📜 CANON:    {canon_data.get('count', 0)} schools found")
        print(f"   📍 Source: {Path(canon_data.get('canon_path', '')).name}")
        
        # Count enhanced vs legacy operations
        total_ops = 0
        enhanced_ops = 0
        schools_with_enums = 0
        schools_with_relationships = 0
        
        for school in canon_data.get('schools', []):
            ops = school.get('operations', [])
            total_ops += len(ops)
            
            # Count enhanced ops (those with enum semantics OR relationships)
            for op in ops:
                if op.get('has_enum_semantics') or op.get('has_relationships'):
                    enhanced_ops += 1
            
            # Count schools with enums (once per school)
            if any(op.get('has_enum_semantics') for op in ops):
                schools_with_enums += 1
            
            # Count schools with relationships (once per school)
            if any(op.get('has_relationships') for op in ops):
                schools_with_relationships += 1
        
        print(f"   ⚙️  Operations: {total_ops} total")
        print(f"   ✨ Enhanced (v2.3): {enhanced_ops} operations")
        print(f"   🎯 Enum Semantics: {schools_with_enums} schools")
        print(f"   🔗 Relationships: {schools_with_relationships} schools")
        
        # List schools if not too many
        if verbosity in ["verbose", "debug"] or (top and canon_data.get('count', 0) <= 20):
            print(f"\n   📚 Schools:")
            for school in canon_data.get('schools', []):
                school_id = school.get('id', '?')
                name = school.get('name', 'Unknown')
                emoji = school.get('emoji', '')
                op_count = school.get('operation_count', 0)
                schema = school.get('schema_version', '?')
                print(f"      {school_id:2}. {emoji} {name:20} - {op_count:2} ops (v{schema})")
    
    # Velocity (Git Archaeology)
    velocity_data = findings.get("velocity", {})
    if velocity_data.get('count', 0) > 0:
        items = velocity_data.get('items', [])
        successful = [i for i in items if not i.get('error')]
        failed = [i for i in items if i.get('error')]
        
        if successful:
            # Aggregate metrics
            total_commits = sum(i.get('total_commits', 0) for i in successful)
            total_added = sum(i.get('lines_added', 0) for i in successful)
            total_deleted = sum(i.get('lines_deleted', 0) for i in successful)
            total_net = total_added - total_deleted
            
            # Get date range (proper span calculation)
            all_first = [i['first_commit'] for i in successful if i.get('first_commit')]
            all_last = [i['last_commit'] for i in successful if i.get('last_commit')]
            
            if all_first and all_last:
                try:
                    from datetime import datetime
                    first_commit = min(all_first)
                    last_commit = max(all_last)
                    first_date = datetime.fromisoformat(first_commit.replace('Z', '+00:00'))
                    last_date = datetime.fromisoformat(last_commit.replace('Z', '+00:00'))
                    total_days = max(1, (last_date - first_date).days)
                except ValueError:
                    total_days = 1
                
                avg_lines_per_day = total_net / total_days
                
                print(f"🔥 VELOCITY: {len(successful)}/{len(items)} repos analyzed")
                print(f"   📈 Commits: {total_commits:,}")
                print(f"   💻 Net Lines: {total_net:+,}")
                print(f"   📅 Span: {first_commit[:10]} → {last_commit[:10]} ({total_days} days)")
                print(f"   ⚡ Lines/Day: {avg_lines_per_day:+,.2f}")
                
                if avg_lines_per_day > 1000:
                    print(f"   🌌 That's EMERGENCE AT VELOCITY! 🔥")
                
                if verbosity in ["verbose", "debug"] or top:
                    # Top repos by velocity
                    top_repos = sorted(successful, key=lambda r: r['lines_per_day'], reverse=True)[:10]
                    print(f"\n   🚀 Top Repos by Velocity:")
                    for i, repo in enumerate(top_repos, 1):
                        print(f"      {i:2}. {repo['name']:30} {repo['lines_per_day']:>10,.2f} lines/day")
                        print(f"          {repo['total_commits']:>4} commits, {repo['net_lines']:>+10,} net lines")
            else:
                # No date info available
                print(f"🔥 VELOCITY: {len(successful)}/{len(items)} repos analyzed")
                print(f"   📈 Commits: {total_commits:,}")
                print(f"   💻 Net Lines: {total_net:+,}")
        
        if failed:
            print(f"   ⚠️  {len(failed)} repos failed to parse")

    # PR Telemetry (The Telepath)
    pr_data = findings.get("pr-telemetry", {})
    if pr_data.get('count', 0) > 0 or pr_data.get('metrics'):
        metrics = pr_data.get('metrics', {})
        avg_health = metrics.get('average_health', 0)
        
        # Health Bar Visualization
        bar_len = 20
        filled = int(avg_health / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        
        print(f"🔮 TELEPATH: {metrics.get('total_count', 0)} PRs scanned")
        print(f"   ❤️ Health:  [{bar}] {avg_health}%")
        print(f"   🟢 Open:    {metrics.get('open_count', 0)}")
        print(f"   🧟 Stale:   {metrics.get('stale_count', 0)}")
        print(f"   ⚠️ Risk:    {metrics.get('high_risk_count', 0)}")
        
        if verbosity in ["verbose", "debug"] or top:
             items = pr_data.get('items', [])
             print(f"\n   📝 PR Details:")
             for item in items[:(top or 10)]:
                 h = item.get('health', 0)
                 icon = "🟢" if h > 80 else "🟡" if h > 50 else "🔴"
                 print(f"      {icon} #{item.get('id')} {item.get('title')[:40]:<40} (Score: {h})")

    
    print("-" * 40)
    print("See artifacts/omni/scan_debug.log for details.")



def cmd_inspect(args):
    """Deep inspection of a single repo (Super-Scan)."""
    # In v0.1, inspect is essentially scan + extra context
    # For now, we route it to scan logic but could enable 'deep' flags
    print(f"🔍 Inspecting {args.path}...")
    args.target = args.path
    args.stdout = True # Inspect usually implies wanting immediate output
    cmd_scan(args)

def cmd_gate(args):
    """Enforce quality gates based on scan results."""
    scan_file = Path(args.from_file)
    if not scan_file.exists():
        print(f"❌ Scan file not found: {scan_file}")
        sys.exit(1)
        
    data = io.load_scan(scan_file)
    success, messages = gate.check(data, strict=args.strict)
    
    for msg in messages:
        print(msg)
        
    sys.exit(0 if success else 1)

def cmd_init(args):
    """Scaffold templates."""
    from omni.scaffold import templates
    
    if args.type == 'contract':
        templates.create_contract(Path.cwd(), force=args.force)
    elif args.type == 'openapi':
        templates.create_openapi_script(Path.cwd(), force=args.force)

def cmd_audit_uuids(args):
    """Run UUID Provenance Audit."""
    from omni.core import provenance
    provenance.run_provenance_audit()

def cmd_audit_deps(args):
    """Scan and generate deps."""
    try:
        from omni.lib import requirements
        requirements.run_gen_deps(args.root, args.output)
    except ImportError:
        print("❌ omni.lib.requirements not found.")

def cmd_audit_lock(args):
    """Lock requirements."""
    try:
        from omni.lib import requirements
        requirements.run_lock_deps(args.input, args.output)
    except ImportError:
        print("❌ omni.lib.requirements not found.")

def cmd_audit_list(args):
    """Run pip list."""
    try:
        from omni.lib import requirements
        requirements.run_pip_list(args.filter)
    except ImportError:
        print("❌ omni.lib.requirements not found.")

def cmd_audit_install(args):
    """Install requirements."""
    try:
        from omni.lib import requirements
        requirements.run_install_reqs(args.file)
    except ImportError:
        print("❌ omni.lib.requirements not found.")

def cmd_canon(args):
    """
    Canon lock management (Science Officer - Build The Law).
    
    Commands:
      omni canon rebuild              # Rebuild all 3 locks
      omni canon rebuild --language   # Rebuild canon.lock.yaml only
      omni canon verify               # Verify all locks
      omni canon scan --school 14     # Scan school operations
      omni canon hash                 # Print lock hashes
    """
    try:
        # Import builders defensively - they are federation-specific
        from omni.builders.codecraft import rosetta_archaeologist
        # Note: These builder imports might need specific paths if not in __init__
        # For now, we assume they might be missing in open source
        import omni.builders as builders # Check existence
    except ImportError:
        print("❌ Canon builders not available in this installation.")
        return

    # Attempt to use specific builders if they exist
    # (Implementation specific to User's environment)
    print("⚠️  Canon management commands are currently proprietary.")

def cmd_registry_render(args):
    """Render Registry MD from Frontmatter."""
    from omni.core import renderer
    renderer.regenerate_registry()

def cmd_registry_get(args):
    """The Boss Hammer: Query the registry for any entity (including virtual projects)."""
    from omni.core import registry
    import json
    import yaml

    # Load ALL projects, including virtual ones
    projects = registry.parse_registry(include_virtual=True)
    
    target = args.name.lower()
    found = None
    
    # Fuzzy Search Logic
    for p in projects:
        # Check UUID, Name, or Display Name
        uuid_str = str(p.get('uuid', '')).lower()
        name = p.get('name', '').lower()
        display = p.get('display_name', '').lower()
        
        if (target == uuid_str or 
            target in name or 
            target in display or
            name == target or
            display == target):
            found = p
            break
            
    if found:
        # Output clean JSON or YAML
        if args.json:
            print(json.dumps(found, indent=2, default=str))
        else:
            # YAML is easier to read for humans
            print(yaml.dump(found, sort_keys=False, default_flow_style=False))
    else:
        print(f"👻 Entity '{args.name}' not found in the Registry.")
        print(f"\nHint: Try 'omni scan registry' to see all {len(projects)} projects.")

def cmd_registry_summary(args):
    """Boss Hammer Summary: Show registry statistics and breakdown."""
    import json
    from collections import defaultdict

    # Use CartographyPillar via settings shim
    try:
        from omni.config.settings import get_cartography
        
        carto = get_cartography()
        if not carto:
            print("❌ CartographyPillar not available")
            return
        
        registry_data = carto.get_registry("projects")
        
        if not registry_data:
            print("❌ PROJECT_REGISTRY_V1.yaml not found")
            return
            
        stats = registry_data.get('stats', {})
        projects = registry_data.get('projects', [])
        
    except ImportError:
        print("❌ federation_heart not available - cannot use CartographyPillar")
        return
    except Exception as e:
        print(f"❌ Failed to load registry: {e}")
        return
    
    # Calculate additional stats
    workspace_counts = defaultdict(int)
    visibility_counts = defaultdict(int)
    status_counts = defaultdict(int)
    classification_counts = defaultdict(int)
    
    for p in projects:
        # Count by workspace (first path only)
        paths = p.get('local_paths', [])
        if paths:
            first_path = str(paths[0])
            if 'Infrastructure' in first_path:
                workspace_counts['Infrastructure'] += 1
            elif 'Workspace' in first_path:
                workspace_counts['Workspace'] += 1
            elif 'Deployment' in first_path:
                workspace_counts['Deployment'] += 1
            elif 'Projects' in first_path:
                workspace_counts['Projects'] += 1
            else:
                workspace_counts['Other'] += 1
        
        # Count by visibility
        vis = p.get('visibility', 'unknown')
        visibility_counts[vis] += 1
        
        # Count by status
        status = p.get('status', 'unknown')
        status_counts[status] += 1
        
        # Count by classification
        classification = p.get('classification', 'unknown')
        classification_counts[classification] += 1
    
    # Output
    print("📊 PROJECT REGISTRY SUMMARY")
    print("=" * 50)
    print(f"\n🗂️  Total Projects: {stats.get('total', len(projects))}")
    print(f"   ├─ With GitHub: {stats.get('github', '?')}")
    print(f"   ├─ Linked (local): {stats.get('linked', '?')}")
    print(f"   ├─ Cloud Only: {stats.get('cloud_only', '?')}")
    print(f"   ├─ Virtual (CMP-only): {stats.get('virtual', '?')}")
    print(f"   └─ Snapshots: {stats.get('local_snapshot', '?')}")
    
    print(f"\n🗺️  Workspace Distribution:")
    for workspace, count in sorted(workspace_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   ├─ {workspace}: {count}")
    
    print(f"\n🔒 Visibility:")
    for vis, count in sorted(visibility_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   ├─ {vis}: {count}")
    
    print(f"\n📋 Classification:")
    for classification, count in sorted(classification_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   ├─ {classification}: {count}")
    
    print(f"\n✅ Status:")
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   ├─ {status}: {count}")
    
    total = stats.get('total', len(projects))
    linked = stats.get('linked', 0)
    if total > 0:
        coverage = linked / total * 100
    else:
        coverage = 0.0
    print(f"\n💡 Local Path Coverage: {linked}/{total} = {coverage:.1f}%")
    
    if args.json:
        print("\n" + "=" * 50)
        print("JSON Output:")
        output = {
            "total": total,
            "stats": stats,
            "workspace_distribution": dict(workspace_counts),
            "visibility": dict(visibility_counts),
            "classification": dict(classification_counts),
            "status": dict(status_counts),
            "coverage_percent": round(coverage, 1)
        }
        print(json.dumps(output, indent=2))

def cmd_library(args):
    """
    Run the Grand Librarian (ACE's Taxonomy Engine).
    
    Workflow:
      omni scan library → Generate census
      omni library curate → Apply taxonomy, generate INSTRUCTION_REGISTRY_V1.yaml
    """
    import yaml
    try:
        from omni.core import librarian
    except ImportError:
        print("❌ omni.core.librarian module not found.")
        print("   This feature requires the Federation Librarian component.")
        return

    from omni.scanners import library
    
    if args.library_command == "curate":
        # Load census
        census_file = Path(args.census) if args.census else ARTIFACTS_DIR / "scan.library.json"
        if not census_file.exists():
            print(f"❌ Census file not found: {census_file}")
            print("   Run 'omni scan library' first to generate census.")
            return
            
        with census_file.open("r", encoding="utf-8") as f:
            scan_data = json.load(f)
        
        # Extract library census from scan findings
        census_data = scan_data.get("findings", {}).get("library", {})
        if not census_data:
            print("❌ No library census found in scan results")
            return
        
        # Load taxonomy
        taxonomy_file = OMNI_ROOT / "templates" / "library_taxonomy.yaml"
        if not taxonomy_file.exists():
             print(f"❌ Taxonomy template not found: {taxonomy_file}")
             return

        with taxonomy_file.open("r", encoding="utf-8") as f:
            taxonomy = yaml.safe_load(f)
            templates = taxonomy.get("templates", [])
        
        # Curate entries
        print(f"[LIBRARY] Curating {len(census_data.get('files', []))} files with taxonomy...")
        entries = librarian.curate_entries_from_census(census_data.get("files", []), templates)
        print(f"[OK] Curated {len(entries)} entries")
        
        # Generate INSTRUCTION_REGISTRY if requested
        if args.output_format == "instruction-registry":
            registry = librarian.export_to_instruction_registry(entries)
            
            # Smart domain detection: All registries go to Infrastructure/governance/registry
            # but filename changes based on which domain was scanned
            if not args.output:
                # Detect domain from scan metadata
                try:
                    scan_target = Path(scan_data.get("metadata", {}).get("target", ".")).resolve()
                except:
                    scan_target = Path(".")
                
                # Check if scan was from Workspace
                if "Workspace" in str(scan_target):
                    filename = "WORKSPACE_INSTRUCTION_REGISTRY_V1.yaml"
                    print(f"[AUTO-DETECT] Domain: Workspace → {filename}")
                else:
                    # Infrastructure or default
                    filename = "INSTRUCTION_REGISTRY_V1.yaml"
                    print(f"[AUTO-DETECT] Domain: Infrastructure → {filename}")
                
                output_path = REGISTRY_ROOT / "instructions" / filename
            else:
                output_path = Path(args.output)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with output_path.open("w", encoding="utf-8") as f:
                yaml.dump(registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            print(f"✅ INSTRUCTION_REGISTRY_V1.yaml written to {output_path}")
            print(f"   Total instructions: {registry['metadata']['total_instructions']}")
        else:
            # Standard library manifest output
            manifest = {
                "schema": "omni.library.manifest.v1",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "entries": [asdict(e) for e in entries]
            }
            
            output_path = Path(args.output) if args.output else ARTIFACTS_DIR / "library_manifest.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            
            print(f"✅ Library manifest written to {output_path}")
    
    elif args.library_command == "organize":
        print("⚠️ Organize command not yet implemented (would move/link files by taxonomy)")
        print("   For safety, use --dry-run before actual organization.")

def cmd_introspect(args):
    """
    Omni examines itself - scanners, commands, drift detection.
    
    Pattern: Scan Self → Report Reality → Detect Drift
    """
    from omni.commands.introspect import cmd_introspect as introspect_impl
    return introspect_impl(args)

def cmd_interpret(args):
    """
    AI-powered analysis of scan results (Omni Brain).
    
    Pattern: Scan → Analyze → Synthesize → Explain
    """
    from omni.core.brain import get_brain
    from datetime import datetime
    
    # 1. Run scan if no input file provided
    if not args.input:
        print("👀 No input file provided. Running scan first...")
        # Run scan and capture results
        scan_args = argparse.Namespace(
            target=args.target,
            scanners=args.scanners,
            all=False,
            report=False,
            verbosity="default"
        )
        cmd_scan(scan_args)
        
        # Load the generated scan file
        scan_file = ARTIFACTS_DIR / "scan.json"
        if not scan_file.exists():
            print("❌ Scan failed to generate results")
            return
            
        with scan_file.open("r", encoding="utf-8") as f:
            scan_results = json.load(f)
    else:
        # Load provided scan file
        with open(args.input, "r", encoding="utf-8") as f:
            scan_results = json.load(f)
    
    # 2. Engage the Brain (Cognition)
    print("🧠 Engaging Logic Engine...")
    brain = get_brain()
    analysis = brain.analyze(scan_results, prompt=args.query)
    
    # 3. Output (Articulation)
    print("\n" + "="*80)
    print("💡 OMNI ANALYSIS")
    print("="*80)
    print(analysis)
    print("="*80)
    print(f"\nAnalyzed at: {datetime.utcnow().isoformat()}Z")

def cmd_map_ecosystem(args):
    """Run Ecosystem Cartographer."""
    from omni.core import cartographer
    # Simple wrapper to run same logic as main block of original script
    # For now, just instantiate and analyze
    mapper = cartographer.EcosystemCartographer(base_path=args.root)
    if args.action == 'analyze':
        mapper.analyze_ecosystem()
    elif args.action == 'guide':
        mapper.analyze_ecosystem()
        mapper.generate_comprehensive_guide()
    elif args.action == 'visualize':
        mapper.analyze_ecosystem()
        mapper.visualize_ecosystem()

def cmd_inspect_tree(args):
    """Run Tree Cleaner."""
    from omni.core import tree
    # Call main logic from tree module
    # We might need to adjust tree.py to accept args cleaner, but it uses sys.argv
    # Let's adjust tree.py to have a run function first, or mock sys.argv?
    # Better to refactor tree.py slightly.
    # For now, assuming refactor:
    tree.generate_tree(args.root, args.output)

def cmd_registry_events(args):
    """Generate Event Registry YAML."""
    from omni.core import registry_events
    registry_events.run_registry_events(args.output, args.scan_file)

def cmd_report(args):
    """Generate reports."""
    from omni.core import reporting
    # Resolve paths
    # We default input to where we usually save registry
    # Try multiple spots
    possible_inputs = [
        Path(args.input) if args.input else None,
        REGISTRY_ROOT / "events" / "EVENT_REGISTRY.yaml",  # Canonical location
        Path("EVENT_REGISTRY.yaml"),  # CWD fallback
        ARTIFACTS_DIR / "EVENT_REGISTRY.yaml"  # Legacy fallback
    ]
    
    registry_path = None
    for p in possible_inputs:
        if p and p.exists():
            registry_path = p
            break
            
    if not registry_path:
        print("❌ Could not find EVENT_REGISTRY.yaml. Run 'omni registry events' first or separate --input.")
        sys.exit(1)
        
    if args.type == 'event_debt':
        report = reporting.generate_debt_report(registry_path, Path(args.output))
        # Now generated, we strictly save it (previously func did it, now returns dict)
        if report:
            with open(args.output, "w", encoding="utf-8") as f:
                yaml.dump(report, f, sort_keys=False)
            print(f"[SUCCESS] Debt report saved to {args.output}")
            print(f"  Debt Items: {report['summary']['total_debt']}")
            
    elif args.type == 'gap_analysis':
         # Default logs path
         logs_path = Path("var/events/federation_bus.ndjson")
         # Allow override via input arg if needed, but defaulting to standard log
         if args.input:
             logs_path = Path(args.input)
             
         if not logs_path.exists():
             # Try absolute from infra root if relative fails
             # Assuming CWD is tools/omni
             logs_path = Path("../../var/events/federation_bus.ndjson")
         
         report = reporting.generate_gap_analysis(registry_path, logs_path)
         
         with open(args.output, "w", encoding="utf-8") as f:
             yaml.dump(report, f, sort_keys=False)
             
         print(f"[SUCCESS] Gap Analysis saved to {args.output}")
         s = report['summary']
         print(f"  Defined: {s['defined_count']} | Observed: {s['observed_count']}")
         print(f"  Latent (Zombies): {s['latent_count']} | Emergent (Rogues): {s['emergent_count']}")
         if report.get('error'):
             print(f"  [WARN] {report['error']}")


def main():
    parser = argparse.ArgumentParser(prog="omni", description="Federation Governance Tricorder")
    parser.add_argument("--version", action="version", version=f"omni {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # SCAN
    p_scan = subparsers.add_parser("scan", help="Scan a target for surfaces and health")
    p_scan.add_argument("target", nargs="?", default=".", help="Target directory (default: current dir)")
    p_scan.add_argument("--all", action="store_true", help="Scan entire Registry")
    p_scan.add_argument("--stdout", action="store_true", help="Print findings to stdout")
    p_scan.add_argument("--format", choices=["json", "summary"], default="summary", help="Output format (default: summary)")
    p_scan.add_argument("--top", type=int, help="Limit output to top N items")
    p_scan.add_argument("--scanners", help="Comma-separated list of scanners to run (e.g. 'events,surfaces')")
    
    # Canon scanner specific flags
    p_scan.add_argument("--canon-source", action="store_true", help="(canon scanner) Scan YAML front matter instead of canon.lock")
    p_scan.add_argument("--canon-verify", action="store_true", help="(canon scanner) Compare source vs built canon")
    p_scan.add_argument("--canon-school", metavar="SCHOOL", help="(canon scanner) Filter to specific school (number or name)")
    
    # Git scanner specific flags
    p_scan.add_argument("--github", action="store_true", help="(git scanner) Use gh CLI to scan all GitHub repos (user + orgs)")
    p_scan.add_argument("--no-update-registry", action="store_true", help="(git scanner) Don't auto-update repo_inventory.json")
    
    # Velocity scanner specific flags  
    p_scan.add_argument("--since", metavar="DATE", help="(velocity scanner) Filter commits since date (e.g., '2025-01-01', '1 month ago')")
    
    # Log Levels
    p_scan.add_argument("--quiet", "-q", dest="verbosity", action="store_const", const="quiet", help="Minimal output")
    p_scan.add_argument("--verbose", "-v", dest="verbosity", action="store_const", const="verbose", help="Verbose output")
    p_scan.add_argument("--debug", dest="verbosity", action="store_const", const="debug", help="Debug output")
    p_scan.set_defaults(func=cmd_scan, verbosity="default")

    # INSPECT
    p_inspect = subparsers.add_parser("inspect", help="Deep inspection of a path")
    p_inspect.add_argument("path", help="Path to inspect")
    p_inspect.set_defaults(func=cmd_inspect)

    # INTROSPECT (Self-scan)
    p_introspect = subparsers.add_parser("introspect", help="Omni examines itself (scanners, commands, drift)")
    p_introspect.add_argument("--drift", action="store_true", help="Show drift between manifests and filesystem")
    p_introspect.add_argument("--scanners", dest="scanners_only", action="store_true", help="Show scanner inventory only")
    p_introspect.set_defaults(func=cmd_introspect)

    # GATE
    p_gate = subparsers.add_parser("gate", help="Enforce quality gates")
    p_gate.add_argument("--from", dest="from_file", default=str(ARTIFACTS_DIR / "scan.json"), help="Input scan file")
    p_gate.add_argument("--strict", action="store_true", help="Fail on any partial/warning")
    p_gate.set_defaults(func=cmd_gate)

    # INIT
    p_init = subparsers.add_parser("init", help="Scaffold templates")
    p_init.add_argument("type", choices=["contract", "openapi"], help="Template type")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files")
    p_init.set_defaults(func=cmd_init)

    # AUDIT
    p_audit = subparsers.add_parser("audit", help="Run audit tools")
    sp_audit = p_audit.add_subparsers(dest="audit_command", required=True)
    
    # audit uuids
    p_audit_uuids = sp_audit.add_parser("uuids", help="Scan UUID provenance (unique/canonical/orphans)")
    p_audit_uuids.set_defaults(func=cmd_audit_uuids)


    # audit deps
    p_audit_deps = sp_audit.add_parser("deps", help="Scan and generate federation requirements")
    p_audit_deps.add_argument("--root", default=str(Path.cwd().parent), help="Root to scan (default: Infrastructure)")
    p_audit_deps.add_argument("-o", "--output", default="requirements.federation.txt", help="Output file")
    p_audit_deps.set_defaults(func=cmd_audit_deps)

    # audit lock
    p_audit_lock = sp_audit.add_parser("lock", help="Lock requirements to installed versions")
    p_audit_lock.add_argument("-o", "--output", default="requirements.federation.locked.txt", help="Output file")
    p_audit_lock.set_defaults(func=cmd_audit_lock)

    # audit list
    p_audit_list = sp_audit.add_parser("list", help="List installed packages (pip list)")
    p_audit_list.add_argument("filter", nargs="?", default="", help="Optional filter string")
    p_audit_list.set_defaults(func=cmd_audit_list)

    # audit install
    p_audit_install = sp_audit.add_parser("install", help="Install requirements (pip/uv install)")
    p_audit_install.add_argument("-f", "--file", default="requirements.federation.locked.txt", help="Requirements file")
    p_audit_install.set_defaults(func=cmd_audit_install)

    # CANON (Science Officer - Build The Law)
    p_canon = subparsers.add_parser("canon", help="Canon lock management (Build The Law)")
    sp_canon = p_canon.add_subparsers(dest="canon_action", required=True)
    
    # canon rebuild
    p_canon_rebuild = sp_canon.add_parser("rebuild", help="Rebuild canon locks (all or specific)")
    p_canon_rebuild.add_argument("--language", dest="only_language", action="store_true", help="Rebuild canon.lock.yaml only")
    p_canon_rebuild.add_argument("--partitions", dest="only_partitions", action="store_true", help="Rebuild canon.partitions.lock.yaml only")
    p_canon_rebuild.add_argument("--executors", dest="only_executors", action="store_true", help="Rebuild canon.executors.lock.yaml only")
    p_canon_rebuild.set_defaults(func=cmd_canon)
    
    # canon verify
    p_canon_verify = sp_canon.add_parser("verify", help="Verify canon lock integrity")
    p_canon_verify.set_defaults(func=cmd_canon)
    
    # canon scan
    p_canon_scan = sp_canon.add_parser("scan", help="Scan school operations from canon.lock")
    p_canon_scan.add_argument("--canon", help="Path to canon.lock file (default: codecraft-native/canon/canon.lock.yaml)")
    p_canon_scan.add_argument("--school", help="School number (e.g. 14) or name (e.g. benediction). Omit for ALL schools.")
    p_canon_scan.add_argument("--format", choices=["detailed", "summary", "json"], default="summary", help="Output format")
    p_canon_scan.set_defaults(func=cmd_canon)
    
    # canon hash
    p_canon_hash = sp_canon.add_parser("hash", help="Print SHA-256 hashes of all canon locks")
    p_canon_hash.set_defaults(func=cmd_canon)

    # REGISTRY
    p_reg = subparsers.add_parser("registry", help="Registry management tools")
    sp_reg = p_reg.add_subparsers(dest="registry_command", required=True)
    
    # registry render
    p_reg_render = sp_reg.add_parser("render", help="Regenerate MD tables from Frontmatter")
    p_reg_render.set_defaults(func=cmd_registry_render)

    # registry get (The Boss Hammer)
    p_reg_get = sp_reg.add_parser("get", help="Query a registry entity (includes virtual projects)")
    p_reg_get.add_argument("name", help="Name or UUID of the project")
    p_reg_get.add_argument("--json", action="store_true", help="Output as JSON instead of YAML")
    p_reg_get.set_defaults(func=cmd_registry_get)
    
    # registry summary (Boss Hammer Summary)
    p_reg_summary = sp_reg.add_parser("summary", help="Show registry statistics and breakdown")
    p_reg_summary.add_argument("--json", action="store_true", help="Output as JSON")
    p_reg_summary.set_defaults(func=cmd_registry_summary)
    
    # registry events
    p_reg_events = sp_reg.add_parser("events", help="Generate Event Registry from scan")
    p_reg_events.add_argument("-o", "--output", default=str(REGISTRY_ROOT / "events" / "EVENT_REGISTRY.yaml"), help="Output file")
    p_reg_events.add_argument("--scan-file", help="Input scan file (default: auto-detect)")
    p_reg_events.set_defaults(func=cmd_registry_events)

    # LIBRARY (Grand Librarian)
    p_lib = subparsers.add_parser("library", help="Grand Librarian - Taxonomy-aware documentation curation")
    sp_lib = p_lib.add_subparsers(dest="library_command", required=True)
    
    # library curate
    p_lib_curate = sp_lib.add_parser("curate", help="Curate census with taxonomy → generate registries")
    p_lib_curate.add_argument("--census", help="Input census file (default: artifacts/omni/scan.library.json)")
    p_lib_curate.add_argument("-o", "--output", help="Output file (default: auto-detect from format)")
    p_lib_curate.add_argument("--format", dest="output_format", choices=["manifest", "instruction-registry"], default="instruction-registry", help="Output format")
    p_lib_curate.set_defaults(func=cmd_library)
    
    # library organize (future)
    p_lib_org = sp_lib.add_parser("organize", help="Organize files into taxonomy-based folders (not yet implemented)")
    p_lib_org.add_argument("--manifest", required=True, help="Library manifest file")
    p_lib_org.add_argument("--target", required=True, help="Target root directory")
    p_lib_org.add_argument("--dry-run", action="store_true", help="Simulate without moving files")
    p_lib_org.set_defaults(func=cmd_library)
    
    # INTERPRET (Omni Brain)
    p_interpret = subparsers.add_parser("interpret", help="AI-powered analysis of scan results (Science Officer mode)")
    p_interpret.add_argument("target", nargs="?", default=".", help="Target to scan (if no input file)")
    p_interpret.add_argument("--input", "-i", help="Input scan file (default: run scan first)")
    p_interpret.add_argument("--scanners", help="Scanners to run (if no input file)")
    p_interpret.add_argument("--query", "-q", help="Custom analysis prompt")
    p_interpret.set_defaults(func=cmd_interpret)
    
    # MAP
    p_map = subparsers.add_parser("map", help="Ecosystem Cartography")
    p_map.add_argument("--root", default=str(Path.cwd().parent.parent), help="Root to map") # Default to user root?
    p_map.add_argument("action", choices=['analyze', 'guide', 'visualize'], default='analyze', nargs='?')
    p_map.set_defaults(func=cmd_map_ecosystem)

    # REPORT
    p_rep = subparsers.add_parser("report", help="Generate reports")
    p_rep.add_argument("--type", choices=['event_debt', 'gap_analysis'], required=True, help="Report type")
    p_rep.add_argument("--input", help="Input file (Registry or Logs depending on context)")
    p_rep.add_argument("-o", "--output", default=str(ARTIFACTS_DIR / "report.yaml"), help="Output file")
    p_rep.set_defaults(func=cmd_report)
    
    # COMPARE EVENTS (Alias)
    p_cmp = subparsers.add_parser("compare-events", help="Compare Static Registry vs Dynamic Logs")
    p_cmp.add_argument("-o", "--output", default=str(ARTIFACTS_DIR / "event_gap_analysis.yaml"), help="Output file")
    p_cmp.set_defaults(func=lambda args: cmd_report(argparse.Namespace(type='gap_analysis', input=None, output=args.output)))

    # TREE (under INSPECT)

    # TREE (under INSPECT)
    p_tree = subparsers.add_parser("tree", help="Generate clean directory tree")
    p_tree.add_argument("root", nargs="?", default=".", help="Root to graph")
    p_tree.add_argument("-o", "--output", default="tree.md", help="Output file")
    p_tree.set_defaults(func=cmd_inspect_tree)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
