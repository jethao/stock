# Trading Agent Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic paper-trading agent scaffold that converts the investment philosophy into typed trade intents, portfolio reviews, risk decisions, human confirmations, paper executions, and audit records.

**Architecture:** The system is a small Python package with explicit agents connected by dataclass domain models. The orchestrator runs one evaluation cycle using mock data and a paper broker; no live brokerage or real-money execution path exists.

**Tech Stack:** Python 3 standard library, dataclasses, JSONL audit logs, pytest.

---

## File Structure

- Create `pyproject.toml`: project metadata, package discovery, pytest config.
- Create `src/stock_agent/__init__.py`: package marker and version.
- Create `src/stock_agent/models.py`: shared dataclass models and enums.
- Create `src/stock_agent/policies/__init__.py`: policy package exports.
- Create `src/stock_agent/policies/investment.py`: structured policy defaults and markdown policy loading.
- Create `src/stock_agent/agents/__init__.py`: agent package exports.
- Create `src/stock_agent/agents/data.py`: mock market, fundamentals, portfolio, and tax-lot data.
- Create `src/stock_agent/agents/strategy.py`: converts data into trade intents.
- Create `src/stock_agent/agents/portfolio.py`: portfolio construction review and tax notes.
- Create `src/stock_agent/agents/risk.py`: hard-rule and warning checks.
- Create `src/stock_agent/agents/confirmation.py`: CLI and fixed human confirmation providers.
- Create `src/stock_agent/agents/execution.py`: execution gate and paper broker adapter.
- Create `src/stock_agent/agents/audit.py`: JSONL audit writer.
- Create `src/stock_agent/orchestrator.py`: single-cycle workflow coordination.
- Create `src/stock_agent/run_once.py`: CLI entrypoint for one mock cycle.
- Create `tests/test_risk_agent.py`: risk hard-rule tests.
- Create `tests/test_confirmation_execution.py`: confirmation and execution tests.
- Create `tests/test_orchestrator.py`: end-to-end mock cycle tests.

## Task 1: Project Skeleton And Domain Models

**Files:**
- Create: `pyproject.toml`
- Create: `src/stock_agent/__init__.py`
- Create: `src/stock_agent/models.py`
- Test: `tests/test_models_import.py`

- [ ] **Step 1: Write the failing import test**

Create `tests/test_models_import.py`:

```python
from stock_agent.models import (
    Asset,
    AssetType,
    MarketSnapshot,
    PortfolioState,
    Position,
    TradeIntent,
    TradeSide,
)


def test_domain_models_can_be_constructed():
    asset = Asset(symbol="PLTR", asset_type=AssetType.STOCK, sector="AI")
    market = MarketSnapshot(
        asset=asset,
        price=20.0,
        previous_close=22.0,
        drawdown_from_recent_high=-0.18,
        average_daily_volume=25_000_000,
        is_penny_stock=False,
        is_leveraged_etf=False,
        earnings_within_days=None,
    )
    portfolio = PortfolioState(
        cash=10_000.0,
        positions=[Position(asset=asset, quantity=10.0, market_price=20.0, cost_basis=15.0)],
        total_account_value=10_200.0,
        margin_enabled=False,
        reconciled=True,
        buying_power=10_000.0,
        bought_value_today=0.0,
    )
    intent = TradeIntent(
        asset=asset,
        side=TradeSide.BUY,
        proposed_amount=1_000.0,
        proposed_weight=0.098,
        time_horizon="long_term",
        strategy="quality_drawdown_mean_reversion",
        rationale="Temporary drawdown with no identified material deterioration.",
        signals={"drawdown_from_recent_high": -0.18},
    )

    assert market.asset.symbol == "PLTR"
    assert portfolio.total_account_value == 10_200.0
    assert intent.side is TradeSide.BUY
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_models_import.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'stock_agent'`.

- [ ] **Step 3: Add project metadata and package marker**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "stock-agent"
version = "0.1.0"
description = "Paper trading agent scaffold with deterministic risk gates."
requires-python = ">=3.11"
dependencies = []

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `src/stock_agent/__init__.py`:

