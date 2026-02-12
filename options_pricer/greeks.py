"""
Unified Greeks interface for both European and American options.
"""

import numpy as np
from dataclasses import dataclass
from european import european_greeks, EuropeanGreeks
from american import binomial_tree


@dataclass
class GreeksResult:
    """Greeks for any option (European or American)."""
    delta: float
    gamma: float
    theta: float  # per day
    vega: float   # per 1% vol move
    rho: float    # per 1% rate move
    style: str    # "european" or "american"


def greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0,
    option_type: str = "call",
    style: str = "european"
) -> GreeksResult:
    """
    Calculate all Greeks for an option.

    For European options, uses analytical formulas.
    For American options, uses finite difference on binomial tree.

    Parameters
    ----------
    S : float
        Spot price
    K : float
        Strike price
    T : float
        Time to expiration (years)
    r : float
        Risk-free rate (annualized)
    sigma : float
        Volatility (annualized)
    q : float, optional
        Continuous dividend yield (default 0)
    option_type : str
        "call" or "put"
    style : str
        "european" or "american"

    Returns
    -------
    GreeksResult
        Dataclass with delta, gamma, theta, vega, rho, style
    """
    if style.lower() == "european":
        eu_greeks = european_greeks(S, K, T, r, sigma, q, option_type)
        return GreeksResult(
            delta=eu_greeks.delta,
            gamma=eu_greeks.gamma,
            theta=eu_greeks.theta,
            vega=eu_greeks.vega,
            rho=eu_greeks.rho,
            style="european"
        )
    else:
        # American: use finite difference on binomial tree
        return _american_greeks_fd(S, K, T, r, sigma, q, option_type)


def _american_greeks_fd(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float,
    option_type: str,
    steps: int = 200
) -> GreeksResult:
    """
    Calculate American Greeks using finite difference.

    Uses central difference where possible, forward/backward at boundaries.
    """
    # Bumps for finite difference
    dS = S * 0.01       # 1% spot bump
    dsigma = 0.01       # 1% vol bump (absolute)
    dr = 0.0001         # 1bp rate bump
    dT = 1/365          # 1 day time bump

    # Base price
    V = binomial_tree(S, K, T, r, sigma, q, option_type, steps)

    # Delta: dV/dS
    V_up = binomial_tree(S + dS, K, T, r, sigma, q, option_type, steps)
    V_down = binomial_tree(S - dS, K, T, r, sigma, q, option_type, steps)
    delta = (V_up - V_down) / (2 * dS)

    # Gamma: d²V/dS²
    gamma = (V_up - 2*V + V_down) / (dS ** 2)

    # Theta: -dV/dT (per day)
    if T > dT:
        V_T_down = binomial_tree(S, K, T - dT, r, sigma, q, option_type, steps)
        theta = (V_T_down - V) / dT / 365  # Already in "per day"
    else:
        theta = np.nan

    # Vega: dV/dsigma (per 1% vol)
    V_sigma_up = binomial_tree(S, K, T, r, sigma + dsigma, q, option_type, steps)
    V_sigma_down = binomial_tree(S, K, T, r, sigma - dsigma, q, option_type, steps)
    vega = (V_sigma_up - V_sigma_down) / 2  # per 1% (since dsigma = 0.01)

    # Rho: dV/dr (per 1% rate)
    V_r_up = binomial_tree(S, K, T, r + dr, sigma, q, option_type, steps)
    V_r_down = binomial_tree(S, K, T, r - dr, sigma, q, option_type, steps)
    rho = (V_r_up - V_r_down) / 2 * 100  # per 1% (dr was 1bp, scale to 1%)

    return GreeksResult(
        delta=delta,
        gamma=gamma,
        theta=theta,
        vega=vega,
        rho=rho,
        style="american"
    )