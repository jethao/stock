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