```python
"""Paper trading agent scaffold."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Implement domain models**

Create `src/stock_agent/models.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AssetType(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    VENTURE_FUND = "venture_fund"


class TradeSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class DecisionStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class ExecutionStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class Asset:
    symbol: str
    asset_type: AssetType
    sector: str
    name: str | None = None


@dataclass(frozen=True)
class MarketSnapshot:
    asset: Asset
    price: float
    previous_close: float
    drawdown_from_recent_high: float
    average_daily_volume: int
    is_penny_stock: bool
    is_leveraged_etf: bool
    earnings_within_days: int | None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class FundamentalSnapshot:
    asset: Asset
    quality_score: float
    material_risk_detected: bool
    summary: str


@dataclass(frozen=True)
class TaxLot:
    asset: Asset
    quantity: float
    cost_basis: float
    acquired_at: datetime


@dataclass(frozen=True)
class Position:
    asset: Asset
    quantity: float
    market_price: float
    cost_basis: float

    @property
    def market_value(self) -> float:
        return self.quantity * self.market_price


@dataclass(frozen=True)
class PortfolioState:
    cash: float
    positions: list[Position]
    total_account_value: float
    margin_enabled: bool
    reconciled: bool
    buying_power: float
    bought_value_today: float

    def position_for(self, symbol: str) -> Position | None:
        return next((position for position in self.positions if position.asset.symbol == symbol), None)

    def current_weight(self, symbol: str) -> float:
        position = self.position_for(symbol)
        if position is None or self.total_account_value <= 0:
            return 0.0
        return position.market_value / self.total_account_value


@dataclass(frozen=True)
class TradeIntent:
    asset: Asset
    side: TradeSide
    proposed_amount: float
    proposed_weight: float
    time_horizon: str
    strategy: str
    rationale: str
    signals: dict[str, Any] = field(default_factory=dict)
    uses_margin: bool = False


@dataclass(frozen=True)
class PortfolioReview:
    intent: TradeIntent
    holding_count_after_trade: int
    post_trade_weight: float
    warnings: list[str] = field(default_factory=list)
    tax_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RiskDecision:
    intent: TradeIntent
    status: DecisionStatus
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def approved(self) -> bool:
        return self.status is DecisionStatus.APPROVED


@dataclass(frozen=True)
class HumanConfirmation:
    intent: TradeIntent
    approved: bool
    reviewer: str
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ExecutionResult:
    intent: TradeIntent
    status: ExecutionStatus
    message: str
    filled_quantity: float = 0.0
    filled_amount: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def to_serializable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_serializable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_serializable(item) for key, item in value.items()}
    return value
```

- [ ] **Step 5: Run the model test**

Run: `pytest tests/test_models_import.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/stock_agent/__init__.py src/stock_agent/models.py tests/test_models_import.py
git commit -m "feat: add trading agent domain models"
```

## Task 2: Policy Loader

**Files:**
- Create: `src/stock_agent/policies/__init__.py`
- Create: `src/stock_agent/policies/investment.py`
- Test: `tests/test_policy.py`

- [ ] **Step 1: Write the failing policy test**

Create `tests/test_policy.py`:

```python
from pathlib import Path

from stock_agent.models import AssetType
from stock_agent.policies.investment import InvestmentPolicy, load_investment_policy


def test_policy_defaults_match_investment_philosophy():
    policy = InvestmentPolicy.default(Path("docs/investment-philosophy.md"))

    assert policy.allowed_asset_types == {AssetType.STOCK, AssetType.ETF, AssetType.VENTURE_FUND}
    assert policy.max_holdings == 10
    assert policy.max_single_stock_weight == 0.25
    assert policy.max_daily_buy_fraction == 0.10
    assert policy.requires_human_confirmation is True
    assert policy.allow_margin is False
    assert policy.allow_shorting is False
    assert "AI" in policy.focus_sectors


def test_load_policy_requires_existing_markdown():
    policy = load_investment_policy(Path("docs/investment-philosophy.md"))

    assert "Never use margin" in policy.markdown_text
```

- [ ] **Step 2: Run the policy test to verify it fails**

Run: `pytest tests/test_policy.py -v`

Expected: FAIL with missing `stock_agent.policies` module.

- [ ] **Step 3: Implement policy package exports**

Create `src/stock_agent/policies/__init__.py`:

```python
from stock_agent.policies.investment import InvestmentPolicy, load_investment_policy

__all__ = ["InvestmentPolicy", "load_investment_policy"]
```

- [ ] **Step 4: Implement the investment policy loader**

Create `src/stock_agent/policies/investment.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from stock_agent.models import AssetType


