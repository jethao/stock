from pathlib import Path

from stock_agent.agents.risk import RiskAgent
from stock_agent.models import (
    Asset,
    AssetType,
    MarketSnapshot,
    PortfolioReview,
    PortfolioState,
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
