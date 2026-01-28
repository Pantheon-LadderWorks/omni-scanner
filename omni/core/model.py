from dataclasses import dataclass, field, asdict
from typing import Dict, Any
from datetime import datetime

@dataclass
class ScanResult:
    target: str
    version: str = "0.1"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    findings: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
