# Alpaca Data Agent Design

## Goal

Replace the current hardcoded mock market/account data path with an optional Alpaca-backed data provider while preserving the existing paper-trading safety flow: strategy, portfolio review, risk checks, human confirmation, paper execution, and audit logging.

The implementation must keep mock data available for tests and offline development. Alpaca must be opt-in through environment configuration.

## Scope

In scope:

- Add Alpaca as an optional dependency.
- Add environment-based runtime configuration.
- Add an Alpaca data agent that returns existing domain models:
  - `PortfolioState`
  - `Position`
  - `MarketSnapshot`
  - `FundamentalSnapshot`
  - `TaxLot`
- Update the orchestrator to choose mock or Alpaca data based on config.
- Add tests that mock Alpaca SDK clients and do not call the network.
- Keep existing paper execution and risk behavior unchanged.

Out of scope:

- Live order execution through Alpaca.
- Replacing the existing `PaperBroker`.
- Streaming real-time data.
- Full company fundamentals from Alpaca.
- SEC EDGAR or FMP fundamentals integration.
- Tax-lot retrieval beyond returning an empty list when unavailable.

## Runtime Configuration

The provider is selected by environment variables:

- `STOCK_AGENT_DATA_PROVIDER=mock` uses the current mock data path.
- `STOCK_AGENT_DATA_PROVIDER=alpaca` uses Alpaca.
- `ALPACA_API_KEY` is required for Alpaca.
- `ALPACA_SECRET_KEY` is required for Alpaca.
- `ALPACA_PAPER=true` uses Alpaca paper trading endpoints.
- `ALPACA_SYMBOLS=PLTR,NVDA` defines the symbol universe to evaluate.

If Alpaca is selected and required credentials or symbols are missing, the orchestrator must fail closed before producing trade intents.

## Alpaca Data Mapping

The Alpaca data agent will use `alpaca-py`:

- `TradingClient` for account state and open positions.
- `StockHistoricalDataClient` for stock bars.
- `StockLatestTradeRequest` or recent bars for current price.
- `StockBarsRequest` for recent bars used to calculate drawdown.

Mapping into domain models:

- Account equity becomes `PortfolioState.total_account_value`.
- Account cash becomes `PortfolioState.cash`.
- Account buying power becomes `PortfolioState.buying_power`.
- Open positions become `Position` records.
- Symbols from `ALPACA_SYMBOLS` become candidate `Asset` records.
- Latest price and recent bar history become `MarketSnapshot` records.
- Drawdown is calculated as `(latest_price - recent_high) / recent_high`.
- Penny-stock detection is `latest_price < 5.00`.
- Leveraged ETF detection is conservative and name/symbol based for v1.

## Fundamentals Behavior

Alpaca is not treated as a fundamentals provider. For v1, the Alpaca data agent will produce conservative interim `FundamentalSnapshot` records for the configured symbol universe:

- `quality_score=0.75`
- `material_risk_detected=False`
- `summary` states that no external fundamentals provider is connected yet.

This preserves the current strategy interface without pretending to have real fundamentals. A later SEC EDGAR or FMP data agent should replace this interim behavior.

## Error Handling

The Alpaca data path fails closed:

- Missing env vars raise a configuration error.
- Empty symbol list raises a configuration error.
- Alpaca client errors raise a data-provider error.
- Missing price data for a symbol skips that symbol and records a warning.
- No market snapshots means the orchestrator returns no execution results.

No broker order is submitted as part of data fetching.

## Testing

Tests will:

- Verify config defaults to mock.
- Verify Alpaca config requires credentials and symbols.
- Verify mocked Alpaca account data maps to `PortfolioState`.
- Verify mocked positions map to `Position`.
- Verify mocked bars map to `MarketSnapshot`.
- Verify orchestrator can select the Alpaca data agent without calling real network clients.
- Verify existing mock workflow and risk tests still pass.

## Acceptance Criteria

The implementation is complete when:

- Existing tests pass.
- New Alpaca data-agent tests pass without network calls.
- `STOCK_AGENT_DATA_PROVIDER=mock python -m stock_agent.run_once` keeps existing mock behavior.
- `STOCK_AGENT_DATA_PROVIDER=alpaca` fails closed with a clear error when required env vars are missing.
- No Alpaca credentials are committed.
- The existing draft PR branch is updated with the change.
