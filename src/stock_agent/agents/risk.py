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
