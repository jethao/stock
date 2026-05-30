from pathlib import Path

from stock_agent.agents.confirmation import FixedConfirmationAgent
from stock_agent.config import ConfigurationError
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


def test_orchestrator_defaults_to_mock_data_provider(tmp_path, monkeypatch):
    monkeypatch.delenv("STOCK_AGENT_DATA_PROVIDER", raising=False)

    orchestrator = TradingOrchestrator(
        policy_path=Path("docs/investment-philosophy.md"),
        audit_path=tmp_path / "audit.jsonl",
        confirmation_agent=FixedConfirmationAgent(approved=False, reviewer="test"),
    )

    assert orchestrator.data_agent.__class__.__name__ == "DataAgent"


def test_orchestrator_fails_closed_for_missing_alpaca_config(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCK_AGENT_DATA_PROVIDER", "alpaca")
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SYMBOLS", raising=False)

    try:
        TradingOrchestrator(
            policy_path=Path("docs/investment-philosophy.md"),
            audit_path=tmp_path / "audit.jsonl",
            confirmation_agent=FixedConfirmationAgent(approved=False, reviewer="test"),
        )
    except ConfigurationError as exc:
        assert "ALPACA_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing Alpaca config to fail closed")
