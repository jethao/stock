from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from stock_agent.models import AssetType


@dataclass(frozen=True)
class InvestmentPolicy:
    policy_path: Path
    markdown_text: str
    allowed_asset_types: set[AssetType]
    focus_sectors: set[str]
    max_holdings: int
    max_single_stock_weight: float
    max_daily_buy_fraction: float
    allow_margin: bool
    allow_shorting: bool
    requires_human_confirmation: bool

    @classmethod
    def default(cls, policy_path: Path, markdown_text: str = "") -> "InvestmentPolicy":
        return cls(
            policy_path=policy_path,
            markdown_text=markdown_text,
            allowed_asset_types={AssetType.STOCK, AssetType.ETF, AssetType.VENTURE_FUND},
            focus_sectors={"Energy", "Space technology", "Biotechnology", "AI"},
            max_holdings=10,
            max_single_stock_weight=0.25,
            max_daily_buy_fraction=0.10,
            allow_margin=False,
            allow_shorting=False,
            requires_human_confirmation=True,
        )


def load_investment_policy(policy_path: Path) -> InvestmentPolicy:
    if not policy_path.exists():
        raise FileNotFoundError(f"Investment policy not found: {policy_path}")
    markdown_text = policy_path.read_text(encoding="utf-8")
    return InvestmentPolicy.default(policy_path=policy_path, markdown_text=markdown_text)
