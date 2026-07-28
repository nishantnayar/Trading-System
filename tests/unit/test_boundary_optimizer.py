"""
Unit tests for boundary_optimizer.

Pure numerical module - no DB, no network. Verifies the minimum-profit
optimization behaves as the theory predicts: faster mean reversion (lower
phi) yields shorter trade cycles and higher expected profit rate; invalid
AR(1) parameters raise rather than silently returning garbage.
"""

import pytest

from src.services.strategy_engine.pairs.boundary_optimizer import (
    BoundaryResult,
    expected_profit_rate,
    inter_trade_interval,
    optimize_boundary,
    trade_duration,
)


@pytest.mark.unit
@pytest.mark.trading
class TestOptimizeBoundary:
    def test_returns_boundary_result(self):
        result = optimize_boundary(phi=0.9, sigma_a=0.2)
        assert isinstance(result, BoundaryResult)

    def test_boundary_is_positive(self):
        result = optimize_boundary(phi=0.9, sigma_a=0.2)
        assert result.boundary > 0

    def test_boundary_within_search_bounds(self):
        result = optimize_boundary(phi=0.9, sigma_a=0.2, u_min=0.05, u_max=1.0)
        assert 0.05 <= result.boundary <= 1.0

    def test_faster_reversion_gives_shorter_cycle(self):
        """Lower phi (faster mean reversion) should produce a shorter
        expected trade cycle (duration + interval) than a slower-reverting
        spread with the same innovation variance - matches CLAUDE.md's
        long-half-life-compresses-tradeability note."""
        fast = optimize_boundary(phi=0.80, sigma_a=0.2)
        slow = optimize_boundary(phi=0.98, sigma_a=0.2)
        fast_cycle = fast.trade_duration + fast.inter_trade_interval
        slow_cycle = slow.trade_duration + slow.inter_trade_interval
        assert fast_cycle < slow_cycle

    def test_invalid_phi_raises(self):
        with pytest.raises(ValueError):
            optimize_boundary(phi=1.0, sigma_a=0.2)

    def test_negative_phi_raises(self):
        with pytest.raises(ValueError):
            optimize_boundary(phi=-0.1, sigma_a=0.2)

    def test_zero_sigma_raises(self):
        with pytest.raises(ValueError):
            optimize_boundary(phi=0.9, sigma_a=0.0)

    def test_negative_sigma_raises(self):
        with pytest.raises(ValueError):
            optimize_boundary(phi=0.9, sigma_a=-0.1)


@pytest.mark.unit
@pytest.mark.trading
class TestExpectedProfitRate:
    def test_zero_boundary_gives_zero_rate(self):
        assert expected_profit_rate(u=0.0, phi=0.9, sigma_a=0.2) == 0.0

    def test_negative_boundary_gives_zero_rate(self):
        assert expected_profit_rate(u=-0.5, phi=0.9, sigma_a=0.2) == 0.0

    def test_positive_boundary_gives_positive_rate(self):
        assert expected_profit_rate(u=0.3, phi=0.9, sigma_a=0.2) > 0.0


@pytest.mark.unit
@pytest.mark.trading
class TestFirstPassageTimes:
    def test_trade_duration_positive(self):
        assert trade_duration(u=0.3, phi=0.9, sigma_a=0.2) > 0

    def test_inter_trade_interval_positive(self):
        assert inter_trade_interval(u=0.3, phi=0.9, sigma_a=0.2) > 0

    def test_larger_boundary_increases_inter_trade_interval(self):
        """A wider boundary should take longer, on average, for the spread
        to reach from the mean - matches slide 25's tighter/looser
        boundary tradeoff (fewer, larger-profit trades)."""
        near = inter_trade_interval(u=0.2, phi=0.9, sigma_a=0.2)
        far = inter_trade_interval(u=0.6, phi=0.9, sigma_a=0.2)
        assert far > near
