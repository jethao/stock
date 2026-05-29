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
