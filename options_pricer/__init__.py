"""
Options Pricer - Standalone options pricing library.

Supports European and American options with Greeks, IV solving,
live data validation, and visualizations.
"""

# European pricing
from european import (
    black_scholes,
    european_greeks,
    EuropeanGreeks,
    put_call_parity_check,
)

# American pricing
from american import (
    binomial_tree,
    baw_american,
)

# Unified Greeks
from greeks import (
    greeks,
    GreeksResult,
)

# Implied volatility
from implied_vol import (
    implied_volatility,
    iv_chain,
)

# Data integration
from data import (
    fetch_option_chain,
    validate_against_market,
    get_risk_free_rate,
    OptionChain,
    ValidationResult,
)

# Visualization
from visuals import (
    plot_payoff,
    plot_payoff_combo,
    plot_greeks_surface,
    plot_volatility_smile,
    plot_term_structure,
    plot_model_vs_market,
    OptionLeg,
)

__version__ = "0.1.0"

__all__ = [
    # European
    "black_scholes",
    "european_greeks",
    "EuropeanGreeks",
    "put_call_parity_check",
    # American
    "binomial_tree",
    "baw_american",
    # Greeks
    "greeks",
    "GreeksResult",
    # IV
    "implied_volatility",
    "iv_chain",
    # Data
    "fetch_option_chain",
    "validate_against_market",
    "get_risk_free_rate",
    "OptionChain",
    "ValidationResult",
    # Visuals
    "plot_payoff",
    "plot_payoff_combo",
    "plot_greeks_surface",
    "plot_volatility_smile",
    "plot_term_structure",
    "plot_model_vs_market",
    "OptionLeg",
]