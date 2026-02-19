import yaml
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone

def generate_debt_report(registry_path: Path, output_path: Path):
    """
    Parses EVENT_REGISTRY.yaml and produces a debt report.
    """
    if not registry_path.exists():
        print(f"[ERR] Registry not found: {registry_path}")
        return

    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = yaml.safe_load(f)
    except Exception as e:
        print(f"[ERR] Failed to load registry: {e}")
        return

    events = registry.get("events", [])
    debt_items = []

    for event in events:
        name = event.get("name", "")
        producers = event.get("producers", [])
        
        # Check for debt conditions
        debt_kind = None
        reason = None
        suggestion = None

        if name.startswith("unknown:"):
            debt_kind = "unknown_event_name"
            reason = "dynamic publish() prevents registry truth"
            suggestion = "publish(LITERAL_EVENT_NAME, data) or publish(CONST_STRING, data)"
        
        elif "event.name" in name:
            debt_kind = "placeholder_event"
            reason = "placeholder name detected"
            suggestion = "replace with concrete event name"
            
        elif "crown://" in name:
            debt_kind = "uri_event_name"
            reason = "URI-style event name (legacy)"
            suggestion = "use dot.notation namespace"
            
        elif name.endswith(".publish(event)") or "publish(event)" in name:
             debt_kind = "dynamic_publish"
             reason = "dynamic publish() var detected"
             suggestion = "use literal string"

        # Lane mismatch check
        elif name.startswith("crown.") and event.get("lane") == "federation":
            debt_kind = "lane_mismatch"
            reason = "crown.* event detected in federation lane"
            suggestion = "set lane=crown or rename namespace"

        # Archived emitter check
        is_archived = False
        producer_locs = []
        for p in producers:
            loc = p.get("location", "")
            producer_locs.append(loc)
            if any(x in loc for x in ["INBOX", "archive", "older_versions"]):
                is_archived = True
        
        if is_archived and not debt_kind: # Only flag if not already flagged
             debt_kind = "archived_emitter"
             reason = "archived emitter polluting universe scan"
             suggestion = "ignore via config exclusions or tag archived=true"

        if debt_kind:
            debt_items.append({
                "kind": debt_kind,
                "category": category, # Added category
                "name": name,
                "locations": producer_locs,
                "reason": reason,
                "suggested_fix": suggestion
            })

    # The function now returns the report dictionary instead of writing to a file
    return {
        "report_type": "event_debt",
        "generated_at": datetime.now(timezone.utc).isoformat(), # Use timezone.utc for consistency
        "debt_items": debt_items,
        "summary": {
            "total_debt": len(debt_items),
            "unknown_names": len([d for d in debt_items if d["category"] == "Unknown / Dynamic"]),
            "placeholders": len([d for d in debt_items if d["category"] == "Placeholder"]),
            "lane_mismatches": len([d for d in debt_items if d["category"] == "Lane Mismatch"]),
            "archived": len([d for d in debt_items if d["category"] == "Archived / Fossil"]),
             "uri_style": len([d for d in debt_items if d["category"] == "URI-ish"]),
        }
    }

