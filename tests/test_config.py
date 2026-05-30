import pytest

from stock_agent.config import ConfigurationError, load_data_provider_config


def test_config_defaults_to_mock_provider(monkeypatch):
    monkeypatch.delenv("STOCK_AGENT_DATA_PROVIDER", raising=False)

    config = load_data_provider_config()

    assert config.provider == "mock"
    assert config.symbols == []


def test_config_parses_alpaca_symbols_and_credentials(monkeypatch):
    monkeypatch.setenv("STOCK_AGENT_DATA_PROVIDER", "alpaca")
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.setenv("ALPACA_SYMBOLS", " PLTR, nvda ,,TSLA ")
    monkeypatch.setenv("ALPACA_PAPER", "false")

    config = load_data_provider_config()

    assert config.provider == "alpaca"
    assert config.api_key == "key"
    assert config.secret_key == "secret"
    assert config.symbols == ["PLTR", "NVDA", "TSLA"]
    assert config.paper is False


def test_alpaca_config_requires_credentials(monkeypatch):
    monkeypatch.setenv("STOCK_AGENT_DATA_PROVIDER", "alpaca")
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
    monkeypatch.setenv("ALPACA_SYMBOLS", "PLTR")

    with pytest.raises(ConfigurationError, match="ALPACA_API_KEY"):
        load_data_provider_config()


def test_alpaca_config_requires_symbols(monkeypatch):
    monkeypatch.setenv("STOCK_AGENT_DATA_PROVIDER", "alpaca")
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.delenv("ALPACA_SYMBOLS", raising=False)

    with pytest.raises(ConfigurationError, match="ALPACA_SYMBOLS"):
        load_data_provider_config()


def test_config_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("STOCK_AGENT_DATA_PROVIDER", "other")

    with pytest.raises(ConfigurationError, match="Unsupported data provider"):
        load_data_provider_config()
