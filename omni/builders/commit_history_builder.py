"""
omni/core/commit_history_builder.py
Commit History Registry Builder
================================
Generates commit history registries for all Federation repositories.
Each repository gets its own JSON file: {repo_name}_commit_history.json

Phoenix Resurrection Evidence:
- Complete commit logs with author, date, message, file stats
- Preserves multi-machine history (Forge Desktop → Current)
- Enables temporal archaeology and lineage tracking

Sources:
1. GitHub Inventory (repo_inventory.json) - which repos exist
2. Local git clones - commit history extraction
3. Federation Heart path resolution - NO HARDCODED PATHS

Output:
- governance/registry/commits/{repo_name}_commit_history.json (per repo)

Uses federation_heart CartographyPillar for path resolution.

Author: Oracle (GitHub Copilot) + The Architect (Kryssie)
Date: February 12, 2026
Law: Charter V1.2 compliant - Federation pattern only
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Federation Heart Integration (pip installed as seraphina-federation)
try:
    from federation_heart.pillars.cartography import CartographyPillar
    HEART_AVAILABLE = True
except ImportError as e:
    HEART_AVAILABLE = False
    _import_error = str(e)

logger = logging.getLogger("Omni.Core.CommitHistoryBuilder")


@dataclass
class CommitRecord:
    """Single commit record."""
    hash: str
    author: str
    date: str
    message: str
    files_changed: int
    insertions: int
    deletions: int


@dataclass
class RepositoryInfo:
    """Repository metadata."""
    name: str
    path: str
    github_url: Optional[str]
    scanned_at: str


@dataclass
class CommitStats:
    """Aggregate statistics."""
    total_commits: int
    first_commit: Optional[str]
    last_commit: Optional[str]
    days_active: int
    total_authors: int
    authors: List[str]
    total_insertions: int
    total_deletions: int
    net_lines: int


@dataclass
class CommitHistoryRegistry:
    """Complete commit history for one repository."""
    repository: RepositoryInfo
    commits: List[CommitRecord]
    stats: CommitStats
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository": asdict(self.repository),
            "commits": [asdict(c) for c in self.commits],
            "stats": asdict(self.stats)
        }


class CommitHistoryBuilder:
    """
    Builds commit history registries for Federation repositories.
    Uses federation_heart for path resolution - NO HARDCODED PATHS.
    """
    
    def __init__(self, infra_root: Path = None):
        if not HEART_AVAILABLE:
            # Fallback mode for standalone operation
            logger.warning(f"⚠️ Federation Heart not available: {_import_error}")
            logger.warning("   Running in standalone mode with fallback paths")
            self._cartography = None
            self.infra_root = infra_root or Path(r"C:\Users\kryst\Infrastructure")
        else:
            # Federation mode (preferred)
            self._cartography = CartographyPillar(infra_root)
            self.infra_root = self._cartography.get_infrastructure_root()
        
        logger.info(f"📜 CommitHistoryBuilder initialized")
        logger.info(f"   - Infrastructure: {self.infra_root}")
        logger.info(f"   - Heart Available: {HEART_AVAILABLE}")
    
    def _get_governance_path(self, subpath: str = "") -> Path:
        """Get governance path using Heart or fallback."""
        if self._cartography:
            gov = self._cartography.resolve_path("governance")
            return gov / subpath if subpath else gov
        else:
            # Fallback
            gov = self.infra_root / "governance"
            return gov / subpath if subpath else gov
    
    def _get_commits_registry_path(self, repo_name: str) -> Path:
        """Get path to commit history file for a repository."""
        commits_dir = self._get_governance_path("registry/commits")
        commits_dir.mkdir(parents=True, exist_ok=True)
        return commits_dir / f"{repo_name}_commit_history.json"
    
    def _load_repo_inventory(self) -> List[Dict]:
        """Load GitHub repository inventory."""
        inventory_path = self._get_governance_path("registry/git_repos/repo_inventory.json")
        
        if not inventory_path.exists():
            logger.warning(f"Repo inventory not found: {inventory_path}")
            return []
        
        try:
            with open(inventory_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('repos', [])
        except Exception as e:
            logger.error(f"Failed to load repo inventory: {e}")
            return []
    
    def _run_git_command(self, repo_path: Path, command: List[str]) -> tuple[Optional[str], Optional[str]]:
        """Run a git command in the repository with robust UTF-8 handling."""
        import subprocess
        
        try:
            # Windows cp1252 workaround: capture as bytes, decode manually
            result = subprocess.run(
                ['git'] + command,
                cwd=repo_path,
                capture_output=True,
                timeout=60,
                # Don't use text=True or encoding - handle manually
            )
            if result.returncode == 0:
                # Manually decode with UTF-8 and replace errors
                stdout = result.stdout.decode('utf-8', errors='replace')
                return stdout, None
            else:
                stderr = result.stderr.decode('utf-8', errors='replace').strip()
                return None, stderr
        except subprocess.TimeoutExpired:
            return None, "Command timeout"
        except Exception as e:
            return None, str(e)
    
    def _parse_commit_log(self, log_output: str) -> List[CommitRecord]:
        """
        Parse git log output into commit records.
        
        Format: COMMIT_START, hash|author|date, MSG_START, full message, MSG_END, numstat lines
        """
        commits = []
        current_commit = None
        in_message = False
        message_lines = []
        
        lines = log_output.split('\n')
        
        for line in lines:
            # Start of new commit
            if line == 'COMMIT_START':
                # Save previous commit
                if current_commit:
                    # Clean up message
                    current_commit.message = '\n'.join(message_lines).strip()
                    commits.append(current_commit)
                    message_lines = []
                
                current_commit = None
                in_message = False
                continue
            
            # Commit header: hash|author|date
            if current_commit is None and '|' in line and not line.startswith('\t'):
                parts = line.split('|', 2)
                if len(parts) == 3:
                    hash_val, author, date = parts
                    current_commit = CommitRecord(
                        hash=hash_val.strip(),
                        author=author.strip(),
                        date=date.strip(),
                        message='',  # Will be filled in later
                        files_changed=0,
                        insertions=0,
                        deletions=0
                    )
                continue
            
            # Message start
            if line == 'MSG_START':
                in_message = True
                message_lines = []
                continue
            
            # Message end
            if line == 'MSG_END':
                in_message = False
                continue
            
            # Message content
            if in_message:
                message_lines.append(line)
                continue
            
            # File stat: insertions\tdeletions\tfilename
            if '\t' in line and current_commit and not in_message:
                parts = line.split('\t')
                if len(parts) >= 3:
                    try:
                        ins = parts[0].strip()
                        dels = parts[1].strip()
                        
                        insertions = int(ins) if ins and ins != '-' else 0
                        deletions = int(dels) if dels and dels != '-' else 0
                        
                        current_commit.files_changed += 1
                        current_commit.insertions += insertions
                        current_commit.deletions += deletions
                    except ValueError:
                        # Binary files show as "-"
                        current_commit.files_changed += 1
        
        # Don't forget the last commit
        if current_commit:
            current_commit.message = '\n'.join(message_lines).strip()
            commits.append(current_commit)
        
        return commits
    
    def _calculate_stats(self, commits: List[CommitRecord]) -> CommitStats:
        """Calculate aggregate statistics from commits."""
        if not commits:
            return CommitStats(
                total_commits=0,
                first_commit=None,
                last_commit=None,
                days_active=0,
                total_authors=0,
                authors=[],
                total_insertions=0,
                total_deletions=0,
                net_lines=0
            )
        
        authors = sorted(set(c.author for c in commits))
        total_ins = sum(c.insertions for c in commits)
        total_dels = sum(c.deletions for c in commits)
        
        # Calculate days active
        if commits[0].date and commits[-1].date:
            try:
                first = datetime.fromisoformat(commits[-1].date.replace('Z', '+00:00'))
                last = datetime.fromisoformat(commits[0].date.replace('Z', '+00:00'))
                days_active = (last - first).days
            except:
                days_active = 0
        else:
            days_active = 0
        
        return CommitStats(
            total_commits=len(commits),
            first_commit=commits[-1].date if commits else None,  # Last in list = oldest
            last_commit=commits[0].date if commits else None,    # First in list = newest
            days_active=days_active,
            total_authors=len(authors),
            authors=authors,
            total_insertions=total_ins,
            total_deletions=total_dels,
            net_lines=total_ins - total_dels
        )
    
    def scan_repository(self, repo_path: Path, repo_name: str, github_url: Optional[str] = None) -> Optional[CommitHistoryRegistry]:
        """
        Scan a single repository's commit history.
        
        Args:
            repo_path: Path to git repository
            repo_name: Repository name
            github_url: Optional GitHub URL
            
        Returns:
            CommitHistoryRegistry or None if error
        """
        repo_path = Path(repo_path).resolve()
        
        # Check if it's a git repository
        if not (repo_path / '.git').exists():
            logger.warning(f"Not a git repository: {repo_path}")
            return None
        
        logger.info(f"📜 Scanning: {repo_name}")
        
        # Get commit log with stats
        # %B = full commit message (subject + body), not just %s (subject only)
        stdout, err = self._run_git_command(
            repo_path,
            ['log', '--all', '--pretty=format:COMMIT_START%n%H|%an|%aI%nMSG_START%n%B%nMSG_END', '--numstat']
        )
        
        if err:
            logger.error(f"   Failed to get git log: {err}")
            return None
        
        if not stdout:
            logger.warning(f"   No commits found")
            return None
        
        # Parse commits
        commits = self._parse_commit_log(stdout)
        
        if not commits:
            logger.warning(f"   Failed to parse commits")
            return None
        
        # Calculate stats
        stats = self._calculate_stats(commits)
        
        logger.info(f"   ✅ {stats.total_commits} commits, {stats.total_authors} authors, {stats.net_lines:+,} net lines")
        
        # Build registry
        return CommitHistoryRegistry(
            repository=RepositoryInfo(
                name=repo_name,
                path=str(repo_path),
                github_url=github_url,
                scanned_at=datetime.now().isoformat()
            ),
            commits=commits,
            stats=stats
        )
    
    def build_single(self, repo_path: Path, repo_name: str = None, github_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Build commit history for a single repository and write to registry.
        
        Args:
            repo_path: Path to repository
            repo_name: Optional repo name (defaults to folder name)
            github_url: Optional GitHub URL
            
        Returns:
            Dict with status, commit_count, registry_file (on success) or error (on failure)
        """
        repo_path = Path(repo_path).resolve()
        
        if repo_name is None:
            repo_name = repo_path.name
        
        # Scan repository
        registry = self.scan_repository(repo_path, repo_name, github_url)
        
        if not registry:
            return {
                'status': 'error',
                'error': 'Failed to scan repository (no commits or parse error)'
            }
        
        # Write to registry
        output_path = self._get_commits_registry_path(repo_name)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(registry.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"   💾 Written: {output_path.relative_to(self.infra_root)}")
            return {
                'status': 'success',
                'commit_count': registry.stats.total_commits,
                'registry_file': str(output_path.relative_to(self.infra_root)),
                'net_lines': registry.stats.net_lines,
                'authors': registry.stats.total_authors
            }
            
        except Exception as e:
            logger.error(f"   Failed to write registry: {e}")
            return {
                'status': 'error',
                'error': f'Failed to write registry: {str(e)}'
            }
    
    def build_all(self, repos: List[Dict] = None) -> Dict[str, bool]:
        """
        Build commit histories for all repositories with local paths.
        
        Args:
            repos: Optional list of repo dicts (from inventory)
                   If None, loads from repo_inventory.json
            
        Returns:
            Dict mapping repo name to success status
        """
        if repos is None:
            repos = self._load_repo_inventory()
        
        if not repos:
            logger.warning("No repositories found")
            return {}
        
        logger.info(f"\n🔥 BUILDING COMMIT HISTORY REGISTRY")
        logger.info(f"   Total repos in inventory: {len(repos)}")
        logger.info("=" * 60)
        
        results = {}
        
        for repo in repos:
            # Only process repos with local paths
            local_path = repo.get('local_path')
            if not local_path:
                continue
            
            if not Path(local_path).exists():
                logger.warning(f"⊘ Local path missing: {repo.get('name')} → {local_path}")
                continue
            
            success = self.build_single(
                Path(local_path),
                repo_name=repo.get('name'),
                github_url=repo.get('url')
            )
            
            results[repo.get('name')] = success
        
        print("\n" + "=" * 60)
        successful = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info(f"✅ Completed: {successful}/{total} successful")
        
        return results
    
    def get_registry_path(self, repo_name: str) -> Path:
        """Get path to commit history registry for a repo."""
        return self._get_commits_registry_path(repo_name)
    
    def load_commit_history(self, repo_name: str) -> Optional[Dict]:
        """Load existing commit history from registry."""
        path = self._get_commits_registry_path(repo_name)
        
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load commit history for {repo_name}: {e}")
            return None
