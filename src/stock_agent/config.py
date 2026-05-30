from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


class ConfigurationError(ValueError):
    """Raised when runtime configuration is missing or unsafe."""


@dataclass(frozen=True)
class DataProviderConfig:
    provider: str
    api_key: str | None = None
    secret_key: str | None = None
    symbols: list[str] | None = None
    paper: bool = True

    def __post_init__(self) -> None:
        if self.symbols is None:
            object.__setattr__(self, "symbols", [])


def load_data_provider_config(env: Mapping[str, str] | None = None) -> DataProviderConfig:
    values = env or os.environ
    provider = values.get("STOCK_AGENT_DATA_PROVIDER", "mock").strip().lower()

    if provider == "mock":
        return DataProviderConfig(provider="mock")

    if provider != "alpaca":
        raise ConfigurationError(f"Unsupported data provider: {provider}")

    api_key = values.get("ALPACA_API_KEY", "").strip()
    secret_key = values.get("ALPACA_SECRET_KEY", "").strip()
    symbols = _parse_symbols(values.get("ALPACA_SYMBOLS", ""))
    paper = values.get("ALPACA_PAPER", "true").strip().lower() not in {"0", "false", "no"}

    missing: list[str] = []
    if not api_key:
        missing.append("ALPACA_API_KEY")
    if not secret_key:
        missing.append("ALPACA_SECRET_KEY")
    if not symbols:
        missing.append("ALPACA_SYMBOLS")
    if missing:
        raise ConfigurationError(f"Missing Alpaca configuration: {', '.join(missing)}")

    return DataProviderConfig(
        provider="alpaca",
        api_key=api_key,
        secret_key=secret_key,
        symbols=symbols,
        paper=paper,
    )


def _parse_symbols(raw_symbols: str) -> list[str]:
    return [symbol.strip().upper() for symbol in raw_symbols.split(",") if symbol.strip()]
