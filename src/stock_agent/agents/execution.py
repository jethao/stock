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
