from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stock_agent.models import to_serializable


class AuditAgent:
    def __init__(self, audit_path: Path) -> None:
        self.audit_path = audit_path

    def record(self, component: str, payload: dict[str, Any]) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": component,
            "payload": to_serializable(payload),
        }
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
