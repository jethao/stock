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
