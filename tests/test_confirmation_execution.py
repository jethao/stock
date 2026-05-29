import json
from pathlib import Path

from stock_agent.agents.audit import AuditAgent
from stock_agent.agents.confirmation import FixedConfirmationAgent
from stock_agent.agents.execution import ExecutionAgent, PaperBroker
from stock_agent.agents.portfolio import PortfolioAgent
from stock_agent.models import Asset, AssetType, DecisionStatus, PortfolioState, RiskDecision, TradeIntent, TradeSide
from stock_agent.policies.investment import InvestmentPolicy


def make_intent(amount=5_000.0):
    asset = Asset(symbol="PLTR", asset_type=AssetType.STOCK, sector="AI")
    return TradeIntent(
        asset=asset,
        side=TradeSide.BUY,
        proposed_amount=amount,
        proposed_weight=0.05,
        time_horizon="long_term",
        strategy="quality_drawdown_mean_reversion",
        rationale="Temporary drawdown with no identified material deterioration.",
        signals={},
    )


def make_portfolio():
    return PortfolioState(
        cash=50_000.0,
        positions=[],
        total_account_value=100_000.0,
        margin_enabled=False,
        reconciled=True,
        buying_power=50_000.0,
        bought_value_today=0.0,
    )


def test_portfolio_review_calculates_post_trade_weight_and_tax_note():
    policy = InvestmentPolicy.default(Path("docs/investment-philosophy.md"))
    intent = make_intent(amount=10_000.0)
    review = PortfolioAgent(policy).review(intent, make_portfolio(), tax_lots=[])

    assert review.holding_count_after_trade == 1
    assert review.post_trade_weight == 0.10
    assert any("No tax lot impact identified" in note for note in review.tax_notes)


def test_execution_is_skipped_without_human_confirmation():
    intent = make_intent()
    risk = RiskDecision(intent=intent, status=DecisionStatus.APPROVED)
    confirmation = FixedConfirmationAgent(approved=False, reviewer="test").request(intent, risk, None)
    result = ExecutionAgent(PaperBroker()).execute(intent, risk, confirmation)

    assert result.status.value == "skipped"
    assert "Human confirmation was not approved" in result.message


def test_approved_trade_executes_against_paper_broker():
    intent = make_intent(amount=2_000.0)
    risk = RiskDecision(intent=intent, status=DecisionStatus.APPROVED)
    confirmation = FixedConfirmationAgent(approved=True, reviewer="test").request(intent, risk, None)
    result = ExecutionAgent(PaperBroker()).execute(intent, risk, confirmation)

    assert result.status.value == "accepted"
    assert result.filled_amount == 2_000.0
    assert result.filled_quantity > 0


def test_audit_agent_writes_jsonl_record(tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    audit = AuditAgent(audit_path)
    intent = make_intent()

    audit.record("risk", {"intent": intent, "outcome": "approved"})

    lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["component"] == "risk"
    assert payload["payload"]["intent"]["asset"]["symbol"] == "PLTR"
