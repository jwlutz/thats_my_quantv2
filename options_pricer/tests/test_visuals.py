"""
Tests for visualization functions.

These are smoke tests - verify functions run without error and return Figure objects.
Visual correctness requires manual inspection.
"""

import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visuals import (
    plot_payoff,
    plot_payoff_combo,
    plot_greeks_surface,
    OptionLeg,
)


class TestPlotPayoff:
    """Tests for single-leg payoff plots."""

    def test_long_call(self):
        """Plot long call payoff."""
        fig = plot_payoff(100, 100, 5, "call", "long")
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_long_put(self):
        """Plot long put payoff."""
        fig = plot_payoff(100, 100, 5, "put", "long")
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_short_call(self):
        """Plot short call payoff."""
        fig = plot_payoff(100, 100, 5, "call", "short")
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_short_put(self):
        """Plot short put payoff."""
        fig = plot_payoff(100, 100, 5, "put", "short")
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_custom_range(self):
        """Plot with custom S range."""
        fig = plot_payoff(100, 100, 5, "call", "long", S_range=(50, 150))
        assert isinstance(fig, Figure)
        plt.close(fig)


class TestPlotPayoffCombo:
    """Tests for multi-leg strategy payoff plots."""

    def test_bull_call_spread(self):
        """Bull call spread: long lower strike, short higher strike."""
        legs = [
            OptionLeg("call", 95, 7, "long"),
            OptionLeg("call", 105, 3, "short"),
        ]
        fig = plot_payoff_combo(legs, 100)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_straddle(self):
        """Long straddle: long call and put at same strike."""
        legs = [
            OptionLeg("call", 100, 5, "long"),
            OptionLeg("put", 100, 5, "long"),
        ]
        fig = plot_payoff_combo(legs, 100)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_iron_condor(self):
        """Iron condor: 4 legs."""
        legs = [
            OptionLeg("put", 90, 1, "short"),
            OptionLeg("put", 95, 2, "long"),
            OptionLeg("call", 105, 2, "long"),
            OptionLeg("call", 110, 1, "short"),
        ]
        fig = plot_payoff_combo(legs, 100)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_butterfly(self):
        """Butterfly spread."""
        legs = [
            OptionLeg("call", 95, 7, "long"),
            OptionLeg("call", 100, 4, "short", quantity=2),
            OptionLeg("call", 105, 2, "long"),
        ]
        fig = plot_payoff_combo(legs, 100)
        assert isinstance(fig, Figure)
        plt.close(fig)


class TestPlotGreeksSurface:
    """Tests for 3D Greeks surface plots."""

    def test_delta_surface(self):
        """Plot delta surface."""
        fig = plot_greeks_surface(
            S_range=(80, 120),
            K=100,
            T_range=(0.1, 1.0),
            r=0.05,
            sigma=0.20,
            greek="delta",
            option_type="call"
        )
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_gamma_surface(self):
        """Plot gamma surface."""
        fig = plot_greeks_surface(
            S_range=(80, 120),
            K=100,
            T_range=(0.1, 1.0),
            r=0.05,
            sigma=0.20,
            greek="gamma"
        )
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_theta_surface(self):
        """Plot theta surface."""
        fig = plot_greeks_surface(
            S_range=(80, 120),
            K=100,
            T_range=(0.1, 1.0),
            r=0.05,
            sigma=0.20,
            greek="theta"
        )
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_vega_surface(self):
        """Plot vega surface."""
        fig = plot_greeks_surface(
            S_range=(80, 120),
            K=100,
            T_range=(0.1, 1.0),
            r=0.05,
            sigma=0.20,
            greek="vega"
        )
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_put_surface(self):
        """Plot surface for put option."""
        fig = plot_greeks_surface(
            S_range=(80, 120),
            K=100,
            T_range=(0.1, 1.0),
            r=0.05,
            sigma=0.20,
            greek="delta",
            option_type="put"
        )
        assert isinstance(fig, Figure)
        plt.close(fig)


# Tests requiring live data are marked separately
@pytest.mark.live
class TestLiveVisuals:
    """Visual tests requiring live market data."""

    def test_volatility_smile(self):
        """Plot volatility smile from live data."""
        from data import fetch_option_chain
        from visuals import plot_volatility_smile

        chain = fetch_option_chain("AAPL")
        fig = plot_volatility_smile(chain)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_term_structure(self):
        """Plot term structure from live data."""
        from visuals import plot_term_structure

        fig = plot_term_structure("SPY")
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_model_vs_market(self):
        """Plot model vs market comparison."""
        from data import validate_against_market
        from visuals import plot_model_vs_market

        result = validate_against_market("AAPL")
        fig = plot_model_vs_market(result)
        assert isinstance(fig, Figure)
        plt.close(fig)


class TestSaveToFile:
    """Test saving plots to file."""

    def test_save_payoff(self, tmp_path):
        """Save payoff plot to file."""
        save_path = tmp_path / "payoff.png"
        fig = plot_payoff(100, 100, 5, "call", "long", save_path=str(save_path))
        assert save_path.exists()
        plt.close(fig)

    def test_save_greeks_surface(self, tmp_path):
        """Save Greeks surface to file."""
        save_path = tmp_path / "greeks.png"
        fig = plot_greeks_surface(
            S_range=(80, 120),
            K=100,
            T_range=(0.1, 1.0),
            r=0.05,
            sigma=0.20,
            greek="delta",
            save_path=str(save_path)
        )
        assert save_path.exists()
        plt.close(fig)