@dataclass(frozen=True)
class InvestmentPolicy:
    policy_path: Path
    markdown_text: str
    allowed_asset_types: set[AssetType]
    focus_sectors: set[str]
    max_holdings: int
    max_single_stock_weight: float
    max_daily_buy_fraction: float
    allow_margin: bool
    allow_shorting: bool
    requires_human_confirmation: bool

    @classmethod
    def default(cls, policy_path: Path, markdown_text: str = "") -> "InvestmentPolicy":
        return cls(
            policy_path=policy_path,
            markdown_text=markdown_text,
            allowed_asset_types={AssetType.STOCK, AssetType.ETF, AssetType.VENTURE_FUND},
            focus_sectors={"Energy", "Space technology", "Biotechnology", "AI"},
            max_holdings=10,
            max_single_stock_weight=0.25,
            max_daily_buy_fraction=0.10,
            allow_margin=False,
            allow_shorting=False,
            requires_human_confirmation=True,
        )


def load_investment_policy(policy_path: Path) -> InvestmentPolicy:
    if not policy_path.exists():
        raise FileNotFoundError(f"Investment policy not found: {policy_path}")
    markdown_text = policy_path.read_text(encoding="utf-8")
    return InvestmentPolicy.default(policy_path=policy_path, markdown_text=markdown_text)
```

- [ ] **Step 5: Run policy tests**

Run: `pytest tests/test_policy.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/stock_agent/policies tests/test_policy.py
git commit -m "feat: load investment policy"
```

## Task 3: Risk Agent

**Files:**
- Create: `src/stock_agent/agents/__init__.py`
- Create: `src/stock_agent/agents/risk.py`
- Test: `tests/test_risk_agent.py`

- [ ] **Step 1: Write failing risk tests**

Create `tests/test_risk_agent.py`:

```python
from pathlib import Path

from stock_agent.agents.risk import RiskAgent
from stock_agent.models import (
    Asset,
    AssetType,
    MarketSnapshot,
    PortfolioReview,
    PortfolioState,
    Position,
    TradeIntent,
    TradeSide,
)
from stock_agent.policies.investment import InvestmentPolicy


def make_policy():
    return InvestmentPolicy.default(Path("docs/investment-philosophy.md"))


def make_asset(symbol="PLTR", asset_type=AssetType.STOCK, sector="AI"):
    return Asset(symbol=symbol, asset_type=asset_type, sector=sector)


def make_market(asset, *, penny=False, leveraged=False):
    return MarketSnapshot(
        asset=asset,
        price=20.0,
        previous_close=22.0,
        drawdown_from_recent_high=-0.18,
        average_daily_volume=10_000_000,
        is_penny_stock=penny,
        is_leveraged_etf=leveraged,
        earnings_within_days=None,
    )


def make_portfolio(*, total=100_000.0, bought_today=0.0, margin=False, reconciled=True, positions=None):
    return PortfolioState(
        cash=50_000.0,
        positions=positions or [],
        total_account_value=total,
        margin_enabled=margin,
        reconciled=reconciled,
        buying_power=50_000.0,
        bought_value_today=bought_today,
    )


def make_intent(asset, *, side=TradeSide.BUY, amount=5_000.0, weight=0.05, uses_margin=False):
    return TradeIntent(
        asset=asset,
        side=side,
        proposed_amount=amount,
        proposed_weight=weight,
        time_horizon="long_term",
        strategy="quality_drawdown_mean_reversion",
        rationale="Temporary drawdown with no identified material deterioration.",
        signals={},
        uses_margin=uses_margin,
    )


def make_review(intent, *, holdings=1, weight=0.05):
    return PortfolioReview(intent=intent, holding_count_after_trade=holdings, post_trade_weight=weight)


def assert_blocked_for(decision, text):
    assert not decision.approved
    assert any(text in reason for reason in decision.reasons)


def test_blocks_short_trades():
    asset = make_asset()
    intent = make_intent(asset, side=TradeSide.SELL)
    decision = RiskAgent(make_policy()).evaluate(intent, make_review(intent), make_market(asset), make_portfolio())

    assert_blocked_for(decision, "Shorting is not allowed")


