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
