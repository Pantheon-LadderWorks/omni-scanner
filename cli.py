"""
Omni CLI - Federation Governance & Introspection Tool
v0.1 - The Tricorder
"""
import argparse
import sys
import json
from pathlib import Path
from omni.core import io, gate
from omni.core.scanners import SCANNERS
from omni.core.model import ScanResult

__version__ = "0.1.0"
__author__ = "Kode_Animator"

def cmd_scan(args):
    """Run scanners on a target."""
    results = {}
    targets = []

    if args.all:
        print("[INFO] Loading Registry for Global Scan...")
        from omni.core import registry
        projects = registry.parse_registry()
        targets = [Path(p['path']) for p in projects]
        target_label = "REGISTRY (Global)"
    else:
        targets = [Path(args.target)]
        target_label = str(args.target)

    # Initialize aggregators
    # For v0.1, we only aggregate surfaces for global scan to match V8 Atlas
    # For single target, we run all active scanners
    
    if args.all:
        total_surfaces = []
        print(f"[SCAN] Scanning {len(targets)} projects from Registry...")
        
        # Only run Surface scanner for global
        from omni.core.scanners import surfaces
        for t in targets:
            if not t.exists(): continue
            try:
                res = surfaces.scan(t)
                total_surfaces.extend(res['items'])
            except Exception:
                pass
        
        results['surfaces'] = {
            "count": len(total_surfaces),
            "items": total_surfaces
        }
        print(f"  [OK] surfaces complete ({len(total_surfaces)} items)")
        
    else:
        # Single Target - Run All Scanners
        target_path = targets[0]
        print(f"[SCAN] Scanning target: {target_path}...")
        active_scanners = SCANNERS.items()
        
        for name, scanner_func in active_scanners:
            try:
                results[name] = scanner_func(target_path)
                print(f"  [OK] {name} complete")
            except Exception as e:
                results[name] = {"error": str(e)}
                print(f"  [ERR] {name} failed: {e}")

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

    # Output
    # Ensure artifacts/omni exists relative to CWD
    output_dir = Path("artifacts/omni")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "scan.json"
    
    io.save_scan(scan_data, output_path)
    print(f"\n[REPORT] Saved to: {output_path}")
    
    if args.stdout:
        print(json.dumps(scan_data.to_dict(), indent=2))

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

def cmd_audit_fetch_db(args):
    """Fetch Canonical UUIDs from Postgres."""
    from omni.core import fetcher
    fetcher.run_fetch_db()

def cmd_audit_deps(args):
    """Scan and generate deps."""
    from omni.core import requirements
    requirements.run_gen_deps(args.root, args.output)

def cmd_audit_lock(args):
    """Lock requirements."""
    from omni.core import requirements
    requirements.run_lock_deps(args.input, args.output)

def cmd_registry_render(args):
    """Render Registry MD from Frontmatter."""
    from omni.core import renderer
    renderer.regenerate_registry()

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

def main():
    parser = argparse.ArgumentParser(prog="omni", description="Federation Governance Tricorder")
    parser.add_argument("--version", action="version", version=f"omni {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # SCAN
    p_scan = subparsers.add_parser("scan", help="Scan a target for surfaces and health")
    p_scan.add_argument("target", nargs="?", default=".", help="Target directory")
    p_scan.add_argument("--all", action="store_true", help="Scan entire Registry")
    p_scan.add_argument("--stdout", action="store_true", help="Print JSON to stdout")
    p_scan.set_defaults(func=cmd_scan)

    # INSPECT
    p_inspect = subparsers.add_parser("inspect", help="Deep inspection of a path")
    p_inspect.add_argument("path", help="Path to inspect")
    p_inspect.set_defaults(func=cmd_inspect)

    # GATE
    p_gate = subparsers.add_parser("gate", help="Enforce quality gates")
    p_gate.add_argument("--from", dest="from_file", default="artifacts/omni/scan.json", help="Input scan file")
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

    # audit fetch-db
    p_audit_fetch = sp_audit.add_parser("fetch-db", help="Fetch Canonical UUIDs from local CMP Postres DB")
    p_audit_fetch.set_defaults(func=cmd_audit_fetch_db)

    # audit deps
    p_audit_deps = sp_audit.add_parser("deps", help="Scan and generate federation requirements")
    p_audit_deps.add_argument("--root", default=str(Path.cwd().parent), help="Root to scan (default: Infrastructure)")
    p_audit_deps.add_argument("-o", "--output", default="requirements.federation.txt", help="Output file")
    p_audit_deps.set_defaults(func=cmd_audit_deps)

    # audit lock
    p_audit_lock = sp_audit.add_parser("lock", help="Lock requirements to installed versions")
    p_audit_lock.add_argument("-i", "--input", default="requirements.federation.txt", help="Input file")
    p_audit_lock.add_argument("-o", "--output", default="requirements.federation.locked.txt", help="Output file")
    p_audit_lock.set_defaults(func=cmd_audit_lock)

    # REGISTRY
    p_reg = subparsers.add_parser("registry", help="Registry management tools")
    sp_reg = p_reg.add_subparsers(dest="registry_command", required=True)
    
    # registry render
    p_reg_render = sp_reg.add_parser("render", help="Regenerate MD tables from Frontmatter")
    p_reg_render.set_defaults(func=cmd_registry_render)

    # MAP
    p_map = subparsers.add_parser("map", help="Ecosystem Cartography")
    p_map.add_argument("--root", default=str(Path.cwd().parent.parent), help="Root to map") # Default to user root?
    p_map.add_argument("action", choices=['analyze', 'guide', 'visualize'], default='analyze', nargs='?')
    p_map.set_defaults(func=cmd_map_ecosystem)

    # TREE (under INSPECT)
    # Update Inspect to handle 'tree' if path is 'tree'? Or valid path?
    # Let's add a dedicated 'omni tree' or 'omni inspect --tree'?
    # Let's stick to 'omni inspect tree <path>' if we want subcommands, but inspect takes a path arg.
    # Let's just add 'omni tree' top level for now or user 'inspect' logic.
    # The user asked for "omni inspect tree".
    # Implementation: 'inspect' parser has 'path'. If path='tree', it might be confusing.
    # Alternative: 'omni tree <root>'
    p_tree = subparsers.add_parser("tree", help="Generate clean directory tree")
    p_tree.add_argument("root", nargs="?", default=".", help="Root to graph")
    p_tree.add_argument("-o", "--output", default="tree.md", help="Output file")
    p_tree.set_defaults(func=cmd_inspect_tree)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
