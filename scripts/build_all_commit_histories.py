"""
Build commit histories for all locally cloned repos.

Filters:
- Must have local_paths (repo is cloned)
- Must have github_url
- Not in EXCLUSION_LIST_V1.yaml
"""

import sys
from pathlib import Path

# Add omni to path
omni_root = Path(__file__).parent.parent
sys.path.insert(0, str(omni_root))

import yaml
import json
from omni.core.commit_history_builder import CommitHistoryBuilder


def load_exclusion_list():
    """Load repos to exclude from EXCLUSION_LIST_V1.yaml"""
    exclusion_path = Path(__file__).parent.parent.parent.parent / "governance" / "registry" / "projects" / "EXCLUSION_LIST_V1.yaml"
    
    if not exclusion_path.exists():
        return set()
    
    with open(exclusion_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Extract repo names (case-insensitive)
    excluded = set()
    for item in data.get('exclusions', []):
        repo_name = item.get('repo', '').lower()
        if repo_name:
            excluded.add(repo_name)
    
    return excluded


def load_project_registry():
    """Load PROJECT_REGISTRY_V1.yaml"""
    registry_path = Path(__file__).parent.parent.parent.parent / "governance" / "registry" / "projects" / "PROJECT_REGISTRY_V1.yaml"
    
    with open(registry_path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def extract_repo_name(github_url):
    """Extract repo name from GitHub URL"""
    if not github_url:
        return None
    # https://github.com/Kryssie6985/codecraft -> codecraft
    return github_url.rstrip('/').split('/')[-1]


def build_all_commit_histories():
    """Build commit histories for all applicable repos"""
    
    print("🔍 Loading exclusion list...")
    excluded_repos = load_exclusion_list()
    print(f"   Excluding {len(excluded_repos)} repos: {', '.join(sorted(excluded_repos))}")
    
    print("\n📋 Loading project registry...")
    registry = load_project_registry()
    total_projects = len(registry['projects'])
    print(f"   Total projects in registry: {total_projects}")
    
    # Filter to repos that:
    # 1. Have github_url
    # 2. Have local_paths (actually cloned)
    # 3. Not in exclusion list
    
    eligible_repos = []
    
    for project in registry['projects']:
        github_url = project.get('github_url')
        local_paths = project.get('local_paths', [])
        
        # Skip if no GitHub URL
        if not github_url:
            continue
        
        # Skip if not cloned locally
        if not local_paths:
            continue
        
        # Skip if in exclusion list
        repo_name = extract_repo_name(github_url)
        if repo_name and repo_name.lower() in excluded_repos:
            print(f"   ⏭️  Skipping {repo_name} (in exclusion list)")
            continue
        
        # Use first local path (primary location)
        local_path = local_paths[0]
        
        eligible_repos.append({
            'name': project.get('name'),
            'display_name': project.get('display_name'),
            'github_url': github_url,
            'local_path': local_path,
            'visibility': project.get('visibility', 'PRIVATE')
        })
    
    print(f"\n✅ Found {len(eligible_repos)} eligible repos")
    print(f"   (Filtered from {total_projects} total projects)")
    
    # Initialize builder
    print("\n🔧 Initializing CommitHistoryBuilder...")
    builder = CommitHistoryBuilder()
    
    # Build commit histories
    results = {
        'successful': [],
        'failed': [],
        'skipped': []
    }
    
    print(f"\n🚀 Building commit histories for {len(eligible_repos)} repos...")
    print("=" * 80)
    
    for i, repo in enumerate(eligible_repos, 1):
        repo_name = repo['display_name'] or repo['name']
        local_path = repo['local_path']
        github_url = repo['github_url']
        
        print(f"\n[{i}/{len(eligible_repos)}] {repo_name}")
        print(f"   Path: {local_path}")
        print(f"   GitHub: {github_url}")
        
        # Check if path exists
        path_obj = Path(local_path)
        if not path_obj.exists():
            print(f"   ⚠️  SKIP: Path does not exist")
            results['skipped'].append({
                'repo': repo_name,
                'reason': 'Path not found',
                'path': local_path
            })
            continue
        
        # Check if it's a git repo
        git_dir = path_obj / '.git'
        if not git_dir.exists():
            print(f"   ⚠️  SKIP: Not a git repository (no .git folder)")
            results['skipped'].append({
                'repo': repo_name,
                'reason': 'No .git folder',
                'path': local_path
            })
            continue
        
        # Build commit history
        try:
            result = builder.build_single(local_path, github_url=github_url)
            
            if result.get('status') == 'success':
                commit_count = result.get('commit_count', 0)
                registry_file = result.get('registry_file', '')
                print(f"   ✅ SUCCESS: {commit_count} commits")
                print(f"   📝 Saved to: {registry_file}")
                
                results['successful'].append({
                    'repo': repo_name,
                    'commits': commit_count,
                    'file': registry_file
                })
            else:
                error = result.get('error', 'Unknown error')
                print(f"   ❌ FAILED: {error}")
                results['failed'].append({
                    'repo': repo_name,
                    'error': error
                })
        
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            results['failed'].append({
                'repo': repo_name,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {len(results['successful'])}")
    print(f"❌ Failed:     {len(results['failed'])}")
    print(f"⏭️  Skipped:    {len(results['skipped'])}")
    print(f"📋 Total:      {len(eligible_repos)}")
    
    if results['successful']:
        print("\n🎉 Successfully built commit histories:")
        for item in results['successful']:
            print(f"   ✅ {item['repo']}: {item['commits']} commits")
    
    if results['failed']:
        print("\n⚠️  Failed builds:")
        for item in results['failed']:
            print(f"   ❌ {item['repo']}: {item['error']}")
    
    if results['skipped']:
        print("\n⏭️  Skipped repos:")
        for item in results['skipped']:
            print(f"   ⚠️  {item['repo']}: {item['reason']}")
    
    # Save summary
    from datetime import datetime
    summary_path = Path(__file__).parent.parent.parent.parent / "governance" / "registry" / "commits" / "_build_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_eligible': len(eligible_repos),
            'successful': len(results['successful']),
            'failed': len(results['failed']),
            'skipped': len(results['skipped']),
            'results': results
        }, f, indent=2)
    
    print(f"\n📝 Build summary saved to: {summary_path}")


if __name__ == '__main__':
    build_all_commit_histories()
