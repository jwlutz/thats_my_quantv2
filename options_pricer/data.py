"""
Live options data integration via yfinance.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import yfinance as yf

from european import black_scholes
from american import binomial_tree
from implied_vol import implied_volatility


@dataclass
class OptionChain:
    """Container for options chain data."""
    ticker: str
    spot_price: float
    expirations: list[str]
    calls: pd.DataFrame
    puts: pd.DataFrame
    fetched_at: datetime


@dataclass
class ValidationResult:
    """Results from model vs market validation."""
    ticker: str
    spot: float
    risk_free_rate: float
    comparison: pd.DataFrame
    mean_abs_error: float
    european_vs_american_diff: float


def fetch_option_chain(ticker: str, expiration: Optional[str] = None) -> OptionChain:
    """
    Fetch live options chain from yfinance.

    Parameters
    ----------
    ticker : str
        Stock ticker (e.g., "AAPL")
    expiration : str, optional
        Specific expiration date (YYYY-MM-DD). If None, uses nearest.

    Returns
    -------
    OptionChain
        Dataclass with calls, puts, expirations, spot price
    """
    stock = yf.Ticker(ticker)

    # Get available expirations
    expirations = list(stock.options)

    if not expirations:
        raise ValueError(f"No options data available for {ticker}")

    # Select expiration
    if expiration is None:
        selected_exp = expirations[0]  # Nearest
    else:
        if expiration not in expirations:
            raise ValueError(f"Expiration {expiration} not available. Choose from: {expirations[:5]}...")
        selected_exp = expiration

    # Fetch chain
    chain = stock.option_chain(selected_exp)

    # Get spot price
    spot = stock.info.get('regularMarketPrice') or stock.info.get('currentPrice')
    if spot is None:
        # Fallback to last close
        hist = stock.history(period="1d")
        spot = hist['Close'].iloc[-1] if len(hist) > 0 else np.nan

    return OptionChain(
        ticker=ticker,
        spot_price=spot,
        expirations=expirations,
        calls=chain.calls,
        puts=chain.puts,
        fetched_at=datetime.now()
    )


def validate_against_market(
    ticker: str,
    expiration: Optional[str] = None,
    risk_free_rate: float = 0.05,
    dividend_yield: float = 0.0
) -> ValidationResult:
    """
    Compare model prices to live market prices.

    Parameters
    ----------
    ticker : str
        Stock ticker
    expiration : str, optional
        Specific expiration date
    risk_free_rate : float
        Risk-free rate to use in models (default 5%)
    dividend_yield : float
        Continuous dividend yield (default 0)

    Returns
    -------
    ValidationResult
        Comparison DataFrame and summary statistics
    """
    chain = fetch_option_chain(ticker, expiration)
    S = chain.spot_price
    r = risk_free_rate
    q = dividend_yield

    # Calculate time to expiration
    if expiration is None:
        exp_date = chain.expirations[0]
    else:
        exp_date = expiration

    exp_datetime = datetime.strptime(exp_date, "%Y-%m-%d")
    T = (exp_datetime - datetime.now()).days / 365.0
    T = max(T, 1/365)  # At least 1 day

    results = []

    # Process calls
    for _, row in chain.calls.iterrows():
        K = row['strike']
        market_price = row.get('lastPrice', np.nan)
        market_iv = row.get('impliedVolatility', np.nan)

        if pd.isna(market_price) or market_price <= 0:
            continue

        # Use market IV if available, else solve for it
        if pd.isna(market_iv) or market_iv <= 0:
            sigma = implied_volatility(market_price, S, K, T, r, q, "call", "european")
        else:
            sigma = market_iv

        if np.isnan(sigma):
            continue

        # Model prices
        eu_price = black_scholes(S, K, T, r, sigma, q, "call")
        am_price = binomial_tree(S, K, T, r, sigma, q, "call", steps=100)

        error_pct = abs(eu_price - market_price) / market_price * 100 if market_price > 0 else np.nan

        results.append({
            'type': 'call',
            'strike': K,
            'market_price': market_price,
            'european_price': eu_price,
            'american_price': am_price,
            'error_pct': error_pct,
            'iv_market': market_iv,
            'iv_model': sigma,
            'moneyness': S / K
        })

    # Process puts
    for _, row in chain.puts.iterrows():
        K = row['strike']
        market_price = row.get('lastPrice', np.nan)
        market_iv = row.get('impliedVolatility', np.nan)

        if pd.isna(market_price) or market_price <= 0:
            continue

        if pd.isna(market_iv) or market_iv <= 0:
            sigma = implied_volatility(market_price, S, K, T, r, q, "put", "european")
        else:
            sigma = market_iv

        if np.isnan(sigma):
            continue

        eu_price = black_scholes(S, K, T, r, sigma, q, "put")
        am_price = binomial_tree(S, K, T, r, sigma, q, "put", steps=100)

        error_pct = abs(eu_price - market_price) / market_price * 100 if market_price > 0 else np.nan

        results.append({
            'type': 'put',
            'strike': K,
            'market_price': market_price,
            'european_price': eu_price,
            'american_price': am_price,
            'error_pct': error_pct,
            'iv_market': market_iv,
            'iv_model': sigma,
            'moneyness': S / K
        })

    df = pd.DataFrame(results)

    # Summary statistics
    mean_abs_error = df['error_pct'].mean() if len(df) > 0 else np.nan
    eu_am_diff = (df['american_price'] - df['european_price']).mean() if len(df) > 0 else np.nan

    return ValidationResult(
        ticker=ticker,
        spot=S,
        risk_free_rate=r,
        comparison=df,
        mean_abs_error=mean_abs_error,
        european_vs_american_diff=eu_am_diff
    )


def get_risk_free_rate() -> float:
    """
    Get current risk-free rate estimate.

    Uses 3-month Treasury yield as proxy. Falls back to hardcoded value.

    Returns
    -------
    float
        Annualized risk-free rate
    """
    try:
        # Try to get 3-month Treasury
        tbill = yf.Ticker("^IRX")  # 13-week Treasury Bill
        hist = tbill.history(period="1d")
        if len(hist) > 0:
            return hist['Close'].iloc[-1] / 100  # Convert from percentage
    except Exception:
        pass

    # Fallback to reasonable default (as of 2024-2025)
    return 0.05