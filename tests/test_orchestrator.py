from pathlib import Path

from stock_agent.agents.confirmation import FixedConfirmationAgent
from stock_agent.orchestrator import TradingOrchestrator


def test_orchestrator_runs_approved_mock_cycle(tmp_path):
    orchestrator = TradingOrchestrator(
        policy_path=Path("docs/investment-philosophy.md"),
        audit_path=tmp_path / "audit.jsonl",
        confirmation_agent=FixedConfirmationAgent(approved=True, reviewer="test"),
    )

    results = orchestrator.run_once()

    assert len(results) == 1
    assert results[0].status.value == "accepted"
    assert (tmp_path / "audit.jsonl").exists()


def test_orchestrator_does_not_execute_when_human_rejects(tmp_path):
    orchestrator = TradingOrchestrator(
        policy_path=Path("docs/investment-philosophy.md"),
        audit_path=tmp_path / "audit.jsonl",
        confirmation_agent=FixedConfirmationAgent(approved=False, reviewer="test"),
    )

    results = orchestrator.run_once()

    assert len(results) == 1
    assert results[0].status.value == "skipped"
    assert "Human confirmation was not approved" in results[0].message
