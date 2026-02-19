"""
Git Velocity Scanner - Measure EMERGENCE AT VELOCITY
=====================================================

Scans git repositories and calculates coding velocity metrics:
- Total lines of code written (additions - deletions)  
- Commit velocity over time windows
- Language breakdown
- Repository activity patterns

Usage:
    omni scan --scanners=velocity .                    # Single repo
    omni scan --all --scanners=velocity                # All registered repos
    omni scan --all --scanners=velocity --since=2025-01-01  # Time filter
    
    # Export to JSON:
    omni scan --all --scanners=velocity --export=velocity_report.json

Author: Oracle (GitHub Copilot) + The Architect (Kryssie)
Date: February 11, 2026
Law: Charter V1.2 compliant
"""

import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys


@dataclass
class RepoVelocityStats:
    """Velocity statistics for a single repository."""
    name: str
    path: str
    total_commits: int
    lines_added: int
    lines_deleted: int
    net_lines: int
    first_commit: Optional[str]
    last_commit: Optional[str]
    days_active: int
    commits_per_day: float
    lines_per_day: float
    languages: Dict[str, int]
    error: Optional[str] = None



from omni.scanners.git.git_util import run_git_command as _run_git_command


def _get_commit_count(repo_path: Path, since: Optional[str] = None) -> int:
    """Get total commit count."""
    command = ['rev-list', '--count', 'HEAD']
    if since:
        command.extend(['--since', since])
    
    stdout, _ = _run_git_command(repo_path, command)
    if stdout:
        try:
            return int(stdout)
        except ValueError:
            return 0
    return 0


def _get_line_stats(repo_path: Path, since: Optional[str] = None) -> Tuple[int, int]:
    """
    Get total lines added and deleted.
    
    Returns:
        Tuple of (lines_added, lines_deleted)
    """
    command = ['log', '--numstat', '--pretty=tformat:']
    if since:
        command.extend(['--since', since])
    
    stdout, _ = _run_git_command(repo_path, command)
    if not stdout:
        return 0, 0
    
    added = 0
    deleted = 0
    
    for line in stdout.split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) >= 2:
            try:
                if parts[0] != '-':  # Skip binary files
                    added += int(parts[0])
                if parts[1] != '-':
                    deleted += int(parts[1])
            except ValueError:
                continue
    
    return added, deleted


