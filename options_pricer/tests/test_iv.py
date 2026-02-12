"""
Tests for implied volatility solver.
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from implied_vol import implied_volatility, iv_chain
from european import black_scholes
from american import binomial_tree


class TestEuropeanIV:
    """Tests for European IV solver."""

    def test_roundtrip_call(self):
        """Price -> IV -> Price should match within tolerance."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.25
        price = black_scholes(S, K, T, r, sigma, 0, "call")

        iv = implied_volatility(price, S, K, T, r, 0, "call", "european")
        recovered_price = black_scholes(S, K, T, r, iv, 0, "call")

        assert abs(recovered_price - price) < 1e-6

    def test_roundtrip_put(self):
        """Put IV roundtrip."""
        S, K, T, r, sigma = 100, 110, 0.5, 0.05, 0.30
        price = black_scholes(S, K, T, r, sigma, 0, "put")

        iv = implied_volatility(price, S, K, T, r, 0, "put", "european")
        recovered_price = black_scholes(S, K, T, r, iv, 0, "put")

        assert abs(recovered_price - price) < 1e-6

    def test_atm_convergence(self):
        """ATM options should converge quickly."""
        S, K, T, r, sigma = 100, 100, 0.25, 0.05, 0.20
        price = black_scholes(S, K, T, r, sigma, 0, "call")

        iv = implied_volatility(price, S, K, T, r, 0, "call", "european")
        assert abs(iv - sigma) < 1e-6

    def test_itm_call(self):
        """ITM call IV should work."""
        S, K, T, r, sigma = 120, 100, 0.5, 0.05, 0.25
        price = black_scholes(S, K, T, r, sigma, 0, "call")

        iv = implied_volatility(price, S, K, T, r, 0, "call", "european")
        assert abs(iv - sigma) < 1e-4

    def test_otm_call(self):
        """OTM call IV should work."""
        S, K, T, r, sigma = 80, 100, 0.5, 0.05, 0.25
        price = black_scholes(S, K, T, r, sigma, 0, "call")

        iv = implied_volatility(price, S, K, T, r, 0, "call", "european")
        assert abs(iv - sigma) < 1e-4

    def test_below_intrinsic_returns_nan(self):
        """Price below intrinsic should return NaN."""
        S, K, T, r = 120, 100, 0.5, 0.05
        intrinsic = S - K * np.exp(-r * T)
        bad_price = intrinsic - 1  # Below intrinsic

        iv = implied_volatility(bad_price, S, K, T, r, 0, "call", "european")
        assert np.isnan(iv)

    def test_with_dividend(self):
        """IV with dividend yield."""
        S, K, T, r, sigma, q = 100, 100, 1, 0.05, 0.25, 0.02
        price = black_scholes(S, K, T, r, sigma, q, "call")

        iv = implied_volatility(price, S, K, T, r, q, "call", "european")
        assert abs(iv - sigma) < 1e-4

    def test_various_vols(self):
        """Test across various volatility levels."""
        S, K, T, r = 100, 100, 0.5, 0.05

        for sigma in [0.10, 0.20, 0.30, 0.50, 1.0]:
            price = black_scholes(S, K, T, r, sigma, 0, "call")
            iv = implied_volatility(price, S, K, T, r, 0, "call", "european")
            assert abs(iv - sigma) < 1e-4, f"Failed for sigma={sigma}"


class TestAmericanIV:
    """Tests for American IV solver."""

    def test_roundtrip_put(self):
        """American put IV roundtrip."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.25
        price = binomial_tree(S, K, T, r, sigma, 0, "put", steps=200)

        iv = implied_volatility(price, S, K, T, r, 0, "put", "american")

        # Verify roundtrip
        recovered_price = binomial_tree(S, K, T, r, iv, 0, "put", steps=200)
        assert abs(recovered_price - price) < 0.01

    def test_call_no_div_same_as_european(self):
        """American call IV (no div) should equal European IV."""
        S, K, T, r, sigma = 100, 100, 0.5, 0.05, 0.25
        price = black_scholes(S, K, T, r, sigma, 0, "call")

        iv_eu = implied_volatility(price, S, K, T, r, 0, "call", "european")
        iv_am = implied_volatility(price, S, K, T, r, 0, "call", "american")

        assert abs(iv_eu - iv_am) < 0.01


class TestIVChain:
    """Tests for batch IV calculation."""

    def test_iv_chain_basic(self):
        """Basic IV chain calculation."""
        S, T, r, sigma = 100, 0.5, 0.05, 0.25
        strikes = np.array([90, 95, 100, 105, 110])
        prices = np.array([black_scholes(S, K, T, r, sigma, 0, "call") for K in strikes])

        ivs = iv_chain(prices, S, strikes, T, r, 0, "call", "european")

        for iv in ivs:
            assert abs(iv - sigma) < 1e-4

    def test_iv_chain_with_nans(self):
        """IV chain should handle invalid prices gracefully."""
        S, T, r = 100, 0.5, 0.05
        strikes = np.array([90, 100, 110])
        prices = np.array([5.0, 0.001, 2.0])  # Middle one too cheap

        ivs = iv_chain(prices, S, strikes, T, r, 0, "call", "european")

        # Should have some valid IVs
        assert not np.all(np.isnan(ivs))


class TestEdgeCases:
    """Edge case tests for IV solver."""

    def test_very_small_price(self):
        """Very small option price."""
        iv = implied_volatility(0.01, 100, 150, 0.25, 0.05, 0, "call", "european")
        # Should either find a high IV or return NaN
        assert np.isnan(iv) or iv > 0

    def test_very_short_expiration(self):
        """Near expiration option."""
        S, K, T, r, sigma = 100, 100, 0.01, 0.05, 0.25
        price = black_scholes(S, K, T, r, sigma, 0, "call")

        iv = implied_volatility(price, S, K, T, r, 0, "call", "european")
        # Should still work
        assert not np.isnan(iv) or price < 1e-6

    def test_invalid_inputs(self):
        """Invalid inputs should return NaN."""
        assert np.isnan(implied_volatility(-1, 100, 100, 1, 0.05, 0, "call"))
        assert np.isnan(implied_volatility(10, -100, 100, 1, 0.05, 0, "call"))
        assert np.isnan(implied_volatility(10, 100, -100, 1, 0.05, 0, "call"))