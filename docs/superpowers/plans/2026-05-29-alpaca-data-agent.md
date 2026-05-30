# Alpaca Data Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in Alpaca-backed data provider that replaces hardcoded market/account data while keeping mock data, paper execution, risk gates, human confirmation, and audit logging intact.

**Architecture:** Keep `DataAgent` as the mock provider and add a separate `AlpacaDataAgent` that maps Alpaca account, positions, and bars into existing dataclasses. Add a small `config.py` factory so `TradingOrchestrator` selects mock or Alpaca from environment variables.

**Tech Stack:** Python 3.11+, dataclasses, alpaca-py 0.43.x, pytest with mocked SDK clients.

---

## File Structure

- Modify `pyproject.toml`: add `alpaca-py>=0.43,<0.44`.
- Create `src/stock_agent/config.py`: environment parsing and provider selection.
- Create `src/stock_agent/agents/alpaca_data.py`: Alpaca-backed data provider.
- Modify `src/stock_agent/orchestrator.py`: accept optional data agent and config-selected default.
- Create `tests/test_config.py`: config parsing tests.
- Create `tests/test_alpaca_data_agent.py`: mocked Alpaca data mapping tests.
- Modify `tests/test_orchestrator.py`: provider selection test.

## Tasks

- [ ] Write config tests for default mock provider, Alpaca credential requirements, symbol parsing, and invalid provider rejection.
- [ ] Implement `DataProviderConfig`, `ConfigurationError`, and `load_data_provider_config`.
- [ ] Write Alpaca mapping tests using fake account, position, and bar objects.
- [ ] Implement `AlpacaDataAgent` with injectable clients for tests and lazy SDK imports for runtime.
- [ ] Update orchestrator to accept injected data agents and select Alpaca when configured.
- [ ] Add `alpaca-py` dependency and install it in the local venv.
- [ ] Run `pytest` and CLI smoke tests for mock behavior and Alpaca fail-closed behavior.
- [ ] Commit and push updates to the existing fork branch.

## Verification

- `.venv/bin/python -m pytest -v` passes.
- `STOCK_AGENT_DATA_PROVIDER=mock printf 'reject\n' | .venv/bin/python -m stock_agent.run_once` keeps mock behavior.
- `STOCK_AGENT_DATA_PROVIDER=alpaca .venv/bin/python -m stock_agent.run_once` fails with a clear missing credentials error when Alpaca env vars are absent.
- No API keys or secrets are written to files.
