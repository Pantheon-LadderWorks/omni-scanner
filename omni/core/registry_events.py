from pathlib import Path
import json
import yaml
from datetime import datetime
from omni.core import io

def run_registry_events(output_path: str = "EVENT_REGISTRY.yaml", scan_file_path: str = None):
    """
    Generates EVENT_REGISTRY.yaml from the latest scan.json.
    """
    scan_file = None
    if scan_file_path:
        scan_file = Path(scan_file_path)
    else:
        # Default Priority: scan.events.json -> scan.events_hooks.json -> scan.json
        # Calculate Artifacts Dir relative to this file (omni/core/registry_events.py)
        # Expected: omni/artifacts/omni
        # This file: omni/core/registry_events.py
        # Root: omni/
        omni_root = Path(__file__).parent.parent
        base = omni_root / "artifacts" / "omni"
        
        candidates = [
            base / "scan.events.json",
            base / "scan.events_hooks.json",
            base / "scan.hooks_events.json",
            base / "scan.json"
        ]
        for c in candidates:
            if c.exists():
                scan_file = c
                break
                
    if not scan_file or not scan_file.exists():
        print(f"[ERR] No scan.json found. Checked priority locations or {scan_file_path}. Run 'omni scan' first.")
        return

    scan_data = io.load_scan(scan_file)
    findings = scan_data.get("findings", {})
    events = findings.get("events", {}).get("items", [])
    hooks = findings.get("hooks", {}).get("items", [])
    
    reg_data = _aggregate_events(events, hooks)
    
    # Save to YAML
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(reg_data, f, sort_keys=False)
        
    print(f"[SUCCESS] Event Registry generated at {output_path}")

def _aggregate_events(raw_events: list, hooks: list = None) -> dict:
    """
    Aggregates raw event findings into a structured registry (Mega-Compliant).
    """
    registry = {
        "registry_version": "1.1",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sources": [{"path": "Infrastructure (Omni Scan)", "type": "static"}],
        "events": [],
        "dynamic_publish_sites": []
    }
    
    # Group by Name
    grouped_events = {}
    
    for e in raw_events:
        name = e.get("event_guess", "unknown")
        
        # Dedupe unknown names using file location
        if name == "unknown":
            match = e.get("match", "")
            if len(match) < 50:
                 name = f"unknown:{match}"
            else:
                 name = f"unknown:{e.get('file')}:{e.get('line')}"
        
        if name not in grouped_events:
            # Initialize with first-seen metadata (lane typically consistent for same event)
            grouped_events[name] = {
                "name": name,
                "lane": e.get("lane", "local"), 
                "producers": [],
                "observed": False,
                # Aggregate patterns to see variety
                "_patterns": set()
            }
            
        entry = grouped_events[name]
        
        # Add Producer
        entry["producers"].append({
            "component": e.get("project", "unknown"), # Proxy for component
            "location": f"{e.get('file')}:{e.get('line')}",
            "transport": e.get("transport", "unknown"),
            "confidence": e.get("confidence", 0.0)
        })
        entry["_patterns"].add(e.get("pattern"))
        
        # Update Lane if we find a 'crown' or 'federation' signal that overrides 'local'
        if entry["lane"] == "local" and e.get("lane") in ["crown", "federation"]:
            entry["lane"] = e.get("lane")

    # Finalize List
    for key, val in grouped_events.items():
        # Remove internal helper keys
        val.pop("_patterns", None)
        
        # Classification Logic
        is_dynamic = key.startswith("dynamic:")
        
        # Determine aggregate confidence (max of producers?)
        max_conf = max([p.get("confidence", 0.0) for p in val["producers"]])
        
        # Reality Grading
        grade = "F"
        if is_dynamic:
            grade = "D" # Dynamic/Unknown
        elif max_conf >= 0.8:
            grade = "B" # High Confidence Literal
             # If we had consumers verify, it would be A
        elif max_conf >= 0.5:
            grade = "C" # Likely real but maybe hook/stub?
            
        val["grade"] = grade
        
        # The Filter Rule:
        if not is_dynamic and max_conf >= 0.7:
             registry["events"].append(val)
        else:
             registry["dynamic_publish_sites"].append(val)
             
    # Add Hooks Section
    if hooks:
        registry["hooks"] = {
            "producers": [],
            "consumers": [],
            "stubs": []
        }
        seen_hooks = set()
        for h in hooks:
            kind = h.get("kind", "unknown")
            # Dedupe Key: path + match
            # But "location" is usually file.name:line, which isn't unique enough across dirs?
            # Actually scanner now sends 'file' as full path.
            # Let's use file path (relative to repo root if possible, but absolute str here) and match.
            
            key = f"{kind}:{h.get('file')}:{h.get('match')}"
            if key in seen_hooks:
                continue
            seen_hooks.add(key)

            item = {
                "description": h.get("description"),
                "location": h.get("location"),
                "file": h.get("file"),
                "match": h.get("match")[:100] # Truncate match
            }
            
            if kind == "polling_loop":
                registry["hooks"]["consumers"].append(item)
            elif kind == "direct_http_egress" or kind == "state_persistence":
                registry["hooks"]["producers"].append(item)
            elif kind == "bus_stub":
                registry["hooks"]["stubs"].append(item)

    return registry
