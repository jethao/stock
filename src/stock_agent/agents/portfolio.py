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
