from datetime import datetime, timezone
from types import SimpleNamespace

from stock_agent.agents.alpaca_data import AlpacaDataAgent
from stock_agent.config import DataProviderConfig
from stock_agent.models import AssetType


class FakeTradingClient:
    def get_account(self):
        return SimpleNamespace(cash="12500.50", equity="25000.00", buying_power="18000.00")

    def get_all_positions(self):
        return [
            SimpleNamespace(
                symbol="PLTR",
                asset_class="us_equity",
                qty="10",
                market_value="200.00",
                avg_entry_price="15.00",
            )
        ]


class FakeBar:
    def __init__(self, close, high=None):
        self.close = close
        self.high = high if high is not None else close
        self.timestamp = datetime.now(timezone.utc)


class FakeBarSet:
    def __init__(self, data):
        self.data = data


class FakeStockDataClient:
    def get_stock_bars(self, request):
        return FakeBarSet(
            {
                "PLTR": [FakeBar(24.0, 25.0), FakeBar(20.0, 21.0)],
                "NVDA": [FakeBar(900.0, 1000.0), FakeBar(850.0, 880.0)],
            }
        )


def make_agent(symbols=None):
    config = DataProviderConfig(
        provider="alpaca",
        api_key="key",
        secret_key="secret",
        symbols=symbols or ["PLTR", "NVDA"],
        symbol_sectors={"PLTR": "AI", "NVDA": "AI"},
        paper=True,
    )
    return AlpacaDataAgent(
        config=config,
        trading_client=FakeTradingClient(),
        stock_data_client=FakeStockDataClient(),
    )


def test_alpaca_data_agent_maps_account_to_portfolio_state():
    portfolio = make_agent().get_portfolio()

    assert portfolio.cash == 12500.50
    assert portfolio.total_account_value == 25000.00
    assert portfolio.buying_power == 18000.00
    assert portfolio.margin_enabled is False
    assert portfolio.reconciled is True


def test_alpaca_data_agent_maps_positions():
    portfolio = make_agent().get_portfolio()

    assert len(portfolio.positions) == 1
    position = portfolio.positions[0]
    assert position.asset.symbol == "PLTR"
    assert position.asset.asset_type is AssetType.STOCK
    assert position.asset.sector == "AI"
    assert position.quantity == 10.0
    assert position.market_price == 20.0
    assert position.cost_basis == 15.0


def test_alpaca_data_agent_maps_bars_to_market_snapshots():
    snapshots = make_agent().get_market_snapshots()

    by_symbol = {snapshot.asset.symbol: snapshot for snapshot in snapshots}
    assert by_symbol["PLTR"].price == 20.0
    assert by_symbol["PLTR"].asset.sector == "AI"
    assert by_symbol["PLTR"].previous_close == 24.0
    assert by_symbol["PLTR"].drawdown_from_recent_high == -0.20
    assert by_symbol["PLTR"].is_penny_stock is False
    assert by_symbol["PLTR"].is_leveraged_etf is False


def test_alpaca_data_agent_returns_interim_fundamentals_for_symbols():
    fundamentals = make_agent(symbols=["PLTR"]).get_fundamentals()

    assert len(fundamentals) == 1
    assert fundamentals[0].asset.symbol == "PLTR"
    assert fundamentals[0].quality_score == 0.75
    assert fundamentals[0].material_risk_detected is False
    assert "No external fundamentals provider" in fundamentals[0].summary


def test_alpaca_data_agent_returns_empty_tax_lots():
    assert make_agent().get_tax_lots() == []
