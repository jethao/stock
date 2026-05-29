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