def test_blocks_margin_trades():
    asset = make_asset()
    intent = make_intent(asset, uses_margin=True)
    decision = RiskAgent(make_policy()).evaluate(intent, make_review(intent), make_market(asset), make_portfolio(margin=True))

    assert_blocked_for(decision, "Margin is not allowed")


def test_blocks_penny_stocks():
    asset = make_asset()
    intent = make_intent(asset)
    decision = RiskAgent(make_policy()).evaluate(intent, make_review(intent), make_market(asset, penny=True), make_portfolio())

    assert_blocked_for(decision, "Penny stocks are not allowed")


def test_blocks_leveraged_etfs():
    asset = make_asset(symbol="TQQQ", asset_type=AssetType.ETF)
    intent = make_intent(asset)
    decision = RiskAgent(make_policy()).evaluate(intent, make_review(intent), make_market(asset, leveraged=True), make_portfolio())

    assert_blocked_for(decision, "Leveraged ETFs are not allowed")


def test_blocks_buying_more_than_ten_percent_in_one_day():
    asset = make_asset()
    intent = make_intent(asset, amount=11_000.0)
    decision = RiskAgent(make_policy()).evaluate(intent, make_review(intent), make_market(asset), make_portfolio(total=100_000.0))

    assert_blocked_for(decision, "Daily buy limit exceeded")


def test_blocks_single_stock_weight_above_limit():
    asset = make_asset()
    intent = make_intent(asset, amount=5_000.0, weight=0.30)
    decision = RiskAgent(make_policy()).evaluate(intent, make_review(intent, weight=0.30), make_market(asset), make_portfolio())

    assert_blocked_for(decision, "Single-stock weight limit exceeded")


def test_blocks_more_than_ten_holdings():
    asset = make_asset()
    intent = make_intent(asset)
    decision = RiskAgent(make_policy()).evaluate(intent, make_review(intent, holdings=11), make_market(asset), make_portfolio())

    assert_blocked_for(decision, "Holding count limit exceeded")


def test_approves_trade_that_passes_hard_rules():
    asset = make_asset()
    intent = make_intent(asset)
    decision = RiskAgent(make_policy()).evaluate(intent, make_review(intent), make_market(asset), make_portfolio())

    assert decision.approved
    assert decision.reasons == []
```

- [ ] **Step 2: Run risk tests to verify they fail**

Run: `pytest tests/test_risk_agent.py -v`

Expected: FAIL with missing `stock_agent.agents` module.

- [ ] **Step 3: Add agent exports**

Create `src/stock_agent/agents/__init__.py`:

```python
"""Agent implementations for the paper trading scaffold."""
```

- [ ] **Step 4: Implement risk agent**

Create `src/stock_agent/agents/risk.py`:

```python
from __future__ import annotations

from stock_agent.models import (
    DecisionStatus,
    MarketSnapshot,
    PortfolioReview,
    PortfolioState,
    RiskDecision,
    TradeIntent,
    TradeSide,
)
from stock_agent.policies.investment import InvestmentPolicy


class RiskAgent:
    def __init__(self, policy: InvestmentPolicy) -> None:
        self.policy = policy

    def evaluate(
        self,
        intent: TradeIntent,
        portfolio_review: PortfolioReview,
        market: MarketSnapshot,
        portfolio: PortfolioState,
    ) -> RiskDecision:
        reasons: list[str] = []
        warnings: list[str] = list(portfolio_review.warnings)

        if intent.asset.asset_type not in self.policy.allowed_asset_types:
            reasons.append(f"Asset type is not allowed: {intent.asset.asset_type.value}")
        if not self.policy.allow_shorting and intent.side is TradeSide.SELL:
            reasons.append("Shorting is not allowed by the investment policy")
        if not self.policy.allow_margin and (intent.uses_margin or portfolio.margin_enabled):
            reasons.append("Margin is not allowed by the investment policy")
        if market.is_penny_stock:
            reasons.append("Penny stocks are not allowed by the investment policy")
        if market.is_leveraged_etf:
            reasons.append("Leveraged ETFs are not allowed by the investment policy")
        if not portfolio.reconciled:
            reasons.append("Account state is not reconciled")

        daily_buy_limit = portfolio.total_account_value * self.policy.max_daily_buy_fraction
        projected_bought_today = portfolio.bought_value_today
        if intent.side is TradeSide.BUY:
            projected_bought_today += intent.proposed_amount
        if projected_bought_today > daily_buy_limit:
            reasons.append(
                f"Daily buy limit exceeded: {projected_bought_today:.2f} > {daily_buy_limit:.2f}"
            )

        if portfolio_review.post_trade_weight > self.policy.max_single_stock_weight:
            reasons.append(
                "Single-stock weight limit exceeded: "
                f"{portfolio_review.post_trade_weight:.2%} > {self.policy.max_single_stock_weight:.2%}"
            )

        if portfolio_review.holding_count_after_trade > self.policy.max_holdings:
            reasons.append(
                f"Holding count limit exceeded: {portfolio_review.holding_count_after_trade} > {self.policy.max_holdings}"
            )

        status = DecisionStatus.REJECTED if reasons else DecisionStatus.APPROVED
        return RiskDecision(intent=intent, status=status, reasons=reasons, warnings=warnings)
