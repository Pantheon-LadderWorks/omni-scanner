import re
import os
from pathlib import Path
from typing import Dict, Any, List
from omni.core import config

def scan(target: Path) -> Dict[str, Any]:
    """
    Scans for 'Hook Points' - potential places for Bus integration.
    """
    conf = config.load_config(target if target.is_dir() else target.parent)
    scan_conf = conf.get("scan", {})
    excludes = scan_conf.get("exclude", [])
    
    findings = []
    
    if target.is_file():
        findings.extend(_scan_file(target))
    else:
        for root, dirs, files in os.walk(target):
            # Exclude logic (same as other scanners - reuse if possible in future)
            dirs[:] = [d for d in dirs if d not in excludes and not any(ex in os.path.join(root, d).replace("\\", "/") for ex in excludes)]
            
            for file in files:
                file_path = Path(root) / file
                if any(ex in str(file_path).replace("\\", "/") for ex in excludes):
                    continue
                if not file_path.suffix in ['.py', '.js', '.ts', '.go']:
                    continue
                # Exclude Windows duplicate copies e.g. foo(1).py
                if re.search(r'\(\d+\)\.', file_path.name):
                    continue

                findings.extend(_scan_file(file_path))

    return {
        "count": len(findings),
        "items": findings
    }

def _scan_file(file_path: Path) -> List[Dict[str, Any]]:
    results = []
    results_counts = {
        "polling_loop": 0,
        "bus_stub": 0,
        "direct_http_egress": 0,
        "state_persistence": 0
    }
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            lineno = i + 1
            content = line.strip()
            
            # Match Limiter
            # Dict key: kind
            counts = results_counts
            
            # 1. Polling / Loops (Potential Consumer Hooks)
            if counts["polling_loop"] < 2:
                if "while True" in content or "while 1" in content:
                     # Look ahead for sleep
                     snippet = "".join(lines[i:i+5])
                     if "sleep(" in snippet:
                         results.append(_make_item(file_path, lineno, "polling_loop", "Found infinite loop with sleep - suggest Bus Subscription", content))
                         counts["polling_loop"] += 1

            # 2. Stub Language (Design Intent)
            if counts["bus_stub"] < 5:
                if "TODO" in content or "FIXME" in content:
                    if any(k in content.lower() for k in ["event", "bus", "publish", "emit", "subscribe", "message"]):
                         results.append(_make_item(file_path, lineno, "bus_stub", "TODO/FIXME related to Bus detected", content))
                         counts["bus_stub"] += 1

            # 3. Direct Side Effects (Potential Producer Hooks)
            if counts["direct_http_egress"] < 3:
                if "requests." in content or "httpx." in content or "fetch(" in content:
                    if "post" in content.lower() or "put" in content.lower():
                        results.append(_make_item(file_path, lineno, "direct_http_egress", "Direct HTTP output - suggest Bus Bridge", content))
                        counts["direct_http_egress"] += 1
            
            # 4. Data Persistence (State Changes)
            if counts["state_persistence"] < 3:
                if ".commit()" in content or ".save()" in content:
                     results.append(_make_item(file_path, lineno, "state_persistence", "State persistence detected - suggest State Change Event", content))
                     counts["state_persistence"] += 1

    except Exception:
        pass
        
    return results

def _make_item(file: Path, line: int, kind: str, desc: str, match: str):
    return {
        "type": "hook_point",
        "kind": kind, # producer, consumer, bridge, stub
        "description": desc,
        "location": f"{file.name}:{line}",
        "file": str(file),
        "line": line,
        "match": match,
        "project": file.parent.name
    }
