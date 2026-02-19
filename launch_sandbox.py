"""
launch_sandbox.py
Simulates a clean "User Install" by forcing Omni to load 
settings_template.py instead of your custom settings.py.
"""
import sys
import os
import importlib.util
from pathlib import Path

# 1. Define the Playground (The "User's Computer")
PLAYGROUND = Path(__file__).parent / "playground"
PLAYGROUND.mkdir(exist_ok=True)

# 2. Set Environment to "Clean Mode"
REAL_ROOT = Path(__file__).parent.resolve()
ARTIFACTS_ROOT = REAL_ROOT / "artifacts" / "sandbox_runs"
ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)

os.environ["OMNI_ROOT"] = str(PLAYGROUND.resolve())
os.environ["OMNI_ARTIFACTS"] = str(ARTIFACTS_ROOT)
os.environ["OMNI_SANDBOX"] = "1"
os.environ["OMNI_CMD_TEST"] = "1" # Prevent effective exit

# 3. THE MAGIC: Hot-Swap the Configuration Module
# We tell Python: "When anyone asks for 'omni.config.settings', give them the template instead."
template_path = Path("omni/config/settings_template.py")
if not template_path.exists():
    print(f"❌ Template not found at {template_path}")
    sys.exit(1)

spec = importlib.util.spec_from_file_location("omni.config.settings", template_path)
mock_settings = importlib.util.module_from_spec(spec)
sys.modules["omni.config.settings"] = mock_settings
spec.loader.exec_module(mock_settings)

# 4. Launch Omni
print(f"\n🎮 ENTERING OMNI SANDBOX MODE")
print(f"📂 Mock Root (Target): {PLAYGROUND.resolve()}")
print(f"📝 Artifacts (Output): {ARTIFACTS_ROOT}")
print(f"🔌 Heart Connection:   DISABLED (Forced Template Load)\n")

# Switch CWD to Playground so "scan ." works as expected
os.chdir(PLAYGROUND)

from omni.cli import main

if __name__ == "__main__":
    # Simulate a user typing "omni scan ."
    if len(sys.argv) == 1:
        sys.argv.append("scan")
        sys.argv.append(".")
    
    try:
        main()
    except SystemExit as e:
        print(f"\n[Sandbox] Exited with code: {e.code}")
