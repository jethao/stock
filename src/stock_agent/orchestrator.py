from __future__ import annotations

from pathlib import Path
from typing import Any

from stock_agent.agents.audit import AuditAgent
from stock_agent.agents.alpaca_data import AlpacaDataAgent
from stock_agent.agents.confirmation import CliConfirmationAgent, FixedConfirmationAgent
from stock_agent.agents.data import DataAgent
from stock_agent.agents.execution import ExecutionAgent, PaperBroker
from stock_agent.agents.portfolio import PortfolioAgent
from stock_agent.agents.risk import RiskAgent
from stock_agent.agents.strategy import StrategyAgent
from stock_agent.config import load_data_provider_config
from stock_agent.models import ExecutionResult
from stock_agent.policies.investment import load_investment_policy


class TradingOrchestrator:
    def __init__(
        self,
        policy_path: Path,
        audit_path: Path,
        confirmation_agent: CliConfirmationAgent | FixedConfirmationAgent | None = None,
        data_agent: Any | None = None,
    ) -> None:
        self.policy = load_investment_policy(policy_path)
        self.data_agent = data_agent or self._build_data_agent()
        self.strategy_agent = StrategyAgent(self.policy)
        self.portfolio_agent = PortfolioAgent(self.policy)
        self.risk_agent = RiskAgent(self.policy)
        self.confirmation_agent = confirmation_agent or CliConfirmationAgent()
        self.execution_agent = ExecutionAgent(PaperBroker())
        self.audit_agent = AuditAgent(audit_path)

    def _build_data_agent(self) -> Any:
        config = load_data_provider_config()
        if config.provider == "alpaca":
            return AlpacaDataAgent(config)
        return DataAgent()

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
