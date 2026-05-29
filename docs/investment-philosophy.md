# Investment Philosophy

This document defines the investment philosophy and execution constraints for the trading agent. The agent must load and apply this policy before every portfolio-building, signal-generation, risk-management, and execution cycle.

## 1. Portfolio Builder

### Tradable Assets

Allowed asset classes:

- Stocks
- ETFs
- Venture funds, when available through an approved platform and suitable for the account

Disallowed assets:

- Penny stocks
- Leveraged ETFs
- Instruments requiring margin
- Instruments that create short exposure
- Assets the broker or account cannot clearly support

### Sector Focus

The portfolio should prioritize companies and funds connected to:

- Energy
- Space technology
- Biotechnology
- Artificial intelligence

The agent may consider assets outside these sectors only when they improve portfolio quality, diversification, or risk control, and only with explicit human confirmation.

### Long-Term Holding Preference

For long-term holdings, favor companies with:

- Breakthrough technology
- An inspiring mission
- Strong founders or founder-led culture
- Durable long-term compounding potential
- Evidence of execution quality

The agent should prefer businesses with meaningful technological or strategic differentiation over short-term price momentum alone.

## 2. Trigger Signals

The agent should look for opportunities where a quality company appears to be temporarily mispriced.

Preferred signals:

- Quality companies experiencing temporary drawdowns
- No identified material fundamental deterioration based on available data
- Mean reversion opportunities after apparent market overreaction
- Long-term compounding potential that remains intact
- Price weakness caused by sentiment, liquidity, or short-term noise rather than business impairment

Avoid:

- Trading around earnings announcements
- Trades driven only by short-term noise
- Trades where the drawdown appears connected to material fundamental risk
- Trades where the agent cannot explain the thesis in plain language

The agent should prefer long-term compounding over short-term trading frequency.

## 3. Portfolio Construction

The portfolio should be concentrated but controlled.

Rules:

- Rebalance weekly, not intraday
- Hold no more than 10 positions
- Allocate no more than 25% of total account value to a single stock
- Avoid unnecessary turnover
- Keep position sizing consistent with conviction, liquidity, and risk limits
- Consider tax implications before rebalancing or realizing gains or losses

If the portfolio already has 10 holdings, the agent must recommend a replacement or rebalance rather than adding an additional holding.

## 4. Risk Management

Hard rules:

- Never use margin
- Never short
- Never buy more than 10% of total account value in one trading day
- Never trade penny stocks
- Never trade leveraged ETFs
- Never execute if account state, position state, or market data cannot be reconciled
- Never execute if the human confirmation step has not completed

Risk checks must happen after trade intent generation and before order creation. Any hard-rule violation must block execution.

Soft review items:

- Sector concentration
- Liquidity concerns
- Thesis uncertainty
- Unusual volatility
- News-driven price action
- Existing exposure to correlated assets

Soft review items should be escalated to the human reviewer with a clear explanation, but they do not automatically block execution unless they conflict with a hard rule.

## 5. Human Confirmation

The agent must always request human confirmation before execution.

No order may be submitted to a broker, including a paper broker, unless the human reviewer explicitly approves the proposed trade.

Each confirmation request must include:

- Symbol or asset name
- Asset type
- Proposed side
- Proposed dollar amount
- Proposed portfolio weight
- Reason for the trade
- Relevant signal summary
- Risk checks passed
- Risk warnings, if any
- Expected effect on portfolio concentration

Human confirmation can approve, reject, or request changes. Any changed trade must be rechecked by the risk-management layer before execution.

## 6. Execution Policy

Execution is allowed only when all of the following are true:

- The asset is allowed by this policy
- The signal is consistent with this policy
- Portfolio construction limits are satisfied
- Risk-management hard rules are satisfied
- Human confirmation has been received
- The broker/account state has been reconciled
- The order details match the approved trade

If any condition fails, the agent must not execute the trade. It should record the reason in the audit log and present the issue for human review.

## 7. Audit Requirements

For every proposed trade, the agent must log:

- Timestamp
- Input data snapshot references
- Signal rationale
- Portfolio state before the trade
- Risk checks and outcomes
- Human confirmation result
- Final execution decision
- Broker response, if an order is submitted

Rejected trades should be logged with the same rigor as approved trades.
