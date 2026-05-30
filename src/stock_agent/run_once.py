from __future__ import annotations

import sys
from pathlib import Path

from stock_agent.config import ConfigurationError
from stock_agent.orchestrator import TradingOrchestrator


def main() -> None:
    try:
        orchestrator = TradingOrchestrator(
            policy_path=Path("docs/investment-philosophy.md"),
            audit_path=Path("logs/audit.jsonl"),
        )
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    results = orchestrator.run_once()
    for result in results:
        print(f"{result.status.value}: {result.message}")


if __name__ == "__main__":
    main()
