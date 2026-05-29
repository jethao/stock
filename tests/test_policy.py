from pathlib import Path

from stock_agent.models import AssetType
from stock_agent.policies.investment import InvestmentPolicy, load_investment_policy


def test_policy_defaults_match_investment_philosophy():
    policy = InvestmentPolicy.default(Path("docs/investment-philosophy.md"))

    assert policy.allowed_asset_types == {AssetType.STOCK, AssetType.ETF, AssetType.VENTURE_FUND}
    assert policy.max_holdings == 10
    assert policy.max_single_stock_weight == 0.25
    assert policy.max_daily_buy_fraction == 0.10
    assert policy.requires_human_confirmation is True
    assert policy.allow_margin is False
    assert policy.allow_shorting is False
    assert "AI" in policy.focus_sectors


def test_load_policy_requires_existing_markdown():
    policy = load_investment_policy(Path("docs/investment-philosophy.md"))

    assert "Never use margin" in policy.markdown_text