def generate_gap_analysis(registry_path: Path, logs_path: Path) -> Dict[str, Any]:
    """
    Compare Static Scan (Registry) vs Dynamic Logs (NDJSON).
    Returns Zombies (Stale) and Rogues (Emergent).
    """
    # Ensure registry_path exists before proceeding
    if not registry_path.exists():
        return {
            "report_type": "gap_analysis",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "defined_count": 0,
                "observed_count": 0,
                "latent_count": 0,
                "emergent_count": 0
            },
            "latent_events": [],
            "emergent_events": [],
            "error": f"Registry not found: {registry_path}"
        }

    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)
    except Exception as e:
        return {
            "report_type": "gap_analysis",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "defined_count": 0,
                "observed_count": 0,
                "latent_count": 0,
                "emergent_count": 0
            },
            "latent_events": [],
            "emergent_events": [],
            "error": f"Failed to load registry: {e}"
        }
    
    # 1. Get Set of Defined Events
    defined_events = {} # Name -> Event Details (dict)
    for item in registry.get('events', []):
        name = item.get('name') 
        if name:
            defined_events[name] = item

    # 2. Get Set of Observed Events from Logs
    observed_events = set()
    observed_details = {} # name -> {count, sources, last_seen}
    
    if logs_path and logs_path.exists():
        with open(logs_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    record = json.loads(line)
                    evt_type = record.get('event_type')
                    if evt_type:
                        observed_events.add(evt_type)
                        
                        if evt_type not in observed_details:
                            observed_details[evt_type] = {"count": 0, "sources": set(), "last_seen": ""}
                        
                        observed_details[evt_type]["count"] += 1
                        observed_details[evt_type]["sources"].add(record.get('source', 'unknown'))
                        # Use timezone.utc for consistency
                        observed_details[evt_type]["last_seen"] = record.get('timestamp') or record.get('_logged_at')
                except json.JSONDecodeError: # Catch specific JSON error
                    # print(f"Skipping malformed JSON line: {line.strip()}") # For debugging
                    continue
                except Exception: # Catch other potential errors during record processing
                    # print(f"Skipping line due to unexpected error: {line.strip()}") # For debugging
                    continue
    else:
        # If logs_path doesn't exist, observed_events will be empty, which is fine.
        # We might want to add a warning or error to the report if logs are expected.
        pass

    # 3. Analyze Gap
    # Using keys for set operations
    defined_names = set(defined_events.keys())
    
    zombies = defined_names - observed_events
    rogues = observed_events - defined_names
    
    # Format Items
    zombie_items = []
    for z in zombies:
        details = defined_events.get(z, {})
        producers = details.get("producers", [])
        
        # Flatten locations
        locations = []
        for p in producers:
            loc = p.get("location")
            if loc: locations.append(loc)
            
        zombie_items.append({
            "event": z,
            "status": "Latent",
            "reason": "Defined in code but never observed on Bus.",
            "locations": locations # Added context
        })
        
    rogue_items = []
    for r in rogues:
        details = observed_details.get(r, {})
        rogue_items.append({
            "event": r,
            "status": "Emergent", # Rebranding "Rogue" to "Emergent"
            "count": details.get("count", 0),
            "sources": sorted(list(details.get("sources", []))), # Sort sources for consistent output
            "last_seen": details.get("last_seen"),
            "reason": "Observed on Bus but not in Static Registry."
        })

    return {
        "report_type": "gap_analysis",
        "generated_at": datetime.now(timezone.utc).isoformat(), # Use timezone.utc for consistency
        "summary": {
            "defined_count": len(defined_events),
            "observed_count": len(observed_events),
            "latent_count": len(zombies),
            "emergent_count": len(rogues)
        },
        "latent_events": sorted(zombie_items, key=lambda x: x['event']),
        "emergent_events": sorted(rogue_items, key=lambda x: x['event'])
    }

def run_debt_report(output_path: str = "artifacts/omni/event_debt.yaml"):
    # Default registry location
    reg_path = Path("artifacts/omni/EVENT_REGISTRY.yaml") 
    # Or should it be the contract one? The user said "You already have EVENT_REGISTRY.yaml generation"
    # and in step 3: "filter it into a debt list".
    # But wait, previous step saved to c:/Users/kryst/Infrastructure/contracts/events/EVENT_REGISTRY.yaml
    # We should probably check both or make it an argument.
    
    # Check contracts/events first
    contracts_reg = Path("contracts/events/EVENT_REGISTRY.yaml") # Relative to tools root? No.
    # The scan runs from tools/omni usually.
    
    # Hardcoded fallback for now based on where we just wrote it
    # But let's look for arg input
    pass
