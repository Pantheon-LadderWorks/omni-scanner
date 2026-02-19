#!/usr/bin/env python
"""
Generate a cleaned "full game board" tree for your user directory.

- Starts at ROOT (default: C:\\Users\\kryst)
- Skips AppData and common dependency / cache dirs
- Skips obviously-binary / vendor-style files
- Writes output to kryst_tree_clean.md in the current working dir
"""

from pathlib import Path
import sys

# ==== CONFIG ======================================================

# Root of the tree. You can override via command line:
# Root of the tree. You can override via command line.
DEFAULT_ROOT = "."

# Directory names whose *entire subtree* should be ignored
EXCLUDED_DIR_NAMES = {
    "AppData",
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".cache",
    ".cargo",
    ".conda",
    ".m2",
    ".npm",
    ".nuget",
    ".gradle",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    ".tox",
    "dist",
    "build",
    "target",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
}

# File extensions to skip (too big / uninteresting for a mental map)
EXCLUDED_FILE_EXTS = {
    ".dll", ".exe", ".pdb", ".lib",
    ".zip", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ".rar", ".iso",
    ".whl",
    ".bin", ".dat", ".pak",
    ".safetensors", ".pt", ".ckpt", ".onnx",
    ".mp4", ".mkv", ".mov", ".avi",
    ".mp3", ".flac", ".wav",
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".crdownload",
}

OUTPUT_FILE = "kryst_tree_clean.md"

# ==== LOGIC =======================================================

def should_skip_dir(path: Path) -> bool:
    """Return True if this directory or any of its parents is excluded."""
    for part in path.parts:
        if part in EXCLUDED_DIR_NAMES:
            return True
    return False


def should_skip_file(path: Path) -> bool:
    """Return True if this file lives in an excluded dir or has a junky extension."""
    if should_skip_dir(path.parent):
        return True
    ext = path.suffix.lower()
    if ext in EXCLUDED_FILE_EXTS:
        return True
    return False


def iter_entries(root: Path):
    """Yield (path, is_dir) for all relevant entries under root."""
    try:
        for entry in root.iterdir():
            # Skip excluded dirs completely
            if entry.is_dir():
                if should_skip_dir(entry):
                    continue
                yield entry, True
            else:
                if should_skip_file(entry):
                    continue
                yield entry, False
    except PermissionError:
        # Just skip stuff we can't read
        return


def walk_tree(root: Path, prefix: str, out):
    """Recursive pretty-printer, similar to `tree /A`."""
    entries = list(iter_entries(root))
    # Directories first, then files, alphabetical
    entries.sort(key=lambda e: (not e[1], e[0].name.lower()))

    for idx, (path, is_dir) in enumerate(entries):
        is_last = idx == len(entries) - 1
        connector = "└── " if is_last else "├── "
        out.write(f"{prefix}{connector}{path.name}\n")

        if is_dir:
            child_prefix = prefix + ("    " if is_last else "│   ")
            walk_tree(path, child_prefix, out)


def generate_tree(root_path, output_file="tree.md"):
    root = Path(root_path).resolve()
    
    # Ensure parent dir exists for output
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"Folder PATH listing (clean) for {root}\n\n")
        out.write(f"{root.name}\n")
        walk_tree(root, "", out)

    print(f"Done. Wrote cleaned tree to: {output_file}")

def main():
    root_str = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    generate_tree(root_str, OUTPUT_FILE)

if __name__ == "__main__":
    main()
