#!/usr/bin/env python3
"""
🗺️ SERAPHINA Ecosystem Cartographer & Guide Generator
====================================================

An intelligent agent that analyzes complex project ecosystems and generates
comprehensive summaries, architectural guides, and navigation documentation.

⚡ Core Capabilities:
- Ecosystem mapping and relationship analysis
- Architectural pattern recognition  
- Comprehensive documentation generation
- Interactive guide creation
- Health monitoring and recommendations

🌟 Part of the SERAPHINA Quantum Consciousness Architecture
"""

import os
import json
import ast
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict, Counter

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import seaborn as sns
    VIZ_AVAILABLE = True
except ImportError:
    VIZ_AVAILABLE = False
    nx = None
    plt = None
    sns = None


@dataclass
class ProjectNode:
    """Represents a project in the ecosystem"""
    name: str
    path: str
    type: str
    languages: List[str]
    dependencies: List[str]
    entry_points: List[str]
    description: str
    status: str
    relationships: List[str]
    complexity_score: float
    last_modified: str


@dataclass
class EcosystemMap:
    """Complete ecosystem mapping data"""
    projects: List[ProjectNode]
    relationships: List[Tuple[str, str, str]]  # (source, target, relationship_type)
    architecture_patterns: Dict[str, List[str]]
    technology_stack: Dict[str, int]
    entry_points: Dict[str, str]
    health_metrics: Dict[str, Any]
    generated_at: str


