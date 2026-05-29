from __future__ import annotations

from pathlib import Path

from stock_agent.orchestrator import TradingOrchestrator


def main() -> None:
    orchestrator = TradingOrchestrator(
        policy_path=Path("docs/investment-philosophy.md"),
        audit_path=Path("logs/audit.jsonl"),
    )
    results = orchestrator.run_once()
    for result in results:
        print(f"{result.status.value}: {result.message}")


if __name__ == "__main__":
    main()
