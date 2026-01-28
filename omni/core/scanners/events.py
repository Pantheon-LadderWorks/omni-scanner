import os
import re
from pathlib import Path
from typing import Dict, Any, List
from omni.core import config

def scan(target: Path) -> Dict[str, Any]:
    """
    Scans the target directory for event emission patterns.
    Returns structured findings.
    """
    conf = config.load_config(target if target.is_dir() else target.parent)
    scan_conf = conf.get("scan", {})
    
    excludes = scan_conf.get("exclude", [])
    patterns = scan_conf.get("patterns", {}).get("generic_events", [])
    
    findings = []
    
    # If target is a file, scan it directly
    if target.is_file():
        findings.extend(_scan_file(target, patterns))
    else:
        # Walk directory
        for root, dirs, files in os.walk(target):
            # Apply Excludes to dirs to prune walk
            # Simple check: name in exclude list
            dirs[:] = [d for d in dirs if d not in excludes and not any(ex in os.path.join(root, d).replace("\\", "/") for ex in excludes)]
            
            for file in files:
                file_path = Path(root) / file
                # Apply Excludes to files
                if any(ex in str(file_path).replace("\\", "/") for ex in excludes):
                    continue
                    
                # Check extensions (implicitly via include logic or simple check)
                if not file_path.suffix in ['.py', '.js', '.ts', '.go', '.rs', '.java']:
                    # Use includes from config? For now simple extension whitelist + config
                    continue

                findings.extend(_scan_file(file_path, patterns))

    return {
        "count": len(findings),
        "items": findings
    }

def _scan_file(file_path: Path, patterns: List[str]) -> List[Dict[str, Any]]:
    results = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                lineno = content[:match.start()].count('\n') + 1
                line_content = content[match.start():content.find('\n', match.start())].strip()
                
                # Extraction Logic
                event_guess = "unknown"
                confidence = 0.5
                
                # 1. Crown URLs (Highest confidence)
                if "crown://" in match.group(0) or "crown://" in line_content:
                    crown_match = re.search(r'(crown://[\w/._-]+)', line_content)
                    if crown_match:
                        event_guess = crown_match.group(1)
                        confidence = 0.95
                
                # 2. String Literals (High confidence)
                elif strings := re.findall(r'["\']([a-zA-Z0-9_.:-]+)["\']', line_content):
                    # STRICT regex: only allow alphanum, dot, colon, dash. No spaces, no brackets.
                    best_string = strings[0] 
                    if len(best_string) > 3:
                         event_guess = best_string
                         confidence = 0.85
                
                # 3. Variable fallback (Low confidence)
                else:
                    event_guess = f"dynamic:{line_content[:30]}..." # Tag as dynamic
                    confidence = 0.5 # Bumped from 0.3 but marked as dynamic

                # VALIDATION GATE
                # Reject if "unknown" unless it's explicitly dynamic
                if event_guess == "unknown" and confidence < 0.5:
                     continue
                
                # Check for "scanner reflection" (regex strings)
                if "\\w" in event_guess or "group(" in event_guess or "[" in event_guess:
                     continue

                # Metadata Guesses
                transport = _guess_transport(line_content, pattern)
                lane = _guess_lane(event_guess, transport)

                results.append({
                    "surface_id": f"{file_path.name}:{lineno}",
                    "file": str(file_path),
                    "line": lineno,
                    "pattern": pattern,
                    "match": line_content,
                    "event_guess": event_guess,
                    "lane": lane,
                    "transport": transport,
                    "confidence": confidence,
                    "project": file_path.parent.name
                })
    except Exception:
        pass
        
    return results

def _guess_transport(line: str, pattern: str) -> str:
    line = line.lower()
    if "ws." in line or "websocket" in line or "socket" in line:
        return "websocket"
    if "http" in line or "post" in line or "fetch" in line or "axios" in line:
        return "http"
    if "redis" in line:
        return "redis"
    # Default assumptions based on common patterns
    if "publish" in line or "emit" in line:
        return "inproc.publish"
    return "unknown"

def _guess_lane(event_name: str, transport: str) -> str:
    if event_name.startswith("crown://"):
        return "crown"
    if event_name.startswith("core.") or event_name.startswith("agent.") or event_name.startswith("system."):
        return "federation"
    if transport == "websocket" or transport == "http":
        return "network"
    # Default to federation if it looks structured, else local
    if "." in event_name and " " not in event_name:
        return "federation"
    return "local"
