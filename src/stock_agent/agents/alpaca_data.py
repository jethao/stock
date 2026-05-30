from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

from stock_agent.config import DataProviderConfig
from stock_agent.models import (
    Asset,
    AssetType,
    FundamentalSnapshot,
    MarketSnapshot,
    PortfolioState,
    Position,
    TaxLot,
)


class AlpacaDataError(RuntimeError):
    """Raised when Alpaca data cannot be mapped into agent state."""


class AlpacaDataAgent:
    def __init__(
        self,
        config: DataProviderConfig,
        trading_client: Any | None = None,
        stock_data_client: Any | None = None,
    ) -> None:
        self.config = config
        self.symbols = config.symbols or []
        self.trading_client = trading_client or self._build_trading_client(config)
        self.stock_data_client = stock_data_client or self._build_stock_data_client(config)

    def get_market_snapshots(self) -> list[MarketSnapshot]:
        bars_by_symbol = self._get_bars_by_symbol()
        snapshots: list[MarketSnapshot] = []
        for symbol in self.symbols:
            bars = bars_by_symbol.get(symbol, [])
            if len(bars) < 2:
                continue
            previous_bar = bars[-2]
            latest_bar = bars[-1]
            latest_price = _as_float(latest_bar.close)
            recent_high = max(_as_float(getattr(bar, "high", bar.close)) for bar in bars)
            drawdown = ((latest_price - recent_high) / recent_high) if recent_high > 0 else 0.0

            snapshots.append(
                MarketSnapshot(
                    asset=self._asset_for(symbol),
                    price=latest_price,
                    previous_close=_as_float(previous_bar.close),
                    drawdown_from_recent_high=round(drawdown, 4),
                    average_daily_volume=0,
                    is_penny_stock=latest_price < 5.0,
                    is_leveraged_etf=_looks_like_leveraged_etf(symbol),
                    earnings_within_days=None,
                    timestamp=getattr(latest_bar, "timestamp", datetime.now(timezone.utc)),
                )
            )
        return snapshots

    def get_fundamentals(self) -> list[FundamentalSnapshot]:
        return [
            FundamentalSnapshot(
                asset=self._asset_for(symbol),
                quality_score=0.75,
                material_risk_detected=False,
                summary="No external fundamentals provider connected yet; using interim Alpaca symbol coverage only.",
            )
            for symbol in self.symbols
        ]

    def get_portfolio(self) -> PortfolioState:
        account = self.trading_client.get_account()
        positions = self._get_positions()
        return PortfolioState(
            cash=_as_float(account.cash),
            positions=positions,
            total_account_value=_as_float(account.equity),
            margin_enabled=False,
            reconciled=True,
            buying_power=_as_float(account.buying_power),
            bought_value_today=0.0,
        )

    def get_tax_lots(self) -> list[TaxLot]:
        return []

    def _get_positions(self) -> list[Position]:
        positions: list[Position] = []
        for raw_position in self.trading_client.get_all_positions():
            quantity = _as_float(raw_position.qty)
            market_value = _as_float(raw_position.market_value)
            market_price = market_value / quantity if quantity else 0.0
            positions.append(
                Position(
                    asset=self._asset_for(raw_position.symbol),
                    quantity=quantity,
                    market_price=market_price,
                    cost_basis=_as_float(raw_position.avg_entry_price),
                )
            )
        return positions

    def _get_bars_by_symbol(self) -> dict[str, list[Any]]:
        request = self._build_bars_request()
        response = self.stock_data_client.get_stock_bars(request)
        return getattr(response, "data", response)

    def _build_bars_request(self) -> Any:
        try:
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame
        except ImportError:
            return SimpleNamespace(
                symbol_or_symbols=self.symbols,
                start=datetime.now(timezone.utc) - timedelta(days=45),
                timeframe="1Day",
            )

        return StockBarsRequest(
            symbol_or_symbols=self.symbols,
            timeframe=TimeFrame.Day,
            start=datetime.now(timezone.utc) - timedelta(days=45),
        )

    def _asset_for(self, symbol: str) -> Asset:
        return Asset(symbol=symbol.upper(), asset_type=AssetType.STOCK, sector="Unknown")

    @staticmethod
    def _build_trading_client(config: DataProviderConfig) -> Any:
        try:
            from alpaca.trading.client import TradingClient
        except ImportError as exc:
            raise AlpacaDataError("alpaca-py is required for Alpaca data provider") from exc
        return TradingClient(config.api_key, config.secret_key, paper=config.paper)

    @staticmethod
    def _build_stock_data_client(config: DataProviderConfig) -> Any:
        try:
            from alpaca.data.historical import StockHistoricalDataClient
        except ImportError as exc:
            raise AlpacaDataError("alpaca-py is required for Alpaca data provider") from exc
        return StockHistoricalDataClient(config.api_key, config.secret_key)


def _as_float(value: Any) -> float:
    return float(value)


def _looks_like_leveraged_etf(symbol: str) -> bool:
    leveraged_symbols = {
        "TQQQ",
        "SQQQ",
        "UPRO",
        "SPXU",
        "SOXL",
        "SOXS",
        "TECL",
        "TECS",
        "FNGU",
        "FNGD",
    }
    return symbol.upper() in leveraged_symbols
