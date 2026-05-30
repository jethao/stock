import pytest

from stock_agent.run_once import main


def test_run_once_reports_configuration_errors_without_traceback(monkeypatch, capsys):
    monkeypatch.setenv("STOCK_AGENT_DATA_PROVIDER", "alpaca")
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SYMBOLS", raising=False)

    with pytest.raises(SystemExit) as exc:
        main()

    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert "Configuration error:" in captured.err
    assert "ALPACA_API_KEY" in captured.err