```

- [ ] **Step 5: Run risk tests**

Run: `pytest tests/test_risk_agent.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/stock_agent/agents src/stock_agent/agents/risk.py tests/test_risk_agent.py
git commit -m "feat: enforce trading risk policy"
```

## Task 4: Portfolio, Confirmation, Execution, And Audit Agents

**Files:**
- Create: `src/stock_agent/agents/portfolio.py`
- Create: `src/stock_agent/agents/confirmation.py`
- Create: `src/stock_agent/agents/execution.py`
- Create: `src/stock_agent/agents/audit.py`
- Test: `tests/test_confirmation_execution.py`

- [ ] **Step 1: Write failing confirmation and execution tests**

Create `tests/test_confirmation_execution.py`:

```python
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
    assert "No tax lot impact identified" in review.tax_notes


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_confirmation_execution.py -v`

Expected: FAIL with missing agent modules.

- [ ] **Step 3: Implement portfolio agent**

Create `src/stock_agent/agents/portfolio.py`:

```python
from __future__ import annotations

from stock_agent.models import PortfolioReview, PortfolioState, TaxLot, TradeIntent, TradeSide
from stock_agent.policies.investment import InvestmentPolicy


class PortfolioAgent:
    def __init__(self, policy: InvestmentPolicy) -> None:
        self.policy = policy

    def review(
        self,
        intent: TradeIntent,
        portfolio: PortfolioState,
        tax_lots: list[TaxLot],
    ) -> PortfolioReview:
        existing = portfolio.position_for(intent.asset.symbol)
        new_position = existing is None and intent.side is TradeSide.BUY
        holding_count = len(portfolio.positions) + (1 if new_position else 0)

        current_value = existing.market_value if existing else 0.0
        post_trade_value = current_value
        if intent.side is TradeSide.BUY:
            post_trade_value += intent.proposed_amount
        else:
            post_trade_value = max(0.0, current_value - intent.proposed_amount)

        post_trade_weight = (
            post_trade_value / portfolio.total_account_value
            if portfolio.total_account_value > 0
            else 0.0
        )

        warnings: list[str] = []
        if intent.asset.sector not in self.policy.focus_sectors:
            warnings.append(f"Asset sector is outside focus sectors: {intent.asset.sector}")
        if holding_count == self.policy.max_holdings:
            warnings.append("Portfolio will be at the maximum holding count")

        tax_notes = self._tax_notes(intent, tax_lots)
        return PortfolioReview(
            intent=intent,
            holding_count_after_trade=holding_count,
            post_trade_weight=post_trade_weight,
            warnings=warnings,
            tax_notes=tax_notes,
        )

    def _tax_notes(self, intent: TradeIntent, tax_lots: list[TaxLot]) -> list[str]:
        matching_lots = [lot for lot in tax_lots if lot.asset.symbol == intent.asset.symbol]
        if intent.side is TradeSide.SELL and matching_lots:
            return ["Selling may realize taxable gains or losses; review tax lots before approval"]
        return ["No tax lot impact identified for this proposed trade"]
```

- [ ] **Step 4: Implement confirmation agent**

Create `src/stock_agent/agents/confirmation.py`:

```python
from __future__ import annotations

from stock_agent.models import HumanConfirmation, PortfolioReview, RiskDecision, TradeIntent