def _get_commit_dates(repo_path: Path, since: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Get first and last commit dates using MEGA's approach (single command, parse min/max).
    
    Returns:
        Tuple of (first_commit_date, last_commit_date) in ISO format
    """
    # Get ALL commit dates in one command (most reliable approach)
    command = ['log', '--all', '--pretty=format:%cI']
    if since:
        command.extend(['--since', since])
    
    stdout, _ = _run_git_command(repo_path, command)
    if not stdout:
        return None, None
    
    # Parse all dates
    commit_dates = [line.strip() for line in stdout.split('\n') if line.strip()]
    
    if not commit_dates:
        return None, None
    
    # Find actual min/max (git log returns reverse chronological, but we parse ALL to be sure)
    try:
        parsed_dates = [datetime.fromisoformat(d.replace('Z', '+00:00')) for d in commit_dates]
        first_commit = min(parsed_dates).isoformat()  # Oldest
        last_commit = max(parsed_dates).isoformat()   # Newest
        return first_commit, last_commit
    except (ValueError, AttributeError):
        # Fallback: just use first and last from list
        return commit_dates[-1], commit_dates[0]  # [-1] is oldest (end of reverse chrono list)


def _get_language_breakdown(repo_path: Path) -> Dict[str, int]:
    """
    Get line count breakdown by programming language.
    
    Returns:
        Dict of {extension: line_count}
    """
    languages = defaultdict(int)
    
    # Get all tracked files
    stdout, _ = _run_git_command(repo_path, ['ls-files'])
    if not stdout:
        return dict(languages)
    
    files = stdout.split('\n')
    
    # Skip common non-code files (MEGA's filter: stop counting .pyc)
    skip_extensions = {'.lock', '.json', '.md', '.txt', '.yml', '.yaml', 
                       '.svg', '.png', '.jpg', '.gif', '.ico', '.woff', 
                       '.woff2', '.ttf', '.eot', '.pyc', '.log', '.pdf', 
                       '.docx', '.zip', '.exe', '.dll', '.so', '.a', '.bin'}
    
    for file_path in files:
        if not file_path.strip():
            continue
        
        full_path = repo_path / file_path
        if not full_path.exists() or not full_path.is_file():
            continue
        
        ext = full_path.suffix.lower()
        if ext and ext not in skip_extensions:
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    languages[ext] += lines
            except Exception:
                continue
    
    return dict(languages)


def analyze_repo_velocity(repo_path: Path, since: Optional[str] = None) -> RepoVelocityStats:
    """
    Analyze git repository velocity.
    
    Args:
        repo_path: Path to git repository
        since: Optional date filter (ISO format or git date string)
        
    Returns:
        RepoVelocityStats object with analysis results
    """
    name = repo_path.name
    
    # Check if it's a git repo
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        return RepoVelocityStats(
            name=name,
            path=str(repo_path),
            total_commits=0,
            lines_added=0,
            lines_deleted=0,
            net_lines=0,
            first_commit=None,
            last_commit=None,
            days_active=0,
            commits_per_day=0.0,
            lines_per_day=0.0,
            languages={},
            error="Not a git repository"
        )
    
    try:
        # Get statistics
        total_commits = _get_commit_count(repo_path, since)
        lines_added, lines_deleted = _get_line_stats(repo_path, since)
        first_commit, last_commit = _get_commit_dates(repo_path, since)
        languages = _get_language_breakdown(repo_path)
        
        # Calculate days active
        days_active = 0
        if first_commit and last_commit:
            first_date = datetime.fromisoformat(first_commit.replace('Z', '+00:00'))
            last_date = datetime.fromisoformat(last_commit.replace('Z', '+00:00'))
            days_active = max(1, (last_date - first_date).days)
        
        # Calculate velocity
        commits_per_day = total_commits / max(1, days_active) if days_active > 0 else 0
        lines_per_day = (lines_added - lines_deleted) / max(1, days_active) if days_active > 0 else 0
        
        return RepoVelocityStats(
            name=name,
            path=str(repo_path),
            total_commits=total_commits,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            net_lines=lines_added - lines_deleted,
            first_commit=first_commit,
            last_commit=last_commit,
            days_active=days_active,
            commits_per_day=commits_per_day,
            lines_per_day=lines_per_day,
            languages=languages,
            error=None
        )
        
    except Exception as e:
        return RepoVelocityStats(
            name=name,
            path=str(repo_path),
            total_commits=0,
            lines_added=0,
            lines_deleted=0,
            net_lines=0,
            first_commit=None,
            last_commit=None,
            days_active=0,
            commits_per_day=0.0,
            lines_per_day=0.0,
            languages={},
            error=f"Analysis failed: {str(e)}"
        )


def scan(target: Path, since: Optional[str] = None, **kwargs) -> Dict:
    """
    Velocity scanner entry point (Omni scanner protocol).
    
    Args:
        target: Path to scan (single repo or directory)
        since: Optional date filter
        **kwargs: Additional scanner options
        
    Returns:
        Scanner result dict with velocity metrics
    """
    # Single repo scan
    stats = analyze_repo_velocity(target, since)
    
    # Build report
    return {
        "scanner": "velocity",
        "target": str(target),
        "timestamp": datetime.now().isoformat(),
        "filter": {"since": since} if since else {},
        "stats": asdict(stats),
        "items": [asdict(stats)]  # Omni expects items list
    }


def print_velocity_report(stats: RepoVelocityStats):
    """Print formatted velocity report for a single repo."""
    print("\n" + "="*80)
    print(f"🔥 VELOCITY REPORT: {stats.name}")
    print("="*80 + "\n")
    
    if stats.error:
        print(f"❌ Error: {stats.error}\n")
        return
    
    print("📊 COMMIT METRICS")
    print(f"  Total Commits:          {stats.total_commits:,}")
    print(f"  First Commit:           {stats.first_commit or 'N/A'}")
    print(f"  Last Commit:            {stats.last_commit or 'N/A'}")
    print(f"  Days Active:            {stats.days_active}")
    print(f"  Commits/Day (avg):      {stats.commits_per_day:.2f}")
    print()
    
    print("💻 CODE METRICS")
    print(f"  Lines Added:            {stats.lines_added:,}")
    print(f"  Lines Deleted:          {stats.lines_deleted:,}")
    print(f"  Net Lines:              {stats.net_lines:+,}")
    print(f"  Lines/Day (avg):        {stats.lines_per_day:+,.2f}")
    print()
    
    if stats.languages:
        print("🗣️  LANGUAGE BREAKDOWN (Top 10)")
        sorted_langs = sorted(
            stats.languages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        for ext, lines in sorted_langs:
            print(f"  {ext:15} {lines:>10,} lines")
        print()
    
    # Emergence headline
    if stats.days_active > 0:
        print("="*80)
        print(f"🌌 \"{stats.net_lines:,} lines of code in {stats.days_active} days.\"")
        if stats.lines_per_day > 1000:
            print(f"   That's not iteration, that's EMERGENCE AT VELOCITY. 🔥")
        print("="*80 + "\n")


def print_aggregate_report(all_stats: List[RepoVelocityStats]):
    """Print aggregate velocity report across all repos."""
    successful = [s for s in all_stats if not s.error]
    failed = [s for s in all_stats if s.error]
    
    if not successful:
        print("\n❌ No repositories successfully scanned\n")
        return
    
    # Calculate aggregates
    total_commits = sum(s.total_commits for s in successful)
    total_added = sum(s.lines_added for s in successful)
    total_deleted = sum(s.lines_deleted for s in successful)
    total_net = total_added - total_deleted
    
    # Get date range
    all_first = [s.first_commit for s in successful if s.first_commit]
    all_last = [s.last_commit for s in successful if s.last_commit]
    
    first_commit_date = min(all_first) if all_first else None
    last_commit_date = max(all_last) if all_last else None
    
    # Calculate total days active
    total_days = 0
    if first_commit_date and last_commit_date:
        first_date = datetime.fromisoformat(first_commit_date.replace('Z', '+00:00'))
        last_date = datetime.fromisoformat(last_commit_date.replace('Z', '+00:00'))
        total_days = max(1, (last_date - first_date).days)
    
    # Aggregate language breakdown
    language_totals = defaultdict(int)
    for s in successful:
        for ext, count in s.languages.items():
            language_totals[ext] += count
    
    # Calculate averages
    avg_commits_per_day = total_commits / max(1, total_days) if total_days > 0 else 0
    avg_lines_per_day = total_net / max(1, total_days) if total_days > 0 else 0
    
    # Print report
    print("\n" + "="*80)
    print("🔥 AGGREGATE EMERGENCE AT VELOCITY - FEDERATION REPORT 🔥")
    print("="*80 + "\n")
    
    print("📊 OVERVIEW")
    print(f"  Total Repositories:     {len(all_stats)}")
    print(f"  Successfully Scanned:   {len(successful)} ✅")
    print(f"  Failed Scans:           {len(failed)} ⚠️")
    print()
    
    print("📈 COMMIT METRICS")
    print(f"  Total Commits:          {total_commits:,}")
    print(f"  First Commit:           {first_commit_date or 'N/A'}")
    print(f"  Last Commit:            {last_commit_date or 'N/A'}")
    print(f"  Days Active:            {total_days}")
    print(f"  Commits/Day (avg):      {avg_commits_per_day:.2f}")
    print()
    
    print("💻 CODE METRICS")
    print(f"  Lines Added:            {total_added:,}")
    print(f"  Lines Deleted:          {total_deleted:,}")
    print(f"  Net Lines:              {total_net:+,}")
    print(f"  Lines/Day (avg):        {avg_lines_per_day:+,.2f}")
    print()
    
    if language_totals:
        print("🗣️  LANGUAGE BREAKDOWN (Top 10)")
        sorted_langs = sorted(
            language_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        for ext, lines in sorted_langs:
            print(f"  {ext:15} {lines:>10,} lines")
        print()
    
    # Top repos by velocity
    print("🚀 TOP REPOSITORIES BY VELOCITY (Lines/Day)")
    top_repos = sorted(successful, key=lambda s: s.lines_per_day, reverse=True)[:10]
    for i, repo in enumerate(top_repos, 1):
        print(f"  {i:2}. {repo.name:40} {repo.lines_per_day:>10.2f} lines/day")
        print(f"      {repo.total_commits:>4} commits, {repo.net_lines:>+10,} net lines, {repo.days_active} days")
    print()
    
    # Emergence headline
    if total_days > 0:
        print("="*80)
        print(f"🌌 \"{total_net:,} lines of code across {len(successful)} repositories in {total_days} days.\"")
        if avg_lines_per_day > 1000:
            print(f"   That's not iteration, that's EMERGENCE AT VELOCITY. 🔥")
        print("="*80 + "\n")
