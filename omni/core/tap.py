import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

class CrownBusTap:
    """
    Runtime tap for intercepting and logging Crown Bus events.
    Usage:
        tap = CrownBusTap()
        tap.attach(my_bus_instance) 
        # ... run tests ...
        # events logged to events_observed.ndjson
    """
    def __init__(self, log_path: str = "events_observed.ndjson"):
        self.log_path = Path(log_path)
        
    def attach(self, bus_instance: Any, method_name: str = "publish"):
        """
        Monkey-patches the bus instance's publish method to intercept calls.
        """
        original_method = getattr(bus_instance, method_name)
        
        def tapped_publish(*args, **kwargs):
            # Capture
            try:
                # Naive capture of args/kwargs
                payload = {
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "args": [str(a) for a in args],
                    "kwargs": {k: str(v) for k, v in kwargs.items()}
                }
                self.log_event(payload)
            except Exception:
                pass # Do not break runtime
                
            # Passthrough
            return original_method(*args, **kwargs)
            
        setattr(bus_instance, method_name, tapped_publish)
        print(f"[TAP] Attached to {bus_instance}.{method_name}")

    def log_event(self, event_data: dict):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_data) + "\n")