class FixedConfirmationAgent:
    def __init__(self, approved: bool, reviewer: str = "system", reason: str | None = None) -> None:
        self.approved = approved
        self.reviewer = reviewer
        self.reason = reason or ("approved" if approved else "rejected")

    def request(
        self,
        intent: TradeIntent,
        risk_decision: RiskDecision,
        portfolio_review: PortfolioReview | None,
    ) -> HumanConfirmation:
        return HumanConfirmation(
            intent=intent,
            approved=self.approved and risk_decision.approved,
            reviewer=self.reviewer,
            reason=self.reason,
        )


class CliConfirmationAgent:
    def request(
        self,
        intent: TradeIntent,
        risk_decision: RiskDecision,
        portfolio_review: PortfolioReview | None,
    ) -> HumanConfirmation:
        print("Trade confirmation required")
        print(f"Symbol: {intent.asset.symbol}")
        print(f"Side: {intent.side.value}")
        print(f"Amount: ${intent.proposed_amount:,.2f}")
        print(f"Weight: {intent.proposed_weight:.2%}")
        print(f"Rationale: {intent.rationale}")
        if portfolio_review is not None:
            print(f"Post-trade weight: {portfolio_review.post_trade_weight:.2%}")
            for warning in portfolio_review.warnings:
                print(f"Warning: {warning}")
            for tax_note in portfolio_review.tax_notes:
                print(f"Tax note: {tax_note}")
        for warning in risk_decision.warnings:
            print(f"Risk warning: {warning}")

        response = input("Type 'approve' to execute, anything else to reject: ").strip().lower()
        approved = response == "approve" and risk_decision.approved
        return HumanConfirmation(
            intent=intent,
            approved=approved,
            reviewer="human",
            reason="approved by human" if approved else "rejected by human or risk decision",
        )
```

- [ ] **Step 5: Implement execution agent and paper broker**

Create `src/stock_agent/agents/execution.py`:

```python
from __future__ import annotations

from stock_agent.models import ExecutionResult, ExecutionStatus, HumanConfirmation, RiskDecision, TradeIntent


class PaperBroker:
    def submit_order(self, intent: TradeIntent) -> ExecutionResult:
        if intent.proposed_amount <= 0:
            return ExecutionResult(
                intent=intent,
                status=ExecutionStatus.REJECTED,
                message="Order amount must be positive",
            )

        assumed_price = 100.0
        filled_quantity = intent.proposed_amount / assumed_price
        return ExecutionResult(
            intent=intent,
            status=ExecutionStatus.ACCEPTED,
            message="Paper order accepted",
            filled_quantity=filled_quantity,
            filled_amount=intent.proposed_amount,
        )


class ExecutionAgent:
    def __init__(self, broker: PaperBroker) -> None:
        self.broker = broker

    def execute(
        self,
        intent: TradeIntent,
        risk_decision: RiskDecision,
        confirmation: HumanConfirmation,
    ) -> ExecutionResult:
        if not risk_decision.approved:
            return ExecutionResult(
                intent=intent,
                status=ExecutionStatus.SKIPPED,
                message="Risk decision was not approved",
            )
        if not confirmation.approved:
            return ExecutionResult(
                intent=intent,
                status=ExecutionStatus.SKIPPED,
                message="Human confirmation was not approved",
            )
        if confirmation.intent != intent:
            return ExecutionResult(
                intent=intent,
                status=ExecutionStatus.REJECTED,
                message="Confirmation does not match trade intent",
            )
        return self.broker.submit_order(intent)
```

- [ ] **Step 6: Implement audit agent**

Create `src/stock_agent/agents/audit.py`:

```python
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
```

- [ ] **Step 7: Run confirmation and execution tests**

Run: `pytest tests/test_confirmation_execution.py -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/stock_agent/agents/portfolio.py src/stock_agent/agents/confirmation.py src/stock_agent/agents/execution.py src/stock_agent/agents/audit.py tests/test_confirmation_execution.py
git commit -m "feat: add portfolio confirmation execution and audit agents"
```

## Task 5: Data, Strategy, Orchestrator, And CLI

**Files:**
- Create: `src/stock_agent/agents/data.py`
- Create: `src/stock_agent/agents/strategy.py`
- Create: `src/stock_agent/orchestrator.py`
- Create: `src/stock_agent/run_once.py`
- Test: `tests/test_orchestrator.py`

- [ ] **Step 1: Write failing orchestrator tests**

Create `tests/test_orchestrator.py`:

```python
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
```

- [ ] **Step 2: Run orchestrator tests to verify they fail**

Run: `pytest tests/test_orchestrator.py -v`

Expected: FAIL with missing `stock_agent.orchestrator`.

- [ ] **Step 3: Implement mock data agent**

Create `src/stock_agent/agents/data.py`:

```python
from __future__ import annotations

