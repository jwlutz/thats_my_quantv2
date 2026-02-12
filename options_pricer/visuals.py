"""
Options visualization functions.

All functions return matplotlib Figure objects and optionally save to file.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Optional, List
from dataclasses import dataclass

from european import black_scholes, european_greeks
from data import OptionChain, ValidationResult


@dataclass
class OptionLeg:
    """Single leg of an options position."""
    option_type: str  # "call" or "put"
    strike: float
    premium: float
    position: str = "long"  # "long" or "short"
    quantity: int = 1


def plot_payoff(
    S: float,
    K: float,
    premium: float,
    option_type: str = "call",
    position: str = "long",
    S_range: Optional[tuple] = None,
    save_path: Optional[str] = None
) -> Figure:
    """
    Plot option payoff diagram at expiration.

    Parameters
    ----------
    S : float
        Current spot price (for reference line)
    K : float
        Strike price
    premium : float
        Option premium paid/received
    option_type : str
        "call" or "put"
    position : str
        "long" or "short"
    S_range : tuple, optional
        (min, max) for x-axis. Default: ±50% from strike
    save_path : str, optional
        Path to save figure

    Returns
    -------
    Figure
        Matplotlib figure object
    """
    if S_range is None:
        S_range = (K * 0.5, K * 1.5)

    prices = np.linspace(S_range[0], S_range[1], 200)

    # Calculate intrinsic value at expiration
    if option_type.lower() == "call":
        intrinsic = np.maximum(prices - K, 0)
    else:
        intrinsic = np.maximum(K - prices, 0)

    # Payoff including premium
    if position.lower() == "long":
        payoff = intrinsic - premium
        breakeven = K + premium if option_type.lower() == "call" else K - premium
    else:
        payoff = premium - intrinsic
        breakeven = K + premium if option_type.lower() == "call" else K - premium

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot payoff line
    ax.plot(prices, payoff, 'b-', linewidth=2, label=f'{position.title()} {option_type.title()}')

    # Zero line
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    # Strike price
    ax.axvline(x=K, color='red', linestyle='--', alpha=0.7, label=f'Strike: ${K:.2f}')

    # Breakeven
    ax.axvline(x=breakeven, color='green', linestyle=':', alpha=0.7, label=f'Breakeven: ${breakeven:.2f}')

    # Current spot
    ax.axvline(x=S, color='purple', linestyle='-.', alpha=0.5, label=f'Spot: ${S:.2f}')

    # Shade profit/loss regions
    ax.fill_between(prices, payoff, 0, where=(payoff > 0), alpha=0.3, color='green', label='Profit')
    ax.fill_between(prices, payoff, 0, where=(payoff < 0), alpha=0.3, color='red', label='Loss')

    ax.set_xlabel('Stock Price at Expiration ($)')
    ax.set_ylabel('Profit/Loss ($)')
    ax.set_title(f'{position.title()} {option_type.title()} Payoff Diagram')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def plot_payoff_combo(
    legs: List[OptionLeg],
    S: float,
    S_range: Optional[tuple] = None,
    save_path: Optional[str] = None
) -> Figure:
    """
    Plot combined payoff for multi-leg strategies (spreads, straddles, etc).

    Parameters
    ----------
    legs : list of OptionLeg
        List of option legs in the strategy
    S : float
        Current spot price
    S_range : tuple, optional
        (min, max) for x-axis
    save_path : str, optional
        Path to save figure

    Returns
    -------
    Figure
    """
    # Determine range from strikes
    strikes = [leg.strike for leg in legs]
    if S_range is None:
        min_K, max_K = min(strikes), max(strikes)
        S_range = (min_K * 0.7, max_K * 1.3)

    prices = np.linspace(S_range[0], S_range[1], 200)
    total_payoff = np.zeros_like(prices)

    fig, ax = plt.subplots(figsize=(10, 6))

    for leg in legs:
        if leg.option_type.lower() == "call":
            intrinsic = np.maximum(prices - leg.strike, 0)
        else:
            intrinsic = np.maximum(leg.strike - prices, 0)

        if leg.position.lower() == "long":
            leg_payoff = (intrinsic - leg.premium) * leg.quantity
        else:
            leg_payoff = (leg.premium - intrinsic) * leg.quantity

        total_payoff += leg_payoff

        # Plot individual leg (faded)
        ax.plot(prices, leg_payoff, '--', alpha=0.4,
                label=f'{leg.position.title()} {leg.quantity}x {leg.option_type.title()} K={leg.strike}')

    # Plot combined payoff
    ax.plot(prices, total_payoff, 'b-', linewidth=2.5, label='Combined Payoff')

    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(x=S, color='purple', linestyle='-.', alpha=0.5, label=f'Spot: ${S:.2f}')

    ax.fill_between(prices, total_payoff, 0, where=(total_payoff > 0), alpha=0.3, color='green')
    ax.fill_between(prices, total_payoff, 0, where=(total_payoff < 0), alpha=0.3, color='red')

    ax.set_xlabel('Stock Price at Expiration ($)')
    ax.set_ylabel('Profit/Loss ($)')
    ax.set_title('Multi-Leg Strategy Payoff')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def plot_greeks_surface(
    S_range: tuple,
    K: float,
    T_range: tuple,
    r: float,
    sigma: float,
    greek: str = "delta",
    option_type: str = "call",
    q: float = 0,
    save_path: Optional[str] = None
) -> Figure:
    """
    Plot 3D surface of a Greek across spot price and time.

    Parameters
    ----------
    S_range : tuple
        (min, max) spot price range
    K : float
        Strike price
    T_range : tuple
        (min, max) time to expiration in years
    r : float
        Risk-free rate
    sigma : float
        Volatility
    greek : str
        "delta", "gamma", "theta", or "vega"
    option_type : str
        "call" or "put"
    q : float
        Dividend yield
    save_path : str, optional
        Path to save figure

    Returns
    -------
    Figure
    """
    S_vals = np.linspace(S_range[0], S_range[1], 50)
    T_vals = np.linspace(max(T_range[0], 0.01), T_range[1], 50)

    S_grid, T_grid = np.meshgrid(S_vals, T_vals)
    Z = np.zeros_like(S_grid)

    for i in range(len(T_vals)):
        for j in range(len(S_vals)):
            g = european_greeks(S_vals[j], K, T_vals[i], r, sigma, q, option_type)
            Z[i, j] = getattr(g, greek)

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    surf = ax.plot_surface(S_grid, T_grid, Z, cmap='viridis', alpha=0.8)

    ax.set_xlabel('Spot Price ($)')
    ax.set_ylabel('Time to Expiration (years)')
    ax.set_zlabel(greek.title())
    ax.set_title(f'{greek.title()} Surface for {option_type.title()} Option (K=${K}, σ={sigma:.0%})')

    fig.colorbar(surf, shrink=0.5, aspect=10)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def plot_volatility_smile(
    chain: OptionChain,
    expiration: Optional[str] = None,
    save_path: Optional[str] = None
) -> Figure:
    """
    Plot implied volatility smile (IV vs strike).

    Parameters
    ----------
    chain : OptionChain
        Options chain data from fetch_option_chain()
    expiration : str, optional
        Expiration date (if multiple in chain)
    save_path : str, optional
        Path to save figure

    Returns
    -------
    Figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    S = chain.spot_price

    # Filter for valid IV
    calls = chain.calls[chain.calls['impliedVolatility'] > 0].copy()
    puts = chain.puts[chain.puts['impliedVolatility'] > 0].copy()

    if len(calls) > 0:
        ax.scatter(calls['strike'], calls['impliedVolatility'] * 100,
                   c='blue', alpha=0.7, label='Calls', s=30)

    if len(puts) > 0:
        ax.scatter(puts['strike'], puts['impliedVolatility'] * 100,
                   c='red', alpha=0.7, label='Puts', s=30)

    # ATM line
    ax.axvline(x=S, color='green', linestyle='--', alpha=0.7, label=f'Spot: ${S:.2f}')

    ax.set_xlabel('Strike Price ($)')
    ax.set_ylabel('Implied Volatility (%)')
    ax.set_title(f'Volatility Smile - {chain.ticker}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def plot_term_structure(
    ticker: str,
    strike: Optional[float] = None,
    save_path: Optional[str] = None
) -> Figure:
    """
    Plot ATM implied volatility term structure across expirations.

    Parameters
    ----------
    ticker : str
        Stock ticker
    strike : float, optional
        Specific strike to use. If None, uses ATM for each expiration.
    save_path : str, optional
        Path to save figure

    Returns
    -------
    Figure
    """
    import yfinance as yf
    from datetime import datetime

    stock = yf.Ticker(ticker)
    expirations = stock.options
    spot = stock.info.get('regularMarketPrice', stock.info.get('currentPrice', 100))

    dates = []
    ivs = []

    for exp in expirations[:10]:  # Limit to first 10 expirations
        try:
            chain = stock.option_chain(exp)
            calls = chain.calls

            # Find ATM or nearest to specified strike
            if strike is None:
                target_K = spot
            else:
                target_K = strike

            # Find closest strike
            idx = (calls['strike'] - target_K).abs().idxmin()
            row = calls.loc[idx]

            iv = row.get('impliedVolatility', np.nan)
            if iv > 0:
                exp_date = datetime.strptime(exp, "%Y-%m-%d")
                days_to_exp = (exp_date - datetime.now()).days
                dates.append(days_to_exp)
                ivs.append(iv * 100)
        except Exception:
            continue

    fig, ax = plt.subplots(figsize=(10, 6))

    if len(dates) > 0:
        ax.plot(dates, ivs, 'bo-', linewidth=2, markersize=8)
        ax.scatter(dates, ivs, c='blue', s=50, zorder=5)

    ax.set_xlabel('Days to Expiration')
    ax.set_ylabel('Implied Volatility (%)')
    ax.set_title(f'IV Term Structure - {ticker}')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def plot_model_vs_market(
    validation: ValidationResult,
    save_path: Optional[str] = None
) -> Figure:
    """
    Scatter plot comparing model prices to market prices.

    Parameters
    ----------
    validation : ValidationResult
        Result from validate_against_market()
    save_path : str, optional
        Path to save figure

    Returns
    -------
    Figure
    """
    df = validation.comparison

    fig, ax = plt.subplots(figsize=(10, 8))

    # Separate calls and puts
    calls = df[df['type'] == 'call']
    puts = df[df['type'] == 'put']

    # Color by moneyness
    if len(calls) > 0:
        scatter_calls = ax.scatter(
            calls['market_price'], calls['european_price'],
            c=calls['moneyness'], cmap='coolwarm', marker='o',
            s=50, alpha=0.7, label='Calls'
        )

    if len(puts) > 0:
        scatter_puts = ax.scatter(
            puts['market_price'], puts['european_price'],
            c=puts['moneyness'], cmap='coolwarm', marker='^',
            s=50, alpha=0.7, label='Puts'
        )

    # Perfect model line
    max_price = max(df['market_price'].max(), df['european_price'].max())
    ax.plot([0, max_price], [0, max_price], 'k--', alpha=0.5, label='Perfect Model')

    # Error bands (±5%)
    ax.fill_between([0, max_price], [0, max_price * 0.95], [0, max_price * 1.05],
                    alpha=0.1, color='green', label='±5% band')

    ax.set_xlabel('Market Price ($)')
    ax.set_ylabel('Model Price ($)')
    ax.set_title(f'Model vs Market - {validation.ticker}\nMean Error: {validation.mean_abs_error:.2f}%')
    ax.legend()
    ax.grid(True, alpha=0.3)

    if len(calls) > 0 or len(puts) > 0:
        plt.colorbar(scatter_calls if len(calls) > 0 else scatter_puts,
                     ax=ax, label='Moneyness (S/K)')

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig