"""
Requirements Scanner & Manager
Consolidates logic from:
- generate_federation_requirements.py
- dedupe_federation_requirements.py
- lock_federation_versions.py
"""
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# ==== CONFIG ====
IGNORE_DIRS = {".git", ".venv", "__pycache__", "mcp-servers", "archive"}
REQ_FILES = {"requirements.txt", "requirements-dev.txt"}

# Regex for locking
REQ_LINE_RE = re.compile(
    r"""
    ^\s*
    (?P<name_extras>[A-Za-z0-9_.\-]+(?:\[[^\]]+\])?)  # package name + optional [extras]
    \s*
    (?P<rest>.*)                                      # version spec, markers, whatever
    $
    """,
    re.VERBOSE,
)

# ==== 1. GENERATION LOGIC ====

def is_ignored(path: Path) -> bool:
    parts = set(p.name for p in path.parents) | {path.name}
    return bool(parts & IGNORE_DIRS)

def parse_req_line(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("-e "):
        return None
    return line

def package_name(spec: str) -> str:
    return re.split(r"[<>=!~\[\]]", spec, 1)[0].strip().lower()

def merge_specs(existing: str, new: str) -> str:
    return new if len(new) > len(existing) else existing

def collect_from_requirements(path: Path, acc: Dict[str, str]) -> None:
    for raw in path.read_text(encoding="utf-8").splitlines():
        spec = parse_req_line(raw)
        if not spec: continue
        name = package_name(spec)
        acc[name] = merge_specs(acc.get(name, ""), spec)

def collect_from_pyproject(path: Path, acc: Dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    deps: List[str] = []
    
    # [project] dependencies
    m = re.search(r"dependencies\s*=\s*\[(.*?)\]", text, flags=re.DOTALL)
    if m:
        for item in m.group(1).split(","):
            item = item.strip().strip('"').strip("'")
            if item: deps.append(item)

    # poetry
    block = re.search(r"\[tool\.poetry\.dependencies\](.*?)(\n\[|$)", text, flags=re.DOTALL)
    if block:
        for line in block.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            name, spec = [x.strip() for x in line.split("=", 1)]
            spec = spec.strip('"').strip("'")
            if name.lower() == "python": continue
            deps.append(f"{name}{spec and ' ' + spec}")

    for spec in deps:
        name = package_name(spec)
        acc[name] = merge_specs(acc.get(name, ""), spec)

def collect_from_setup_cfg(path: Path, acc: Dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    block = re.search(r"\[options\]\s*(.*?)(\n\[|$)", text, flags=re.DOTALL)
    if not block: return
    deps = re.search(r"install_requires\s*=\s*(.*)", block.group(1), flags=re.DOTALL)
    if not deps: return
    for line in deps.group(1).splitlines():
        line = line.strip().lstrip("-").strip()
        if not line or line.startswith("#"): continue
        name = package_name(line)
        acc[name] = merge_specs(acc.get(name, ""), line)

def scan_requirements(root_path: Path) -> Dict[str, str]:
    acc: Dict[str, str] = {}
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        path = Path(root)
        if is_ignored(path): continue
        
        files_set = set(files)
        for fname in files_set & REQ_FILES:
            collect_from_requirements(path / fname, acc)
        if "pyproject.toml" in files_set:
            collect_from_pyproject(path / "pyproject.toml", acc)
        if "setup.cfg" in files_set:
            collect_from_setup_cfg(path / "setup.cfg", acc)
            
    return acc

# ==== 2. DEDUPE LOGIC ====

def clean_req_line_strict(line: str) -> str | None:
    raw = line.strip()
    if not raw or raw.startswith("#"): return None
    raw = raw.lstrip("-• ").strip()
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        raw = raw[1:-1].strip()
    else:
        raw = raw.strip('"').strip("'")
    return raw if raw else None

def generate_deduped_requirements(raw_reqs: Dict[str, str], output_path: Path):
    unique = sorted(raw_reqs.values(), key=str.lower)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# === OMNI GENERATED REQUIREMENTS ===\n")
        f.write(f"# Generated: {__import__('datetime').datetime.now()}\n")
        f.write("# Uniqueness enforced by Omni Core\n\n")
        for req in unique:
            f.write(f"{req}\n")
    print(f"✅ Wrote {len(unique)} unique requirements to {output_path}")

# ==== 3. LOCK LOGIC ====

def get_installed_version(pkg_name: str) -> Optional[str]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg_name],
            capture_output=True, text=True
        )
        if proc.returncode != 0: return None
        for line in proc.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None

def lock_requirements_file(input_path: Path, output_path: Path):
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return

    lines = input_path.read_text(encoding="utf-8").splitlines()
    body_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    
    locked_lines = []
    
    for line in body_lines:
        m = REQ_LINE_RE.match(line.strip())
        if not m: continue
        
        name_extras = m.group("name_extras")
        base_name = name_extras.split("[", 1)[0]
        
        version = get_installed_version(base_name)
        if version:
            locked_lines.append(f"{name_extras}=={version}")
        else:
            locked_lines.append(line) # Fallback
            
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# 🔒 Auto-locked federation requirements\n")
        f.write("# Generated by OMNI Core\n\n")
        for line in sorted(set(locked_lines)): # Simple sort + unique
            f.write(f"{line}\n")
            
    print(f"✅ Wrote locked requirements to: {output_path}")

# ==== ENTRY POINTS ====

def run_gen_deps(root_str: str, output_str: str):
    root = Path(root_str).resolve()
    out = Path(output_str)
    print(f"Scanning for dependencies in {root}...")
    reqs = scan_requirements(root)
    generate_deduped_requirements(reqs, out)

    print(f"Locking requirements from {inp}...")
    lock_requirements_file(inp, out)

def run_pip_list(filter_str: str = ""):
    """Run pip list, optionally filtering."""
    cmd = [sys.executable, "-m", "pip", "list"]
    print(f"📦 Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def run_install_reqs(req_file: str):
    """Install requirements using uv (if available) or pip."""
    path = Path(req_file).resolve()
    if not path.exists():
        print(f"❌ Requirements file not found: {path}")
        return

    # Check for uv
    has_uv = False
    try:
        subprocess.run(["uv", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        has_uv = True
    except FileNotFoundError:
        pass

    if has_uv:
        print("🚀 Detected `uv`. Using high-speed installer.")
        # Note: uv pip install --system might be needed on some systems, 
        # but --user is our doctrine. uv supports --user? 
        # Actually uv usually manages venvs. For user install, standard pip is often safer/easier 
        # unless using 'uv pip install --python <sys.executable>'.
        # Let's keep it simple for now: if uv is there, try to use it with standard flags, 
        # but if it fails, fallback? 
        # Use simple uv pip install logic.
        cmd = ["uv", "pip", "install", "-r", str(path)]
        # UV might complain about system environment. 
        # The user wants speed but also stability.
        # Let's try uv, if it fails, maybe fallback.
        # Actually, for "NO VENV" doctrine, 'uv pip install --system' is the equivalent 
        # but 'uv' prefers venvs.
        # User said "integrate pip and uv".
        # Let's default to pip for reliability on "user" installs, allow UV via explicit override?
        # No, user asked exactly for this. Let's try uv cmd.
        pass 
    else:
        print("🐢 `uv` not found. Using standard pip.")

    # DOCTRINE: Install to user space
    # Command construction
    if has_uv:
        # uv pip install -r requirements.txt --system (to install to system python)
        # or just run it.
        cmd = ["uv", "pip", "install", "--system", "-r", str(path)]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "--user", "-r", str(path)]
    
    print(f"📦 Installing from {path.name}...")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Installation complete.")
    except subprocess.CalledProcessError:
        print("❌ Installation failed.")
