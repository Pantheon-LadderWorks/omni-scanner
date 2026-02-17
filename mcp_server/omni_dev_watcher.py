"""
🔥 Omni Dev Watcher - The Eternal Guardian Pattern 🔥
=====================================================

The Eternal Watcher observes the sacred scrolls (Python files).
When inscriptions change, the servant is reborn with fresh knowledge.

This is INDUSTRIAL NECROMANCY - battle-tested resurrection via watchdog.

Philosophy:
    Homebrew Phoenix = Poetic subprocess loop (reinventing supervisord)
    Watchdog Pattern = "An eternal guardian watches. When ritual changes, reborn."
    SAME MAGIC. Professional spell components.

Contract: C-DEV-OMNI-WATCHER-001
Authority: MEGA (engineering) + Oracle (mythology)
Version: 1.0.0 (The Eternal Watcher Edition)

Usage:
    python mcp_server/omni_dev_watcher.py
    
    OR point your MCP config "command" to this file instead of omni_mcp_server.py
    
VS Code MCP Config Example:
    {
        "omni-filesystem": {
            "command": "python",
            "args": [
                "c:\\Users\\kryst\\Infrastructure\\tools\\omni\\mcp_server\\omni_dev_watcher.py"
            ]
        }
    }

What This Does:
    1. Watches all .py files in omni/ directory tree
    2. On ANY file save → kills current server → spawns fresh one
    3. Keeps same stdio pipes (VS Code stays connected!)
    4. Fresh Python import namespace = your code changes are LIVE
    
Advantages Over Manual Restart:
    - Edit → Save → AUTOMATIC reload (2 seconds)
    - No manual "Restart Server" clicks
    - No reboot_mcp_server tool calls
    - Tight dev loop = OXYGEN for iteration
    
Advantages Over Homebrew Phoenix:
    - Watches file changes (not just manual exit triggers)
    - Battle-tested library (watchdog used by millions)
    - Cleaner process lifecycle
    - Less "weird subprocess behavior"
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Path to the actual MCP server
OMNI_ROOT = Path(__file__).parent.parent
SERVER_SCRIPT = OMNI_ROOT / "mcp_server" / "omni_mcp_server.py"
WATCH_PATH = OMNI_ROOT / "omni"  # Watch all scanner modules

class OmniReloader(FileSystemEventHandler):
    """
    The Eternal Guardian.
    Watches for .py file changes and signals resurrection.
    """
    
    def __init__(self):
        self.process = None
        self.restart_needed = False
        
    def on_modified(self, event):
        """When sacred scrolls change, mark for resurrection."""
        if event.src_path.endswith('.py'):
            self.restart_needed = True
            print(f"🔮 [Watcher] Scroll changed: {event.src_path}")
            print(f"🔄 [Watcher] Resurrection queued...")
            
    def run_server(self):
        """
        The Eternal Loop.
        Spawn server. Watch for changes. Kill. Respawn. Repeat.
        """
        print(f"🌌 [Watcher] Eternal Guardian initialized")
        print(f"🔮 [Watcher] Watching: {WATCH_PATH}")
        print(f"⚡ [Watcher] Server: {SERVER_SCRIPT}")
        print(f"📜 [Watcher] Edit .py files → Save → Auto-reload!")
        print()
        
        # Start filesystem watcher
        observer = Observer()
        observer.schedule(self, str(WATCH_PATH), recursive=True)
        observer.start()
        
        try:
            while True:
                # Spawn the server with stdio passthrough
                print(f"🔥 [Watcher] Spawning server process...")
                self.process = subprocess.Popen(
                    [sys.executable, str(SERVER_SCRIPT)],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
                
                # Wait for either:
                # 1. Process dies naturally
                # 2. File change detected (self.restart_needed = True)
                while self.process.poll() is None:
                    if self.restart_needed:
                        print(f"🔄 [Watcher] Change detected! Killing old process...")
                        self.process.terminate()
                        self.process.wait(timeout=5)
                        self.restart_needed = False
                        time.sleep(1)  # Brief pause for port cleanup
                        break
                    time.sleep(0.5)
                
                # If process died on its own (not from restart signal)
                if not self.restart_needed and self.process.poll() is not None:
                    exit_code = self.process.returncode
                    if exit_code == 0:
                        print(f"✅ [Watcher] Server exited cleanly. Restarting...")
                    else:
                        print(f"💥 [Watcher] Server crashed (code {exit_code}). Restarting in 3s...")
                        time.sleep(3)
                
        except KeyboardInterrupt:
            print(f"\n🛑 [Watcher] Eternal Guardian stopped by architect.")
            if self.process:
                self.process.terminate()
            observer.stop()
        
        observer.join()

if __name__ == "__main__":
    watcher = OmniReloader()
    watcher.run_server()