from stock_agent.models import (
    Asset,
    AssetType,
    FundamentalSnapshot,
    MarketSnapshot,
    PortfolioState,
    TaxLot,
)


class DataAgent:
    def get_market_snapshots(self) -> list[MarketSnapshot]:
        asset = Asset(symbol="PLTR", asset_type=AssetType.STOCK, sector="AI", name="Palantir Technologies")
        return [
            MarketSnapshot(
                asset=asset,
                price=20.0,
                previous_close=22.0,
                drawdown_from_recent_high=-0.18,
                average_daily_volume=25_000_000,
                is_penny_stock=False,
                is_leveraged_etf=False,
                earnings_within_days=21,
            )
        ]

    def get_fundamentals(self) -> list[FundamentalSnapshot]:
        asset = Asset(symbol="PLTR", asset_type=AssetType.STOCK, sector="AI", name="Palantir Technologies")
        return [
            FundamentalSnapshot(
                asset=asset,
                quality_score=0.82,
                material_risk_detected=False,
                summary="High-quality AI-focused company with no material deterioration identified in mock data.",
            )
        ]

    def get_portfolio(self) -> PortfolioState:
        return PortfolioState(
            cash=50_000.0,
            positions=[],
            total_account_value=100_000.0,
            margin_enabled=False,
            reconciled=True,
            buying_power=50_000.0,
            bought_value_today=0.0,
        )

    def get_tax_lots(self) -> list[TaxLot]:
        return []
```

- [ ] **Step 4: Implement strategy agent**

Create `src/stock_agent/agents/strategy.py`:

```python
from __future__ import annotations

from stock_agent.models import FundamentalSnapshot, MarketSnapshot, TradeIntent, TradeSide
from stock_agent.policies.investment import InvestmentPolicy


class StrategyAgent:
    def __init__(self, policy: InvestmentPolicy) -> None:
        self.policy = policy

    def generate_intents(
        self,
        market_snapshots: list[MarketSnapshot],
        fundamentals: list[FundamentalSnapshot],
        account_value: float,
    ) -> list[TradeIntent]:
        fundamentals_by_symbol = {item.asset.symbol: item for item in fundamentals}
        intents: list[TradeIntent] = []

        for market in market_snapshots:
            fundamental = fundamentals_by_symbol.get(market.asset.symbol)
            if fundamental is None:
                continue
            if market.asset.sector not in self.policy.focus_sectors:
                continue
            if market.earnings_within_days is not None and market.earnings_within_days <= 7:
                continue
            if fundamental.material_risk_detected:
                continue
            if fundamental.quality_score < 0.7:
                continue
            if market.drawdown_from_recent_high > -0.10:
                continue

            proposed_amount = min(account_value * 0.05, account_value * self.policy.max_daily_buy_fraction)
            intents.append(
                TradeIntent(
                    asset=market.asset,
                    side=TradeSide.BUY,
                    proposed_amount=proposed_amount,
                    proposed_weight=proposed_amount / account_value,
                    time_horizon="long_term",
                    strategy="quality_drawdown_mean_reversion",
                    rationale=(
                        "Quality company in a focus sector with a temporary drawdown "
                        "and no identified material fundamental deterioration."
                    ),
                    signals={
                        "drawdown_from_recent_high": market.drawdown_from_recent_high,
                        "quality_score": fundamental.quality_score,
                        "earnings_within_days": market.earnings_within_days,
                        "fundamental_risk_detected": fundamental.material_risk_detected,
                    },
                )
            )

        return intents
```

- [ ] **Step 5: Implement orchestrator**

Create `src/stock_agent/orchestrator.py`:

```python
from __future__ import annotations

from pathlib import Path

from stock_agent.agents.audit import AuditAgent
from stock_agent.agents.confirmation import CliConfirmationAgent, FixedConfirmationAgent
from stock_agent.agents.data import DataAgent
from stock_agent.agents.execution import ExecutionAgent, PaperBroker
from stock_agent.agents.portfolio import PortfolioAgent
from stock_agent.agents.risk import RiskAgent
from stock_agent.agents.strategy import StrategyAgent
from stock_agent.models import ExecutionResult
from stock_agent.policies.investment import load_investment_policy


