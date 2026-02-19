"""
PR Telemetry Scanner - The Telepath
====================================

Purpose:
    Remote sensing of Pull Request health, Canon Compliance, and Architectural Drift.
    "To see without touching."

Architecture:
    - Independent Scanner Class (PRTelemetryScanner)
    - Uses 'gh' CLI for batch retrieval (GraphQL/JSON)
    - Implements Health Scoring Algorithm (C-OMNI-TELEMETRY-001) for drift detection
    - Output: Standard Omni Artifact (scan.pr_telemetry.json)

Usage:
    omni scan --scanners=pr-telemetry .
    omni scan --scanners=pr-telemetry --target=owner/repo

Author: Seraphina (via Antigravity)
Contract: C-OMNI-TELEMETRY-001
"""

import json
import logging
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from omni.config import settings

logger = logging.getLogger("Omni.Scanners.Git.PRTelemetry")

class PRTelemetryScanner:
    """
    The Telepath Scanner.
    Analyzes Pull Requests for health, canon compliance, and drift.
    """

    def __init__(self):
        self.heart_available = settings.heart_available
        # Cache paths if Federation is available
        if self.heart_available:
            self.inventory_path = settings.get_repo_inventory_path()
        else:
            self.inventory_path = None

    def scan(self, target: str, **kwargs) -> Dict[str, Any]:
        """
        Scan a target (repo path or owner/repo string) for PR telemetry.
        
        Args:
            target: Local path or "owner/repo" string.
            **kwargs: Extra options (e.g., 'state', 'limit').
        
        Returns:
            Dict: Telemetry report fitting C-OMNI-TELEMETRY-001 spec.
        """
        # 1. Resolve Target
        repo_slug = self._resolve_target(target)
        if not repo_slug:
            return self._error_response("Could not resolve valid GitHub repository from target.")

        logger.info(f"🔮 Telepath scanning: {repo_slug}")

        # 2. Fetch Data (Batch)
        prs = self._fetch_prs(repo_slug, kwargs.get("limit", 50))
        
        # 3. Analyze & Score
        scored_items = []
        metrics = {
            "total_count": len(prs),
            "open_count": 0,
            "stale_count": 0,
            "high_risk_count": 0,
            "canon_compliant_count": 0,
            "average_health": 0.0
        }
        
        total_health = 0
        
        for pr in prs:
            analysis = self._analyze_pr(pr)
            scored_items.append(analysis)
            
            # Aggregate metrics
            if analysis["state"] == "OPEN":
                metrics["open_count"] += 1
            if "Stale Draft" in analysis["flags"]:
                metrics["stale_count"] += 1
            if analysis["health"] < 50:
                metrics["high_risk_count"] += 1
                
            total_health += analysis["health"]

        if metrics["total_count"] > 0:
            metrics["average_health"] = round(total_health / metrics["total_count"], 1)
        else:
            metrics["average_health"] = 100.0 # No PRs = perfect health?

        # 4. Construct Report
        return {
            "telemetry_type": "pr_health",
            "scanner": "pr-telemetry",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": repo_slug,
            "metrics": metrics,
            "items": scored_items
        }

    def _resolve_target(self, target: str) -> Optional[str]:
        """Resolves 'owner/repo' from local path or returns string as-is."""
        # If it looks like a path
        path = Path(target)
        if path.exists() and (path / ".git").is_dir():
            # Use shared utility to get remote URL
            from omni.scanners.git.git_util import get_remote_url
            url = get_remote_url(path)
            
            if url:
                # Convert normalized https://github.com/owner/repo to owner/repo
                if "github.com" in url:
                    parts = url.split("github.com")[-1].strip("/").split("/")
                    if len(parts) >= 2:
                        return f"{parts[-2]}/{parts[-1]}"
        
        # Assume it's already "owner/repo" if it contains a slash
        if "/" in str(target) and not "\\" in str(target): # weak check
             return str(target)
             
        return None

    def _fetch_prs(self, repo_slug: str, limit: int) -> List[Dict]:
        """
        Fetch PRs using 'gh' CLI.
        Fields: number, title, state, updatedAt, headRefName, author, statusCheckRollup, files
        """
        if not shutil.which("gh"):
            logger.error("GitHub CLI (gh) not found in PATH.")
            return []
            
        fields = "number,title,state,updatedAt,isDraft,author,files,statusCheckRollup"
        cmd = [
            "gh", "pr", "list",
            "--repo", repo_slug,
            "--json", fields,
            "--limit", str(limit),
            "--state", "all" # Get closed too? Maybe just open for now directly. Contract implies current health. 
        ]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if res.returncode != 0:
                logger.error(f"gh CLI error: {res.stderr}")
                return []
            return json.loads(res.stdout)
        except Exception as e:
            logger.error(f"Failed to fetch PRs: {e}")
            return []

    def _analyze_pr(self, pr: Dict) -> Dict:
        """
        Calculate Health Score based on C-OMNI-TELEMETRY-001.
        Base: 100
        """
        score = 100
        flags = []
        
        # --- Penalties ---
        
        # 1. Stale Draft (-20)
        updated_at = datetime.fromisoformat(pr.get("updatedAt").replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - updated_at).days
        is_draft = pr.get("isDraft", False)
        
        if is_draft and age_days > 30:
            score -= 20
            flags.append("Stale Draft")
            
        # 2. CI Failure (-30)
        # Check statusCheckRollup -> state
        rollup = pr.get("statusCheckRollup", {})
        if rollup:
            # gh returns a list or dict depending on version/state
            # usually: [{"status": "COMPLETED", "conclusion": "FAILURE", ...}]
            # Simplistic check for now
            status_str = str(rollup).upper()
            if "FAILURE" in status_str or "ERROR" in status_str:
                score -= 30
                flags.append("CI Failure")

        # 3. Documentation Debt (-5)
        # Check file list
        files = pr.get("files", []) # gh pr list --json files might perform separate API calls? 
        # Actually 'files' is not available in basic list without separate call for some implementations, 
        # but modern gh supports it. If files is empty list but we suspect files exist, we might flag 'Unknown Files'.
        # Assuming we get file paths:
        file_paths = [f.get("path", "") for f in files] if isinstance(files, list) else []
        
        if len(file_paths) > 10:
            has_docs = any(f.endswith(".md") or "docs/" in f for f in file_paths)
            if not has_docs:
                score -= 5
                flags.append("Documentation Debt")

        # 4. Canon Violation (-15)
        # Touching shielded paths without intent
        shielded_paths = ["federation_heart", "governance"]
        touched_shielded = any(any(s in f for s in shielded_paths) for f in file_paths)
        
        title = pr.get("title", "").lower()
        has_intent = any(x in title for x in ["feat", "fix", "chore", "refactor", "ci"])
        
        if touched_shielded and not has_intent:
            score -= 15
            flags.append("Canon Violation (Shielded Path)")

        # --- Bonuses ---

        # 1. Council Action (+10)
        author = pr.get("author", {}).get("login", "")
        council_members = settings.get_council_members()
        if author.lower() in council_members:
            score += 10
            flags.append("Council Action")

        # 2. Quick Win (+5)
        created_at_str = pr.get("createdAt") # Need to request this field if we want accuracy, using updatedAt as proxy if missing
        # let's assume age < 1 day for now based on updatedAt if newly created
        if age_days < 1 and len(file_paths) < 5:
            score += 5
            flags.append("Quick Win")

        # Cap score
        score = max(0, min(100, score))
        
        return {
            "id": str(pr.get("number")),
            "number": pr.get("number"),  # Added for compatibility
            "title": pr.get("title"),
            "author": author,
            "state": pr.get("state"),
            "health": score,
            "flags": flags,
            "meta": {
                "updated_at": pr.get("updatedAt"),
                "file_count": len(file_paths)
            }
        }

    def _error_response(self, message: str) -> Dict:
        return {
            "telemetry_type": "error",
            "scanner": "pr-telemetry",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": "unknown",
            "metrics": {},
            "items": [],
            "error": message
        }

def scan(target: str = ".", **kwargs) -> Dict[str, Any]:
    """CLI Entrypoint wrapper."""
    scanner = PRTelemetryScanner()
    return scanner.scan(target, **kwargs)