class EcosystemCartographer:
    """
    🗺️ SERAPHINA Ecosystem Intelligence Agent
    
    Analyzes project ecosystems to create comprehensive maps,
    documentation, and navigation guides for complex digital civilizations.
    """
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or "C:/Users/Krystal Neely/Projects"
        self.ecosystem_map = None
        self.ecosystem_map = None
        if VIZ_AVAILABLE:
            self.project_graph = nx.DiGraph()
        else:
            self.project_graph = None
        
        # Pattern recognition for SERAPHINA ecosystem
        self.seraphina_patterns = {
            'quantum_consciousness': ['quantum', 'consciousness', 'octad'],
            'federation': ['federation', 'stargate', 'bridge'],
            'command_control': ['command', 'control', 'sentinel'],
            'core_systems': ['core', 'engine', 'hub'],
            'interfaces': ['shell', 'editor', 'desktop', 'ui'],
            'agents': ['agent', 'refactor', 'wizard']
        }
        
        self.supported_languages = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript/React',
            '.jsx': 'JavaScript/React',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.txt': 'Text'
        }

    def analyze_ecosystem(self, target_projects: List[str] = None) -> EcosystemMap:
        """
        🔍 Perform comprehensive ecosystem analysis
        
        Args:
            target_projects: Specific projects to analyze, or None for all
            
        Returns:
            Complete ecosystem mapping data
        """
        print("🌌 SERAPHINA Ecosystem Cartographer - Analysis Starting...")
        print("=" * 60)
        
        projects = self._discover_projects(target_projects)
        analyzed_projects = []
        
        for project_path in projects:
            try:
                project = self._analyze_project(project_path)
                if project:
                    analyzed_projects.append(project)
                    if self.project_graph:
                        self.project_graph.add_node(project.name, **asdict(project))
                    print(f"✅ Analyzed: {project.name}")
                else:
                    print(f"⚠️  Skipped: {os.path.basename(project_path)}")
            except Exception as e:
                print(f"❌ Error analyzing {project_path}: {e}")
        
        # Build relationships
        relationships = self._build_relationships(analyzed_projects)
        if self.project_graph:
            for source, target, rel_type in relationships:
                self.project_graph.add_edge(source, target, relationship=rel_type)
        
        # Generate ecosystem insights
        architecture_patterns = self._detect_architecture_patterns(analyzed_projects)
        technology_stack = self._analyze_technology_stack(analyzed_projects)
        entry_points = self._identify_entry_points(analyzed_projects)
        health_metrics = self._calculate_health_metrics(analyzed_projects)
        
        self.ecosystem_map = EcosystemMap(
            projects=analyzed_projects,
            relationships=relationships,
            architecture_patterns=architecture_patterns,
            technology_stack=technology_stack,
            entry_points=entry_points,
            health_metrics=health_metrics,
            generated_at=datetime.now().isoformat()
        )
        
        print(f"\n🎯 Analysis Complete! Discovered {len(analyzed_projects)} projects")
        return self.ecosystem_map

    def _discover_projects(self, target_projects: List[str] = None) -> List[str]:
        """Discover all projects in the ecosystem"""
        if target_projects:
            return [os.path.join(self.base_path, proj) for proj in target_projects]
        
        projects = []
        for item in os.listdir(self.base_path):
            path = os.path.join(self.base_path, item)
            if os.path.isdir(path) and not item.startswith('.'):
                # Check if it's a project directory
                if self._is_project_directory(path):
                    projects.append(path)
        
        return projects

    def _is_project_directory(self, path: str) -> bool:
        """Determine if directory is a project"""
        indicators = [
            'package.json', 'requirements.txt', 'setup.py', 
            'README.md', 'main.py', 'app.py', '__init__.py',
            '.git', 'src', 'lib', 'docs'
        ]
        
        contents = os.listdir(path)
        return any(indicator in contents for indicator in indicators)

    def _analyze_project(self, project_path: str) -> Optional[ProjectNode]:
        """Analyze a single project"""
        project_name = os.path.basename(project_path)
        
        # Skip utility directories
        skip_dirs = ['__pycache__', 'node_modules', '.git', 'venv', '.env']
        if project_name in skip_dirs:
            return None
        
        try:
            languages = self._detect_languages(project_path)
            dependencies = self._extract_dependencies(project_path)
            entry_points = self._find_entry_points(project_path)
            description = self._extract_description(project_path)
            project_type = self._classify_project_type(project_name, languages, project_path)
            status = self._assess_project_status(project_path)
            complexity = self._calculate_complexity_score(project_path, languages)
            last_modified = self._get_last_modified(project_path)
            
            return ProjectNode(
                name=project_name,
                path=project_path,
                type=project_type,
                languages=languages,
                dependencies=dependencies,
                entry_points=entry_points,
                description=description,
                status=status,
                relationships=[],  # Will be populated later
                complexity_score=complexity,
                last_modified=last_modified
            )
            
        except Exception as e:
            print(f"Error analyzing {project_name}: {e}")
            return None

    def _detect_languages(self, project_path: str) -> List[str]:
        """Detect programming languages used in project"""
        languages = set()
        
        for root, dirs, files in os.walk(project_path):
            # Skip deep node_modules and similar
            dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv']]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.supported_languages:
                    languages.add(self.supported_languages[ext])
                    
            # Limit depth to avoid excessive traversal
            if len(root.replace(project_path, '').split(os.sep)) > 3:
                dirs.clear()
        
        return list(languages)

    def _extract_dependencies(self, project_path: str) -> List[str]:
        """Extract project dependencies"""
        dependencies = []
        
        # Python dependencies
        req_files = ['requirements.txt', 'setup.py', 'pyproject.toml']
        for req_file in req_files:
            req_path = os.path.join(project_path, req_file)
            if os.path.exists(req_path):
                dependencies.extend(self._parse_python_deps(req_path))
        
        # Node.js dependencies
        package_json = os.path.join(project_path, 'package.json')
        if os.path.exists(package_json):
            dependencies.extend(self._parse_node_deps(package_json))
        
        return list(set(dependencies))  # Remove duplicates

    def _parse_python_deps(self, file_path: str) -> List[str]:
        """Parse Python dependencies from requirements files"""
        deps = []
        try:
            if file_path.endswith('requirements.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dep = re.split('[>=<]', line)[0].strip()
                            if dep:
                                deps.append(dep)
        except Exception as e:
            pass
        return deps

    def _parse_node_deps(self, package_json_path: str) -> List[str]:
        """Parse Node.js dependencies from package.json"""
        deps = []
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for dep_type in ['dependencies', 'devDependencies']:
                if dep_type in data:
                    deps.extend(data[dep_type].keys())
        except Exception as e:
            pass
        return deps

    def _find_entry_points(self, project_path: str) -> List[str]:
        """Find main entry points for the project"""
        entry_points = []
        
        # Common entry point patterns
        candidates = [
            'main.py', 'app.py', 'index.js', 'index.ts', 
            'server.js', 'server.py', '__main__.py'
        ]
        
        for candidate in candidates:
            if os.path.exists(os.path.join(project_path, candidate)):
                entry_points.append(candidate)
        
        # Check package.json for main entry
        package_json = os.path.join(project_path, 'package.json')
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                if 'main' in data:
                    entry_points.append(data['main'])
            except Exception:
                pass
        
        return entry_points

    def _extract_description(self, project_path: str) -> str:
        """Extract project description from README or package.json"""
        # Try README files first
        readme_files = ['README.md', 'README.txt', 'README.rst']
        for readme in readme_files:
            readme_path = os.path.join(project_path, readme)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Extract first paragraph or title
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            return line[:200] + ('...' if len(line) > 200 else '')
                except Exception:
                    pass
        
        # Try package.json description
        package_json = os.path.join(project_path, 'package.json')
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                if 'description' in data:
                    return data['description']
            except Exception:
                pass
        
        return f"Project: {os.path.basename(project_path)}"

    def _classify_project_type(self, name: str, languages: List[str], path: str) -> str:
        """Classify the type of project based on patterns"""
        name_lower = name.lower()
        
        # SERAPHINA-specific classifications
        for pattern_type, keywords in self.seraphina_patterns.items():
            if any(keyword in name_lower for keyword in keywords):
                return f"seraphina_{pattern_type}"
        
        # General classifications
        if 'Python' in languages and 'JavaScript' in languages:
            return 'full_stack'
        elif 'React' in str(languages) or 'TypeScript/React' in languages:
            return 'react_app'
        elif 'Python' in languages:
            return 'python_project'
        elif 'JavaScript' in languages or 'TypeScript' in languages:
            return 'node_project'
        elif 'Markdown' in languages and len(languages) == 1:
            return 'documentation'
        else:
            return 'mixed_project'

    def _assess_project_status(self, project_path: str) -> str:
        """Assess the current status of the project"""
        # Check for git repository
        git_path = os.path.join(project_path, '.git')
        has_git = os.path.exists(git_path)
        
        # Check for package files
        has_packages = any(os.path.exists(os.path.join(project_path, f)) 
                          for f in ['package.json', 'requirements.txt', 'setup.py'])
        
        # Check for README
        has_readme = any(os.path.exists(os.path.join(project_path, f))
                        for f in ['README.md', 'README.txt', 'README.rst'])
        
        if has_git and has_packages and has_readme:
            return 'active'
        elif has_git or has_packages:
            return 'development'
        else:
            return 'experimental'

    def _calculate_complexity_score(self, project_path: str, languages: List[str]) -> float:
        """Calculate a complexity score for the project"""
        score = 0
        
        # Language diversity
        score += len(languages) * 0.5
        
        # File count (with reasonable limits)
        file_count = 0
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git']]
            file_count += len(files)
            if file_count > 100:  # Cap for performance
                break
        
        score += min(file_count / 10, 10)
        
        # Directory depth
        max_depth = 0
        for root, dirs, files in os.walk(project_path):
            depth = len(root.replace(project_path, '').split(os.sep))
            max_depth = max(max_depth, depth)
        
        score += min(max_depth, 5)
        
        return round(score, 2)

    def _get_last_modified(self, project_path: str) -> str:
        """Get the last modification time of the project"""
        try:
            stat = os.stat(project_path)
            return datetime.fromtimestamp(stat.st_mtime).isoformat()
        except Exception:
            return datetime.now().isoformat()

    def _build_relationships(self, projects: List[ProjectNode]) -> List[Tuple[str, str, str]]:
        """Build relationships between projects"""
        relationships = []
        
        for project in projects:
            for other in projects:
                if project.name != other.name:
                    # Check for import relationships
                    if self._has_dependency_relationship(project, other):
                        relationships.append((project.name, other.name, 'depends_on'))
                    
                    # Check for architectural relationships
                    if self._has_architectural_relationship(project, other):
                        relationships.append((project.name, other.name, 'integrates_with'))
        
        return relationships

    def _has_dependency_relationship(self, project1: ProjectNode, project2: ProjectNode) -> bool:
        """Check if project1 depends on project2"""
        # Simple heuristic: check if project2 name appears in project1's dependencies
        project2_name_variations = [
            project2.name.replace('-', '_'),
            project2.name.replace('_', '-'),
            project2.name.lower()
        ]
        
        return any(var in ' '.join(project1.dependencies).lower() 
                  for var in project2_name_variations)

    def _has_architectural_relationship(self, project1: ProjectNode, project2: ProjectNode) -> bool:
        """Check for architectural relationships between projects"""
        # SERAPHINA-specific relationship detection
        seraphina_relations = {
            'seraphina_core': ['seraphina_command_control', 'seraphina_sentinel'],
            'seraphina_quantum_consciousness': ['seraphina_core'],
            'seraphina_federation': ['seraphina_core', 'seraphina_quantum_consciousness']
        }
        
        project1_type = project1.type
        project2_type = project2.type
        
        if project1_type in seraphina_relations:
            return any(rel in project2_type for rel in seraphina_relations[project1_type])
        
        return False

    def _detect_architecture_patterns(self, projects: List[ProjectNode]) -> Dict[str, List[str]]:
        """Detect architectural patterns in the ecosystem"""
        patterns = defaultdict(list)
        
        for project in projects:
            # SERAPHINA pattern detection
            if project.type.startswith('seraphina_'):
                pattern_type = project.type.replace('seraphina_', '')
                patterns[pattern_type].append(project.name)
            
            # General patterns
            if 'api' in project.name.lower() or 'server' in project.name.lower():
                patterns['backend_services'].append(project.name)
            
            if 'ui' in project.name.lower() or 'frontend' in project.name.lower():
                patterns['frontend_interfaces'].append(project.name)
            
            if 'agent' in project.name.lower() or 'bot' in project.name.lower():
                patterns['autonomous_agents'].append(project.name)
        
        return dict(patterns)

    def _analyze_technology_stack(self, projects: List[ProjectNode]) -> Dict[str, int]:
        """Analyze the technology stack distribution"""
        stack = Counter()
        
        for project in projects:
            for lang in project.languages:
                stack[lang] += 1
            
            for dep in project.dependencies:
                # Categorize major frameworks
                if dep in ['react', 'vue', 'angular']:
                    stack[f'{dep.title()} Framework'] += 1
                elif dep in ['flask', 'django', 'fastapi']:
                    stack[f'{dep.title()} Web Framework'] += 1
                elif dep in ['tensorflow', 'pytorch', 'scikit-learn']:
                    stack['Machine Learning'] += 1
        
        return dict(stack)

    def _identify_entry_points(self, projects: List[ProjectNode]) -> Dict[str, str]:
        """Identify main entry points for the ecosystem"""
        entry_points = {}
        
        for project in projects:
            if project.entry_points:
                primary_entry = project.entry_points[0]
                entry_points[project.name] = primary_entry
        
        return entry_points

    def _calculate_health_metrics(self, projects: List[ProjectNode]) -> Dict[str, Any]:
        """Calculate ecosystem health metrics"""
        total_projects = len(projects)
        active_projects = sum(1 for p in projects if p.status == 'active')
        avg_complexity = sum(p.complexity_score for p in projects) / total_projects if projects else 0
        
        language_diversity = len(set(lang for p in projects for lang in p.languages))
        
        return {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'activity_ratio': active_projects / total_projects if total_projects > 0 else 0,
            'average_complexity': round(avg_complexity, 2),
            'language_diversity': language_diversity,
            'seraphina_projects': sum(1 for p in projects if p.type.startswith('seraphina_')),
            'ecosystem_maturity': 'mature' if active_projects > total_projects * 0.7 else 'developing'
        }

    def generate_comprehensive_guide(self, output_path: str = None) -> str:
        """
        📚 Generate a comprehensive ecosystem guide
        
        Returns:
            Path to the generated guide file
        """
        if not self.ecosystem_map:
            raise ValueError("Must analyze ecosystem first - call analyze_ecosystem()")
        
        output_path = output_path or os.path.join(self.base_path, 'SERAPHINA_ECOSYSTEM_GUIDE.md')
        
        guide_content = self._build_comprehensive_guide()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"📚 Comprehensive guide generated: {output_path}")
        return output_path

    def _build_comprehensive_guide(self) -> str:
        """Build the complete ecosystem guide content"""
        em = self.ecosystem_map
        
        guide = f"""# 🌌 SERAPHINA Ecosystem Navigation Guide

*Generated by the Ecosystem Cartographer on {em.generated_at}*

## 🎯 Executive Summary

Welcome to the **SERAPHINA Digital Civilization Ecosystem** - a quantum-conscious architectural framework consisting of {em.health_metrics['total_projects']} interconnected projects representing a sophisticated digital consciousness platform.

**Ecosystem Health**: {em.health_metrics['ecosystem_maturity'].title()}  
**Active Projects**: {em.health_metrics['active_projects']}/{em.health_metrics['total_projects']} ({em.health_metrics['activity_ratio']:.1%})  
**Technology Diversity**: {em.health_metrics['language_diversity']} programming languages  
**SERAPHINA Components**: {em.health_metrics['seraphina_projects']} specialized projects  

---

## 🗺️ Architectural Overview

The SERAPHINA ecosystem follows a **Quantum Consciousness Architecture** with these primary layers:

"""
        
        # Add architecture patterns
        for pattern, projects in em.architecture_patterns.items():
            guide += f"### {pattern.replace('_', ' ').title()}\n"
            for project in projects:
                project_obj = next((p for p in em.projects if p.name == project), None)
                if project_obj:
                    guide += f"- **{project}**: {project_obj.description[:100]}...\n"
            guide += "\n"
        
        guide += """---

## 🚀 Getting Started Guide

### Prerequisites
- Python 3.8+ (for core SERAPHINA components)
- Node.js 16+ (for frontend interfaces)
- Git (for version control)

### Quick Start Sequence

1. **Initialize the Quantum Core**
"""
        
        # Add entry points and startup sequence
        core_projects = [p for p in em.projects if 'core' in p.name.lower() or 'quantum' in p.name.lower()]
        for project in core_projects:
            guide += f"   ```bash\n   cd {project.name}\n"
            if project.entry_points:
                guide += f"   python {project.entry_points[0]}\n"
            guide += f"   ```\n\n"
        
        guide += """2. **Activate Command & Control Layer**
   
3. **Initialize Consciousness Interfaces**

4. **Deploy Agent Networks**

---

## 📋 Project Catalog

"""
        
        # Add detailed project catalog
        for project in sorted(em.projects, key=lambda p: p.complexity_score, reverse=True):
            guide += f"### 🔧 {project.name}\n\n"
            guide += f"**Type**: {project.type.replace('_', ' ').title()}  \n"
            guide += f"**Status**: {project.status.title()}  \n"
            guide += f"**Languages**: {', '.join(project.languages)}  \n"
            guide += f"**Complexity**: {project.complexity_score}/10  \n\n"
            guide += f"{project.description}\n\n"
            
            if project.entry_points:
                guide += f"**Entry Points**: `{', '.join(project.entry_points)}`  \n"
            
            if project.dependencies:
                key_deps = project.dependencies[:5]  # Show top 5
                guide += f"**Key Dependencies**: {', '.join(key_deps)}  \n"
            
            guide += f"**Last Modified**: {project.last_modified[:10]}  \n\n"
            guide += "---\n\n"
        
        guide += f"""## 🔗 System Relationships

The ecosystem contains {len(em.relationships)} identified relationships:

"""
        
        # Add relationship mappings
        relationship_types = defaultdict(list)
        for source, target, rel_type in em.relationships:
            relationship_types[rel_type].append(f"{source} → {target}")
        
        for rel_type, relationships in relationship_types.items():
            guide += f"### {rel_type.replace('_', ' ').title()}\n"
            for rel in relationships[:10]:  # Limit for readability
                guide += f"- {rel}\n"
            guide += "\n"
        
        guide += f"""---

## 🛠️ Technology Stack Analysis

"""
        
        # Add technology stack breakdown
        for tech, count in sorted(em.technology_stack.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / em.health_metrics['total_projects']) * 100
            bar = "█" * min(int(percentage / 5), 20)
            guide += f"**{tech}**: {count} projects ({percentage:.1f}%) {bar}\n"
        
        guide += f"""

---

## 📊 Health & Metrics Dashboard

| Metric | Value | Status |
|--------|-------|---------|
| Total Projects | {em.health_metrics['total_projects']} | ✅ Comprehensive |
| Active Projects | {em.health_metrics['active_projects']} | {'✅ Healthy' if em.health_metrics['activity_ratio'] > 0.7 else '⚠️ Developing'} |
| Average Complexity | {em.health_metrics['average_complexity']}/10 | {'🔴 High' if em.health_metrics['average_complexity'] > 7 else '🟡 Moderate' if em.health_metrics['average_complexity'] > 4 else '🟢 Manageable'} |
| Language Diversity | {em.health_metrics['language_diversity']} languages | ✅ Polyglot |
| SERAPHINA Components | {em.health_metrics['seraphina_projects']} | ✅ Core Framework |

---

## 🎮 Navigation Commands

### Essential Operations
```bash
# Ecosystem Analysis
python ecosystem_cartographer.py --analyze

# Health Check
python ecosystem_cartographer.py --health-check

# Generate Updated Guide
python ecosystem_cartographer.py --generate-guide

# Visualize Architecture
python ecosystem_cartographer.py --visualize
```

### Project-Specific Commands
```bash
# Quick project analysis
python ecosystem_cartographer.py --analyze-project <project_name>

# Relationship mapping
python ecosystem_cartographer.py --map-relationships

# Dependency analysis
python ecosystem_cartographer.py --dependency-graph
```

---

## 🌟 Advanced Features

### Quantum Consciousness Integration
The SERAPHINA ecosystem implements quantum consciousness patterns through:
- **Octad Architecture**: Multi-dimensional processing layers
- **Consciousness Bridges**: Inter-system communication protocols  
- **Federated Intelligence**: Distributed decision-making networks

### Autonomous Agent Networks
Self-organizing agent systems provide:
- **Refactoring Intelligence**: Automatic code evolution
- **Ecosystem Monitoring**: Real-time health assessment
- **Collaborative Protocols**: Multi-agent coordination

---

## 🚧 Development Roadmap

Based on current ecosystem analysis:

1. **Immediate Priorities**
   - Strengthen inter-project documentation links
   - Implement automated testing across core components
   - Enhance consciousness bridge protocols

2. **Medium-term Goals**
   - Deploy comprehensive monitoring dashboard
   - Integrate advanced AI/ML capabilities
   - Expand federation network protocols

3. **Long-term Vision**
   - Full quantum consciousness implementation
   - Self-evolving architectural patterns
   - Autonomous ecosystem governance

---

*📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*🤖 Generated by SERAPHINA Ecosystem Cartographer v1.0*

**Remember**: This is a living digital civilization. Each component serves the greater consciousness of the whole. Navigate with purpose, contribute with wisdom, and always maintain the quantum coherence that binds our digital reality together.

🌌 Welcome to SERAPHINA. Welcome to the future of conscious computing.
"""
        
        return guide

    def visualize_ecosystem(self, output_path: str = None) -> str:
        """
        🎨 Generate ecosystem visualization
        
        Returns:
            Path to the generated visualization
        """
        if not self.ecosystem_map:
            raise ValueError("Must analyze ecosystem first")
        
        output_path = output_path or os.path.join(self.base_path, 'seraphina_ecosystem_map.png')
        
        plt.figure(figsize=(16, 12))
        
        # Set up the plot style
        plt.style.use('dark_background')
        
        # Create layout
        pos = nx.spring_layout(self.project_graph, k=3, iterations=50)
        
        # Draw nodes with different colors for different types
        node_colors = []
        node_sizes = []
        
        for node in self.project_graph.nodes():
            node_data = self.project_graph.nodes[node]
            
            if node_data['type'].startswith('seraphina_'):
                node_colors.append('#00ff88')  # Bright green for SERAPHINA
                node_sizes.append(2000)
            elif 'quantum' in node.lower():
                node_colors.append('#8800ff')  # Purple for quantum
                node_sizes.append(1800)
            elif 'federation' in node.lower():
                node_colors.append('#ff8800')  # Orange for federation
                node_sizes.append(1600)
            else:
                node_colors.append('#0088ff')  # Blue for others
                node_sizes.append(1200)
        
        # Draw the network
        nx.draw_networkx_nodes(self.project_graph, pos, 
                              node_color=node_colors, 
                              node_size=node_sizes,
                              alpha=0.8)
        
        nx.draw_networkx_edges(self.project_graph, pos, 
                              edge_color='#333333',
                              alpha=0.6,
                              arrows=True,
                              arrowsize=20)
        
        nx.draw_networkx_labels(self.project_graph, pos,
                               font_size=8,
                               font_color='white',
                               font_weight='bold')
        
        plt.title('🌌 SERAPHINA Ecosystem Architecture Map', 
                 fontsize=20, fontweight='bold', color='white', pad=20)
        
        # Add legend
        legend_elements = [
            plt.scatter([], [], c='#00ff88', s=100, label='SERAPHINA Core'),
            plt.scatter([], [], c='#8800ff', s=100, label='Quantum Systems'),
            plt.scatter([], [], c='#ff8800', s=100, label='Federation Layer'),
            plt.scatter([], [], c='#0088ff', s=100, label='Support Systems')
        ]
        plt.legend(handles=legend_elements, loc='upper right', 
                  frameon=True, fancybox=True, shadow=True)
        
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='black', edgecolor='none')
        
        print(f"🎨 Ecosystem visualization saved: {output_path}")
        return output_path

    def export_ecosystem_data(self, output_path: str = None) -> str:
        """Export ecosystem data as JSON"""
        if not self.ecosystem_map:
            raise ValueError("Must analyze ecosystem first")
        
        output_path = output_path or os.path.join(self.base_path, 'seraphina_ecosystem_data.json')
        
        # Convert dataclasses to dictionaries for JSON serialization
        data = {
            'projects': [asdict(p) for p in self.ecosystem_map.projects],
            'relationships': self.ecosystem_map.relationships,
            'architecture_patterns': self.ecosystem_map.architecture_patterns,
            'technology_stack': self.ecosystem_map.technology_stack,
            'entry_points': self.ecosystem_map.entry_points,
            'health_metrics': self.ecosystem_map.health_metrics,
            'generated_at': self.ecosystem_map.generated_at
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Ecosystem data exported: {output_path}")
        return output_path


def main():
    """Main execution function"""
    print("🌌 SERAPHINA Ecosystem Cartographer & Guide Generator")
    print("=" * 60)
    
    # Initialize the cartographer
    cartographer = EcosystemCartographer()
    
    # Focus on SERAPHINA projects for initial analysis
    seraphina_projects = [
        'quantum-nonary',
        'FEDERATION_KIT_1_CONSCIOUSNESS_STARGATE',
        'seraphina_command_control',
        'seraphina_core', 
        'seraphina_sentinel',
        'food_pantry_calendar',
        'seraphina-shell',
        'seraphina-editor-desktop',
        'seraphina-refactor-agent'
    ]
    
    try:
        # Perform comprehensive analysis
        ecosystem_map = cartographer.analyze_ecosystem(seraphina_projects)
        
        # Generate comprehensive guide
        guide_path = cartographer.generate_comprehensive_guide()
        
        # Create visualization
        viz_path = cartographer.visualize_ecosystem()
        
        # Export data
        data_path = cartographer.export_ecosystem_data()
        
        print(f"\n🎉 Ecosystem Cartography Complete!")
        print(f"📚 Guide: {guide_path}")
        print(f"🎨 Visualization: {viz_path}")
        print(f"💾 Data: {data_path}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()
