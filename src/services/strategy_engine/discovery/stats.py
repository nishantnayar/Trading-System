"""
Statistical tests used by pair and basket discovery.

All functions are pure (no DB access).
"""

from typing import List, Tuple, cast

import numpy as np
import pandas as pd


def compute_log_returns(prices: pd.Series) -> pd.Series:
    """Compute log returns from a price series."""
    return cast(pd.Series, np.log(prices).diff().dropna())


def pearson_correlation(s1: pd.Series, s2: pd.Series) -> float:
    """Pearson correlation of log returns on the aligned series."""
    r1 = compute_log_returns(s1)
    r2 = compute_log_returns(s2)
    aligned = pd.concat([r1, r2], axis=1).dropna()
    if len(aligned) < 30:
        return 0.0
    return float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))


def engle_granger_cointegration(s1: pd.Series, s2: pd.Series) -> Tuple[float, float]:
    """
    Run Engle-Granger cointegration test on log prices.
    Returns (p_value, hedge_ratio).
    hedge_ratio is the OLS beta from regressing log(s1) on log(s2).
    """
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tools import add_constant
    from statsmodels.tsa.stattools import coint

    log_s1 = np.log(s1)
    log_s2 = np.log(s2)
    aligned = pd.concat([log_s1, log_s2], axis=1).dropna()
    if len(aligned) < 60:
        return 1.0, 1.0

    y = aligned.iloc[:, 0].values
    x = aligned.iloc[:, 1].values

    # OLS hedge ratio
    x_const = add_constant(x)
    model = OLS(y, x_const).fit()
    hedge_ratio = float(model.params[1])

    # Engle-Granger test (tests residuals for stationarity)
    _, p_value, _ = coint(y, x)

    return float(p_value), hedge_ratio


def compute_half_life(spread: pd.Series) -> float:
    """
    Compute mean-reversion half-life via AR(1) on delta-spread.
    half_life = -log(2) / log(1 + beta_ar1)  in same units as the series index.
    Returns inf if the series is not mean-reverting.
    """
    half_life, _beta, _sigma_a = compute_half_life_and_ar1(spread)
    return half_life


def compute_half_life_and_ar1(spread: pd.Series) -> Tuple[float, float, float]:
    """
    Compute mean-reversion half-life and the underlying AR(1) fit.
    half_life = -log(2) / log(1 + beta_ar1)  in same units as the series index.

    Returns:
        (half_life, beta, sigma_a) where beta is the OLS slope of
        delta-spread on lagged spread (AR(1) coefficient phi = 1 + beta),
        and sigma_a is the residual std dev of that regression - both
        feed src.services.strategy_engine.pairs.boundary_optimizer.
        Returns (inf, 0.0, 0.0) if the series is not mean-reverting or
        has insufficient data.
    """
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tools import add_constant

    spread = spread.dropna()
    if len(spread) < 30:
        return float("inf"), 0.0, 0.0

    delta = spread.diff().dropna()
    lagged = spread.shift(1).dropna()

    # Align
    aligned = pd.concat([delta, lagged], axis=1).dropna()
    if len(aligned) < 20:
        return float("inf"), 0.0, 0.0

    y = aligned.iloc[:, 0].values
    x = add_constant(aligned.iloc[:, 1].values)
    model = OLS(y, x).fit()
    beta = float(model.params[1])

    if beta >= 0:
        # Not mean-reverting
        return float("inf"), beta, float(model.resid.std())

    half_life = -np.log(2) / np.log(1 + beta)
    return float(half_life), beta, float(model.resid.std())


def johansen_cointegration(
    prices_df: pd.DataFrame,
) -> Tuple[float, List[float]]:
    """
    Run Johansen cointegration test on log prices of N assets.

    Returns (min_pvalue, hedge_weights) where:
      - min_pvalue is the trace statistic p-value for the r=0 hypothesis
        (i.e. probability of seeing this trace statistic if no cointegration)
      - hedge_weights is the first cointegrating eigenvector, normalized so
        weights[0] = 1.0  (sign is flipped if weights[0] < 0)
    """
    from statsmodels.tsa.vector_ar.vecm import coint_johansen

    log_prices: pd.DataFrame = prices_df.dropna().apply(np.log)
    if len(log_prices) < 60:
        return 1.0, [1.0] * len(prices_df.columns)

    result = coint_johansen(log_prices, det_order=0, k_ar_diff=1)

    # trace_stat_crit_vals shape: (num_assets, 3) for 10%, 5%, 1% crit values
    # cvt: critical values for trace statistic
    # lr1: trace statistics
    trace_stat = result.lr1[0]
    crit_val_5pct = result.cvt[0, 1]

    # Approximate p-value: 0.01 if stat > 1% crit, 0.05 if > 5%, else 0.10+
    # statsmodels does not give exact p-values for Johansen; use conservative approx.
    crit_1pct = result.cvt[0, 2]
    if trace_stat > crit_1pct:
        p_value = 0.01
    elif trace_stat > crit_val_5pct:
        p_value = 0.05
    else:
        p_value = 0.15

    # First eigenvector = fastest mean-reverting cointegrating combination
    evec = result.evec[:, 0]

    # Normalize so first weight = 1.0, flip sign if needed
    if evec[0] < 0:
        evec = -evec
    evec = evec / evec[0]

    return float(p_value), [float(w) for w in evec]


def compute_basket_spread(
    prices_df: pd.DataFrame,
    hedge_weights: List[float],
) -> pd.Series:
    """
    Compute basket spread: spread = sum(w_i * log(P_i)) for each row.
    Drops rows where any price is missing.
    """
    log_prices: pd.DataFrame = prices_df.dropna().apply(np.log)
    weights = np.array(hedge_weights)
    spread = log_prices.values @ weights
    return pd.Series(np.asarray(spread, dtype=float), index=log_prices.index, name="spread")


def compute_min_pairwise_correlation(prices_df: pd.DataFrame) -> float:
    """Minimum Pearson correlation on log returns across all pairs in the basket."""
    log_returns = cast(pd.DataFrame, np.log(prices_df)).diff().dropna()
    cols = log_returns.columns.tolist()
    min_corr = 1.0
    for i, c1 in enumerate(cols):
        for c2 in cols[i + 1 :]:
            c = float(log_returns[c1].corr(log_returns[c2]))
            if c < min_corr:
                min_corr = c
    return min_corr
