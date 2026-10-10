"""
Unit tests for the shared P&L module and KellySizer's injected trade history.
"""

from types import SimpleNamespace

import pytest

from src.services.strategy_engine.pairs.position_sizer import (
    BOOTSTRAP_FRACTION,
    KellySizer,
)
from src.services.strategy_engine.pnl import legs_pnl, pair_pnl

pytestmark = [pytest.mark.unit, pytest.mark.trading]


class TestPairPnl:
    def test_long_spread_profit(self):
        # long 10 @100 -> 110 (+100), short 5 @200 -> 190 (+50)
        pnl, pct = pair_pnl("LONG_SPREAD", 10, 5, 100, 200, 110, 190)
        assert pnl == pytest.approx(150.0)
        assert pct == pytest.approx(150.0 / 2000 * 100)

    def test_short_spread_is_mirror_of_long(self):
        long_pnl, _ = pair_pnl("LONG_SPREAD", 10, 5, 100, 200, 110, 190)
        short_pnl, _ = pair_pnl("SHORT_SPREAD", 10, 5, 100, 200, 110, 190)
        assert short_pnl == pytest.approx(-long_pnl)

    def test_commission_deducted(self):
        pnl, _ = pair_pnl("LONG_SPREAD", 1, 1, 100, 100, 100, 100, commission=2.5)
        assert pnl == pytest.approx(-2.5)

    def test_pct_is_percentage_not_fraction(self):
        _, pct = pair_pnl("LONG_SPREAD", 1, 1, 100, 100, 101, 100)
        assert pct == pytest.approx(0.5)  # $1 on $200 cost = 0.5%


class TestLegsPnl:
    def test_basket_three_legs(self):
        legs = [(10, 50, 55), (-4, 100, 90), (-2, 25, 25)]
        pnl, pct = legs_pnl(legs)
        assert pnl == pytest.approx(50 + 40 + 0)
        assert pct == pytest.approx(90 / (500 + 400 + 50) * 100)

    def test_zero_cost_returns_zero_pct(self):
        assert legs_pnl([]) == (0.0, 0.0)


class TestKellySizerInjectedHistory:
    def _pair(self):
        return SimpleNamespace(symbol1="A", symbol2="B", max_allocation_pct=None)

    def test_bootstrap_with_few_trades_does_not_hit_db(self, monkeypatch):
        sizer = KellySizer(self._pair(), closed_trades=[])
        monkeypatch.setattr(
            sizer, "_load_closed_trades", lambda: pytest.fail("DB was queried")
        )
        assert sizer._compute_fraction() == BOOTSTRAP_FRACTION

    def test_bootstrap_splits_fraction_across_legs(self):
        sizer = KellySizer(self._pair(), closed_trades=[])
        qty1, qty2 = sizer.calculate_size(100_000, 100.0, 50.0)
        # 2% of 100k = 2,000 split across 2 legs -> 1,000 per leg
        assert (qty1, qty2) == (10, 20)

    def test_uses_injected_history_for_kelly(self):
        wins = [SimpleNamespace(pnl_pct=1.0)] * 15
        losses = [SimpleNamespace(pnl_pct=-0.5)] * 10
        sizer = KellySizer(self._pair(), closed_trades=wins + losses)
        # W=0.6, R=2 -> kelly=0.4, half=0.2 (within [0.01, 0.24])
        assert sizer._compute_fraction() == pytest.approx(0.2)
