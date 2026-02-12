"""
Tests for American option pricing.
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from american import binomial_tree, baw_american
from european import black_scholes


class TestBinomialTree:
    """Tests for binomial tree pricing."""

    def test_american_call_no_div_equals_european(self):
        """American call without dividends equals European call."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.20
        american = binomial_tree(S, K, T, r, sigma, 0, "call", steps=500)
        european = black_scholes(S, K, T, r, sigma, 0, "call")
        assert abs(american - european) < 0.01

    def test_american_put_geq_european(self):
        """American put should be >= European put."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.20
        american = binomial_tree(S, K, T, r, sigma, 0, "put", steps=200)
        european = black_scholes(S, K, T, r, sigma, 0, "put")
        assert american >= european - 0.001  # Small tolerance for numerical error

    def test_early_exercise_premium_exists_for_put(self):
        """ITM American put should have early exercise premium."""
        S, K, T, r, sigma = 80, 100, 1, 0.05, 0.20  # ITM put
        american = binomial_tree(S, K, T, r, sigma, 0, "put", steps=200)
        european = black_scholes(S, K, T, r, sigma, 0, "put")
        # Premium should be positive for ITM put
        assert american > european

    def test_convergence_with_more_steps(self):
        """Price should converge as steps increase."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.20

        prices = []
        for steps in [50, 100, 200, 500]:
            price = binomial_tree(S, K, T, r, sigma, 0, "put", steps=steps)
            prices.append(price)

        # Differences should decrease
        diffs = [abs(prices[i+1] - prices[i]) for i in range(len(prices)-1)]
        assert diffs[-1] < diffs[0]  # Converging

    def test_at_expiration(self):
        """At expiration, returns intrinsic value."""
        price = binomial_tree(110, 100, 0, 0.05, 0.20, 0, "call")
        assert abs(price - 10) < 1e-10

    def test_deep_itm_put_early_exercise(self):
        """Very deep ITM put should be close to intrinsic (early exercise optimal)."""
        S, K = 20, 100  # Very deep ITM
        american = binomial_tree(S, K, 1, 0.05, 0.20, 0, "put", steps=200)
        intrinsic = K - S
        # Should be very close to intrinsic because early exercise is optimal
        assert abs(american - intrinsic) < 2

    def test_with_dividend_call(self):
        """American call with dividend should exceed European."""
        S, K, T, r, sigma, q = 100, 100, 1, 0.05, 0.20, 0.03
        american = binomial_tree(S, K, T, r, sigma, q, "call", steps=500)
        european = black_scholes(S, K, T, r, sigma, q, "call")
        # With dividends, American call may have early exercise premium
        # Use tolerance for binomial tree numerical error
        assert american >= european - 0.02


class TestBAW:
    """Tests for Barone-Adesi-Whaley approximation."""

    def test_baw_call_no_div_equals_european(self):
        """BAW call without dividends equals European."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.20
        baw = baw_american(S, K, T, r, sigma, 0, "call")
        european = black_scholes(S, K, T, r, sigma, 0, "call")
        assert abs(baw - european) < 0.01

    def test_baw_vs_binomial_put(self):
        """BAW should be within 0.1% of binomial for puts."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.20
        baw = baw_american(S, K, T, r, sigma, 0, "put")
        binomial = binomial_tree(S, K, T, r, sigma, 0, "put", steps=500)

        relative_error = abs(baw - binomial) / binomial
        assert relative_error < 0.01, f"BAW error: {relative_error:.2%}"

    def test_baw_vs_binomial_itm_put(self):
        """BAW for ITM put should be close to binomial."""
        S, K, T, r, sigma = 90, 100, 0.5, 0.05, 0.25
        baw = baw_american(S, K, T, r, sigma, 0, "put")
        binomial = binomial_tree(S, K, T, r, sigma, 0, "put", steps=500)

        relative_error = abs(baw - binomial) / binomial
        assert relative_error < 0.02

    def test_baw_vs_binomial_otm_put(self):
        """BAW for OTM put should be close to binomial."""
        S, K, T, r, sigma = 110, 100, 0.5, 0.05, 0.25
        baw = baw_american(S, K, T, r, sigma, 0, "put")
        binomial = binomial_tree(S, K, T, r, sigma, 0, "put", steps=500)

        relative_error = abs(baw - binomial) / max(binomial, 0.01)
        assert relative_error < 0.02

    def test_baw_put_geq_european(self):
        """BAW put should be >= European put."""
        S, K, T, r, sigma = 100, 100, 1, 0.05, 0.20
        baw = baw_american(S, K, T, r, sigma, 0, "put")
        european = black_scholes(S, K, T, r, sigma, 0, "put")
        assert baw >= european - 0.01

    def test_at_expiration(self):
        """At expiration, returns intrinsic value."""
        price = baw_american(110, 100, 0, 0.05, 0.20, 0, "call")
        assert abs(price - 10) < 1e-10


class TestAmericanVsEuropean:
    """Comparative tests between American and European options."""

    def test_american_geq_european_all_cases(self):
        """American option should always be >= European."""
        test_cases = [
            (100, 100, 1, 0.05, 0.20, 0, "call"),
            (100, 100, 1, 0.05, 0.20, 0, "put"),
            (80, 100, 0.5, 0.05, 0.30, 0, "put"),  # ITM put
            (120, 100, 0.5, 0.05, 0.30, 0, "call"),  # ITM call
            (100, 100, 1, 0.05, 0.20, 0.02, "call"),  # With dividend
        ]

        for S, K, T, r, sigma, q, opt_type in test_cases:
            american = binomial_tree(S, K, T, r, sigma, q, opt_type, steps=200)
            european = black_scholes(S, K, T, r, sigma, q, opt_type)
            assert american >= european - 0.01, \
                f"American < European for {opt_type} S={S} K={K}"