"""
Implied volatility solver using Newton-Raphson with Brent's method fallback.
"""

import numpy as np
from scipy.optimize import brentq
from european import black_scholes, european_greeks
from american import binomial_tree


def implied_volatility(
    price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float = 0,
    option_type: str = "call",
    style: str = "european",
    tol: float = 1e-6,
    max_iter: int = 100
) -> float:
    """
    Solve for implied volatility given a market price.

    Uses Newton-Raphson with vega as derivative, falls back to Brent's
    method if NR fails to converge.

    Parameters
    ----------
    price : float
        Market price of the option
    S : float
        Spot price
    K : float
        Strike price
    T : float
        Time to expiration (years)
    r : float
        Risk-free rate (annualized)
    q : float, optional
        Continuous dividend yield (default 0)
    option_type : str
        "call" or "put"
    style : str
        "european" or "american"
    tol : float
        Convergence tolerance
    max_iter : int
        Maximum iterations for Newton-Raphson

    Returns
    -------
    float
        Implied volatility (annualized), or NaN if not found
    """
    # Validate inputs
    if price <= 0 or S <= 0 or K <= 0 or T <= 0:
        return np.nan

    # Check against intrinsic value
    if option_type.lower() == "call":
        intrinsic = max(S * np.exp(-q * T) - K * np.exp(-r * T), 0)
    else:
        intrinsic = max(K * np.exp(-r * T) - S * np.exp(-q * T), 0)

    if price < intrinsic - tol:
        # Price below intrinsic - arbitrage, no valid IV
        return np.nan

    if style.lower() == "european":
        return _iv_european(price, S, K, T, r, q, option_type, tol, max_iter)
    else:
        return _iv_american(price, S, K, T, r, q, option_type, tol, max_iter)


def _iv_european(price, S, K, T, r, q, option_type, tol, max_iter):
    """IV solver for European options using Newton-Raphson."""
    # Initial guess using Brenner-Subrahmanyam approximation
    sigma = np.sqrt(2 * np.pi / T) * price / S

    # Clamp to reasonable range
    sigma = max(0.01, min(sigma, 5.0))

    for _ in range(max_iter):
        model_price = black_scholes(S, K, T, r, sigma, q, option_type)
        diff = model_price - price

        if abs(diff) < tol:
            return sigma

        # Get vega for Newton step
        greeks = european_greeks(S, K, T, r, sigma, q, option_type)
        vega = greeks.vega * 100  # Convert from per 1% to per 100%

        if abs(vega) < 1e-10:
            break  # Vega too small, NR won't work

        sigma = sigma - diff / vega

        # Keep in reasonable bounds
        sigma = max(0.001, min(sigma, 10.0))

    # Newton-Raphson failed, try Brent's method
    return _iv_brent(price, S, K, T, r, q, option_type, "european", tol)


def _iv_american(price, S, K, T, r, q, option_type, tol, max_iter):
    """IV solver for American options using Brent's method (NR not practical)."""
    # American options: vega not easily available, use Brent's directly
    return _iv_brent(price, S, K, T, r, q, option_type, "american", tol)


def _iv_brent(price, S, K, T, r, q, option_type, style, tol):
    """Solve IV using Brent's method (bracketing)."""

    def objective(sigma):
        if style == "european":
            return black_scholes(S, K, T, r, sigma, q, option_type) - price
        else:
            return binomial_tree(S, K, T, r, sigma, q, option_type, steps=100) - price

    try:
        # Search in reasonable volatility range
        iv = brentq(objective, 0.001, 10.0, xtol=tol)
        return iv
    except ValueError:
        # No root in bracket - likely no valid IV
        return np.nan


def iv_chain(
    prices: np.ndarray,
    S: float,
    strikes: np.ndarray,
    T: float,
    r: float,
    q: float = 0,
    option_type: str = "call",
    style: str = "european"
) -> np.ndarray:
    """
    Calculate IV for multiple options (vectorized where possible).

    Parameters
    ----------
    prices : array
        Market prices
    S : float
        Spot price
    strikes : array
        Strike prices (same length as prices)
    T : float
        Time to expiration
    r, q, option_type, style : same as implied_volatility

    Returns
    -------
    array
        Implied volatilities
    """
    ivs = np.zeros(len(prices))
    for i, (price, K) in enumerate(zip(prices, strikes)):
        ivs[i] = implied_volatility(price, S, K, T, r, q, option_type, style)
    return ivs