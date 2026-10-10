"""
Boundary Optimizer - Minimum Profit Optimization for pairs trading.

Research/backtest tool. Given the AR(1) parameters of a pair's spread
(the same phi fitted for half-life in discovery/stats.py), finds
the entry z-score boundary U that maximizes expected profit rate:

    expected_profit_rate(U) = U / (trade_duration(U) + inter_trade_interval(U))

Trade duration and inter-trade interval are the mean first-passage times
of the stationary AR(1) spread process, following Lin, McCrae & Gulati
(2006) and Puspaningrum, Lin & Gulati (2010). Not used in live trading -
output is a suggested entry_threshold for PairRegistry, reviewed and set
manually or via backtest tooling.
"""

from dataclasses import dataclass
from typing import Callable, Optional, cast

import numpy as np
import numpy.typing as npt
from scipy import optimize


@dataclass
class BoundaryResult:
    """Optimal entry boundary and the expected trade economics behind it."""

    boundary: float  # optimal U, in z-score / sigma_eq units
    expected_profit_rate: float  # U / (duration + interval), per bar
    trade_duration: float  # bars, mean first-passage time U -> mean
    inter_trade_interval: float  # bars, mean first-passage time mean -> U


def _stationary_std(phi: float, sigma_a: float) -> float:
    """Stationary standard deviation of a mean-zero AR(1) process."""
    return float(sigma_a / np.sqrt(1 - phi**2))


def _mean_first_passage_time(
    start: float,
    target_offset_fn: Callable[[npt.NDArray[np.float64]], npt.NDArray[np.bool_]],
    phi: float,
    sigma_a: float,
    n_grid: int = 200,
) -> float:
    """
    Approximate mean first-passage time via the discretized integral equation
    from Puspaningrum et al. (2010):

        E[T(s)] = integral_{-inf}^{inf} E[T(s')] * phi_pdf(s' | s) ds' + 1

    Solved on a bounded grid [-bound, bound] by linear system, since the
    AR(1) transition kernel decays fast (Gaussian innovations).
    """
    sigma_eq = _stationary_std(phi, sigma_a)
    bound = 6 * sigma_eq
    grid = cast(npt.NDArray[np.float64], np.linspace(-bound, bound, n_grid))
    dx = grid[1] - grid[0]

    # Transition density: s' | s ~ N(phi*s, sigma_a^2)
    def kernel_row(s: float) -> npt.NDArray[np.float64]:
        density = np.exp(-((grid - phi * s) ** 2) / (2 * sigma_a**2)) / (
            np.sqrt(2 * np.pi) * sigma_a
        )
        return cast(npt.NDArray[np.float64], density * dx)

    target_mask = target_offset_fn(grid)

    A = np.eye(n_grid)
    b = np.ones(n_grid)
    for i, s in enumerate(grid):
        if target_mask[i]:
            # Absorbing: passage already occurred, T = 0 contribution beyond entry
            A[i, i] = 1.0
            b[i] = 0.0
        else:
            A[i, :] -= kernel_row(s)

    T = np.linalg.solve(A, b)
    idx = np.argmin(np.abs(grid - start))
    return float(T[idx])


def trade_duration(u: float, phi: float, sigma_a: float) -> float:
    """Mean first-passage time from U back to the mean (0)."""

    def reached_mean(grid: npt.NDArray[np.float64]) -> npt.NDArray[np.bool_]:
        return cast(npt.NDArray[np.bool_], np.abs(grid) < (grid[1] - grid[0]))

    return _mean_first_passage_time(u, reached_mean, phi, sigma_a)


def inter_trade_interval(u: float, phi: float, sigma_a: float) -> float:
    """Mean first-passage time from the mean (0) out to U."""

    def reached_u(grid: npt.NDArray[np.float64]) -> npt.NDArray[np.bool_]:
        return grid >= u

    return _mean_first_passage_time(0.0, reached_u, phi, sigma_a)


def expected_profit_rate(u: float, phi: float, sigma_a: float) -> float:
    """
    Expected profit per bar for boundary U: minimum profit per trade (U,
    per Lin et al. 2006) divided by the full trade cycle duration.
    """
    if u <= 0:
        return 0.0
    duration = trade_duration(u, phi, sigma_a)
    interval = inter_trade_interval(u, phi, sigma_a)
    cycle = duration + interval
    if cycle <= 0:
        return 0.0
    return u / cycle


def optimize_boundary(
    phi: float,
    sigma_a: float,
    u_min: Optional[float] = None,
    u_max: Optional[float] = None,
) -> BoundaryResult:
    """
    Find the entry boundary U (in raw spread units) maximizing expected
    profit rate, per the minimum-profit-optimization framework.

    Args:
        phi:     AR(1) coefficient of the spread, |phi| < 1 (mean-reverting).
                 Same fit as half_life in discovery/stats.py, via
                 phi = 1 + beta from compute_half_life's OLS regression.
        sigma_a: Residual (innovation) std dev from that same OLS fit
                 (model.resid.std()).
        u_min:   Lower search bound. Defaults to 0.1 * stationary std.
        u_max:   Upper search bound. Defaults to 3 * stationary std.

    Returns:
        BoundaryResult with the optimal U and its expected trade economics.
    """
    if not (0 < phi < 1):
        raise ValueError(
            f"phi must be in (0, 1) for a mean-reverting spread, got {phi}"
        )
    if sigma_a <= 0:
        raise ValueError(f"sigma_a must be positive, got {sigma_a}")

    sigma_eq = _stationary_std(phi, sigma_a)
    lo = u_min if u_min is not None else 0.1 * sigma_eq
    hi = u_max if u_max is not None else 3.0 * sigma_eq

    neg_rate = lambda u: -expected_profit_rate(u, phi, sigma_a)  # noqa: E731
    result = optimize.minimize_scalar(  # type: ignore[call-overload]
        neg_rate, bounds=(lo, hi), method="bounded"
    )

    u_star = float(result.x)
    duration = trade_duration(u_star, phi, sigma_a)
    interval = inter_trade_interval(u_star, phi, sigma_a)

    return BoundaryResult(
        boundary=u_star,
        expected_profit_rate=-float(result.fun),
        trade_duration=duration,
        inter_trade_interval=interval,
    )