class TradingOrchestrator:
    def __init__(
        self,
        policy_path: Path,
        audit_path: Path,
        confirmation_agent: CliConfirmationAgent | FixedConfirmationAgent | None = None,
    ) -> None:
        self.policy = load_investment_policy(policy_path)
        self.data_agent = DataAgent()
        self.strategy_agent = StrategyAgent(self.policy)
        self.portfolio_agent = PortfolioAgent(self.policy)
        self.risk_agent = RiskAgent(self.policy)
        self.confirmation_agent = confirmation_agent or CliConfirmationAgent()
        self.execution_agent = ExecutionAgent(PaperBroker())
        self.audit_agent = AuditAgent(audit_path)

    def run_once(self) -> list[ExecutionResult]:
        portfolio = self.data_agent.get_portfolio()
        markets = self.data_agent.get_market_snapshots()
        fundamentals = self.data_agent.get_fundamentals()
        tax_lots = self.data_agent.get_tax_lots()
        markets_by_symbol = {market.asset.symbol: market for market in markets}

        intents = self.strategy_agent.generate_intents(
            market_snapshots=markets,
            fundamentals=fundamentals,
            account_value=portfolio.total_account_value,
        )

        results: list[ExecutionResult] = []
        for intent in intents:
            market = markets_by_symbol[intent.asset.symbol]
            portfolio_review = self.portfolio_agent.review(intent, portfolio, tax_lots)
            risk_decision = self.risk_agent.evaluate(intent, portfolio_review, market, portfolio)
            self.audit_agent.record(
                "risk",
                {
                    "intent": intent,
                    "portfolio_review": portfolio_review,
                    "risk_decision": risk_decision,
                },
            )

            confirmation = self.confirmation_agent.request(intent, risk_decision, portfolio_review)
            self.audit_agent.record("confirmation", {"confirmation": confirmation})

            result = self.execution_agent.execute(intent, risk_decision, confirmation)
            self.audit_agent.record("execution", {"execution_result": result})
            results.append(result)

        return results
```

- [ ] **Step 6: Implement CLI entrypoint**

Create `src/stock_agent/run_once.py`:

```python
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
```

- [ ] **Step 7: Run orchestrator tests**

Run: `pytest tests/test_orchestrator.py -v`

Expected: PASS.

- [ ] **Step 8: Run full test suite**

Run: `pytest -v`

Expected: PASS.

- [ ] **Step 9: Run the CLI smoke test**

Run: `printf 'reject\n' | python -m stock_agent.run_once`

Expected output includes: `skipped: Human confirmation was not approved`.

- [ ] **Step 10: Commit**

```bash
git add src/stock_agent/agents/data.py src/stock_agent/agents/strategy.py src/stock_agent/orchestrator.py src/stock_agent/run_once.py tests/test_orchestrator.py
git commit -m "feat: orchestrate mock trading cycle"
```

## Task 6: Final Verification

**Files:**
- Modify only if verification exposes a bug in files from Tasks 1-5.

- [ ] **Step 1: Run all tests**

Run: `pytest -v`

Expected: all tests pass.

- [ ] **Step 2: Run CLI approval path**

Run: `printf 'approve\n' | python -m stock_agent.run_once`

Expected output includes: `accepted: Paper order accepted`.

- [ ] **Step 3: Inspect audit output**

Run: `tail -n 3 logs/audit.jsonl`

Expected: three JSONL records for `risk`, `confirmation`, and `execution`.

- [ ] **Step 4: Check git status**

Run: `git status --short`

Expected: only intended source, test, plan, and audit-log changes are present. Do not add `.DS_Store`.

- [ ] **Step 5: Commit verification fixes if needed**

If a verification bug required code changes, commit them:

```bash
git add src tests
git commit -m "fix: stabilize trading agent scaffold"
```

If no fixes were required, do not create an empty commit.

## Self-Review

- Spec coverage: The plan implements typed models, policy loading, mock data, strategy generation, portfolio review, risk gates, human confirmation, paper execution, audit JSONL, CLI entrypoint, and tests.
- Completion scan: The plan contains concrete implementation and verification steps throughout.
- Type consistency: The same model names and fields are used across tests, agents, orchestrator, and CLI.
