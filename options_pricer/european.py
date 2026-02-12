"""
European option pricing using Black-Scholes-Merton model.

Formulas with continuous dividend yield q:
    d1 = (ln(S/K) + (r - q + σ²/2)T) / (σ√T)
    d2 = d1 - σ√T
    C = S·e^(-qT)·N(d1) - K·e^(-rT)·N(d2)
    P = K·e^(-rT)·N(-d2) - S·e^(-qT)·N(-d1)
"""

import numpy as np
from scipy.stats import norm
from dataclasses import dataclass


@dataclass
class EuropeanGreeks:
    """Greeks for a European option."""
    delta: float
    gamma: float
    theta: float  # per day
    vega: float   # per 1% vol move
    rho: float    # per 1% rate move


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float, q: float = 0) -> tuple[float, float]:
    """Calculate d1 and d2 for Black-Scholes formula."""
    if T <= 0 or sigma <= 0:
        return np.nan, np.nan

    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    return d1, d2


def black_scholes(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0,
    option_type: str = "call"
) -> float:
    """
    Price a European option using Black-Scholes-Merton.

    Parameters
    ----------
    S : float
        Spot price of underlying
    K : float
        Strike price
    T : float
        Time to expiration in years
    r : float
        Risk-free interest rate (annualized)
    sigma : float
        Volatility (annualized)
    q : float, optional
        Continuous dividend yield (default 0)
    option_type : str
        "call" or "put"

    Returns
    -------
    float
        Option price
    """
    if T <= 0:
        # At expiration, return intrinsic value
        if option_type.lower() == "call":
            return max(S - K, 0)
        else:
            return max(K - S, 0)

    d1, d2 = _d1_d2(S, K, T, r, sigma, q)

    if np.isnan(d1):
        return np.nan

    discount = np.exp(-r * T)
    dividend_discount = np.exp(-q * T)

    if option_type.lower() == "call":
        return S * dividend_discount * norm.cdf(d1) - K * discount * norm.cdf(d2)
    else:
        return K * discount * norm.cdf(-d2) - S * dividend_discount * norm.cdf(-d1)


def european_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0,
    option_type: str = "call"
) -> EuropeanGreeks:
    """
    Calculate all Greeks for a European option.

    Parameters
    ----------
    S, K, T, r, sigma, q, option_type : same as black_scholes

    Returns
    -------
    EuropeanGreeks
        Dataclass with delta, gamma, theta, vega, rho
    """
    if T <= 0 or sigma <= 0:
        return EuropeanGreeks(
            delta=np.nan, gamma=np.nan, theta=np.nan, vega=np.nan, rho=np.nan
        )

    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    sqrt_T = np.sqrt(T)

    discount = np.exp(-r * T)
    dividend_discount = np.exp(-q * T)

    # N(d1), N(d2), n(d1) - CDF and PDF of standard normal
    N_d1 = norm.cdf(d1)
    N_d2 = norm.cdf(d2)
    n_d1 = norm.pdf(d1)

    # Gamma is the same for calls and puts
    gamma = dividend_discount * n_d1 / (S * sigma * sqrt_T)

    # Vega is the same for calls and puts (per 1% = 0.01 vol move)
    vega = S * dividend_discount * n_d1 * sqrt_T * 0.01

    if option_type.lower() == "call":
        delta = dividend_discount * N_d1
        theta = (
            -dividend_discount * S * n_d1 * sigma / (2 * sqrt_T)
            - r * K * discount * N_d2
            + q * S * dividend_discount * N_d1
        ) / 365  # per day
        rho = K * T * discount * N_d2 * 0.01  # per 1% rate move
    else:
        delta = dividend_discount * (N_d1 - 1)
        theta = (
            -dividend_discount * S * n_d1 * sigma / (2 * sqrt_T)
            + r * K * discount * norm.cdf(-d2)
            - q * S * dividend_discount * norm.cdf(-d1)
        ) / 365  # per day
        rho = -K * T * discount * norm.cdf(-d2) * 0.01  # per 1% rate move

    return EuropeanGreeks(
        delta=delta,
        gamma=gamma,
        theta=theta,
        vega=vega,
        rho=rho
    )


def put_call_parity_check(
    call_price: float,
    put_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    q: float = 0
) -> float:
    """
    Check put-call parity: C - P = S*e^(-qT) - K*e^(-rT)

    Returns the difference (should be ~0 for valid prices).
    """
    lhs = call_price - put_price
    rhs = S * np.exp(-q * T) - K * np.exp(-r * T)
    return lhs - rhs