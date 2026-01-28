import asyncio
import sys
from pathlib import Path

# Add root to sys.path
# Add Infrastructure root
sys.path.append(str(Path(__file__).resolve().parents[3]))
# Add User root (for infrastructure.* imports)
sys.path.append(str(Path(__file__).resolve().parents[4]))

try:
    from infrastructure.orchestration.federation_bus import get_federation_bus, FederationEvent
except ImportError:
    print("Could not import infrastructure.orchestration, trying orchestration directly...")
    from orchestration.federation_bus import get_federation_bus, FederationEvent

async def main():
    print("Initializing Bus...")
    bus = get_federation_bus()
    await bus.connect()
    
    print("Publishing test event...")
    event = FederationEvent.create(
        source="test_script",
        event_type="test.auto.logging",
        data={"message": "If you see this, the logger works!"}
    )
    
    await bus.publish(event)
    print("Event published.")
    
    # Give async writer a moment
    await asyncio.sleep(0.5)
    
    # Check file
    log_path = Path("c:/Users/kryst/Infrastructure/var/events/federation_bus.ndjson")
    if log_path.exists():
        print(f"Log file found at: {log_path}")
        print("Content:")
        print(log_path.read_text())
    else:
        print(f"ERROR: Log file not found at {log_path}")

if __name__ == "__main__":
    asyncio.run(main())
