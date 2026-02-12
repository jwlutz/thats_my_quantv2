"""
American option pricing using:
1. Cox-Ross-Rubinstein binomial tree (exact)
2. Barone-Adesi-Whaley quadratic approximation (fast)
"""

import numpy as np
from scipy.stats import norm
from european import black_scholes, _d1_d2


def binomial_tree(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0,
    option_type: str = "call",
    steps: int = 100
) -> float:
    """
    Price an American option using Cox-Ross-Rubinstein binomial tree.

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
    steps : int
        Number of time steps (more = more accurate but slower)

    Returns
    -------
    float
        American option price
    """
    if T <= 0:
        if option_type.lower() == "call":
            return max(S - K, 0)
        else:
            return max(K - S, 0)

    dt = T / steps
    u = np.exp(sigma * np.sqrt(dt))  # up factor
    d = 1 / u                         # down factor
    p = (np.exp((r - q) * dt) - d) / (u - d)  # risk-neutral probability

    discount = np.exp(-r * dt)

    # Build price tree at maturity
    prices = S * (u ** np.arange(steps, -1, -1)) * (d ** np.arange(0, steps + 1, 1))

    # Option values at maturity
    if option_type.lower() == "call":
        values = np.maximum(prices - K, 0)
    else:
        values = np.maximum(K - prices, 0)

    # Backward induction
    for i in range(steps - 1, -1, -1):
        prices = S * (u ** np.arange(i, -1, -1)) * (d ** np.arange(0, i + 1, 1))

        # Continuation value
        continuation = discount * (p * values[:-1] + (1 - p) * values[1:])

        # Early exercise value
        if option_type.lower() == "call":
            exercise = np.maximum(prices - K, 0)
        else:
            exercise = np.maximum(K - prices, 0)

        # American: take max of exercise and continuation
        values = np.maximum(continuation, exercise)

    return values[0]


def baw_american(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0,
    option_type: str = "call"
) -> float:
    """
    Price American option using Barone-Adesi-Whaley quadratic approximation.

    Fast approximation (~0.1% error vs binomial with 500 steps).

    Reference: Barone-Adesi & Whaley (1987)
    "Efficient Analytic Approximation of American Option Values"

    Parameters
    ----------
    S, K, T, r, sigma, q, option_type : same as binomial_tree

    Returns
    -------
    float
        American option price (approximation)
    """
    if T <= 0:
        if option_type.lower() == "call":
            return max(S - K, 0)
        else:
            return max(K - S, 0)

    # Get European price first
    european_price = black_scholes(S, K, T, r, sigma, q, option_type)

    # Special case: no early exercise benefit for call without dividends
    if option_type.lower() == "call" and q == 0:
        return european_price

    # BAW parameters
    sigma_sq = sigma ** 2
    h = 1 - np.exp(-r * T)

    # Calculate M, N, K_prime
    M = 2 * r / sigma_sq
    N = 2 * (r - q) / sigma_sq
    K_prime = 1 - np.exp(-r * T)

    if option_type.lower() == "call":
        # For calls
        q1 = (-(N - 1) + np.sqrt((N - 1)**2 + 4 * M / K_prime)) / 2

        if q1 <= 0:
            return european_price

        # Find critical price S* using Newton-Raphson
        S_star = _find_critical_price_call(K, T, r, sigma, q, q1)

        if S < S_star:
            d1, _ = _d1_d2(S_star, K, T, r, sigma, q)
            A1 = (S_star / q1) * (1 - np.exp(-q * T) * norm.cdf(d1))
            return european_price + A1 * (S / S_star) ** q1
        else:
            return S - K  # Exercise immediately
    else:
        # For puts
        q2 = (-(N - 1) - np.sqrt((N - 1)**2 + 4 * M / K_prime)) / 2

        if q2 >= 0:
            return european_price

        # Find critical price S* using Newton-Raphson
        S_star = _find_critical_price_put(K, T, r, sigma, q, q2)

        if S > S_star:
            d1, _ = _d1_d2(S_star, K, T, r, sigma, q)
            A2 = -(S_star / q2) * (1 - np.exp(-q * T) * norm.cdf(-d1))
            return european_price + A2 * (S / S_star) ** q2
        else:
            return K - S  # Exercise immediately


def _find_critical_price_call(K, T, r, sigma, q, q1, tol=1e-6, max_iter=100):
    """Find critical stock price S* for American call using Newton-Raphson."""
    # Initial guess
    S_star = K

    for _ in range(max_iter):
        d1, _ = _d1_d2(S_star, K, T, r, sigma, q)

        bs_price = black_scholes(S_star, K, T, r, sigma, q, "call")
        intrinsic = S_star - K

        # LHS - RHS of critical price equation
        lhs = bs_price + (1 - np.exp(-q * T) * norm.cdf(d1)) * S_star / q1
        rhs = intrinsic

        diff = lhs - rhs

        if abs(diff) < tol:
            break

        # Derivative for Newton-Raphson
        dividend_discount = np.exp(-q * T)
        n_d1 = norm.pdf(d1)
        sqrt_T = np.sqrt(T)

        delta = dividend_discount * norm.cdf(d1)
        d_lhs = delta + (1 - dividend_discount * norm.cdf(d1)) / q1 + \
                dividend_discount * n_d1 * S_star / (q1 * sigma * sqrt_T * S_star)
        d_rhs = 1

        deriv = d_lhs - d_rhs

        if abs(deriv) < 1e-10:
            break

        S_star = S_star - diff / deriv
        S_star = max(S_star, K * 0.01)  # Keep positive

    return S_star


def _find_critical_price_put(K, T, r, sigma, q, q2, tol=1e-6, max_iter=100):
    """Find critical stock price S* for American put using Newton-Raphson."""
    # Initial guess
    S_star = K

    for _ in range(max_iter):
        d1, _ = _d1_d2(S_star, K, T, r, sigma, q)

        bs_price = black_scholes(S_star, K, T, r, sigma, q, "put")
        intrinsic = K - S_star

        # LHS - RHS of critical price equation
        lhs = bs_price - (1 - np.exp(-q * T) * norm.cdf(-d1)) * S_star / q2
        rhs = intrinsic

        diff = lhs - rhs

        if abs(diff) < tol:
            break

        # Derivative for Newton-Raphson
        dividend_discount = np.exp(-q * T)
        n_d1 = norm.pdf(d1)
        sqrt_T = np.sqrt(T)

        delta = dividend_discount * (norm.cdf(d1) - 1)
        d_lhs = delta - (1 - dividend_discount * norm.cdf(-d1)) / q2 - \
                dividend_discount * n_d1 * S_star / (q2 * sigma * sqrt_T * S_star)
        d_rhs = -1

        deriv = d_lhs - d_rhs

        if abs(deriv) < 1e-10:
            break

        S_star = S_star - diff / deriv
        S_star = max(S_star, K * 0.01)  # Keep positive

    return S_star