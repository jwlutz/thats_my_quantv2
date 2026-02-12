"""
Tests for European option pricing.
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from european import black_scholes, european_greeks, put_call_parity_check


class TestBlackScholes:
    """Tests for Black-Scholes pricing."""

    def test_hull_textbook_call(self):
        """Hull textbook example: ATM call should be ~10.45."""
        # S=100, K=100, T=1, r=5%, sigma=20%, q=0
        price = black_scholes(100, 100, 1, 0.05, 0.20, 0, "call")
        assert abs(price - 10.45) < 0.1, f"Expected ~10.45, got {price}"

    def test_hull_textbook_put(self):
        """Hull textbook example for put."""
        price = black_scholes(100, 100, 1, 0.05, 0.20, 0, "put")
        # Put should be call - S + K*e^(-rT) by put-call parity
        call = black_scholes(100, 100, 1, 0.05, 0.20, 0, "call")
        expected = call - 100 + 100 * np.exp(-0.05 * 1)
        assert abs(price - expected) < 1e-10

    def test_put_call_parity(self):
        """Put-call parity should hold to machine precision."""
        S, K, T, r, sigma, q = 100, 100, 1, 0.05, 0.20, 0
        call = black_scholes(S, K, T, r, sigma, q, "call")
        put = black_scholes(S, K, T, r, sigma, q, "put")

        diff = put_call_parity_check(call, put, S, K, T, r, q)
        assert abs(diff) < 1e-10, f"Put-call parity violated: diff = {diff}"

    def test_put_call_parity_with_dividend(self):
        """Put-call parity with dividend yield."""
        S, K, T, r, sigma, q = 100, 110, 0.5, 0.05, 0.25, 0.02
        call = black_scholes(S, K, T, r, sigma, q, "call")
        put = black_scholes(S, K, T, r, sigma, q, "put")

        diff = put_call_parity_check(call, put, S, K, T, r, q)
        assert abs(diff) < 1e-10

    def test_deep_itm_call(self):
        """Deep ITM call should be close to intrinsic value."""
        S, K, T, r, sigma = 150, 100, 0.25, 0.05, 0.20
        price = black_scholes(S, K, T, r, sigma, 0, "call")
        intrinsic = S - K * np.exp(-r * T)
        assert price > intrinsic - 0.01  # Must be >= intrinsic

    def test_deep_otm_call(self):
        """Deep OTM call should be close to zero."""
        price = black_scholes(50, 100, 0.25, 0.05, 0.20, 0, "call")
        assert price < 0.01

    def test_at_expiration_call(self):
        """At expiration, price equals intrinsic value."""
        price = black_scholes(110, 100, 0, 0.05, 0.20, 0, "call")
        assert abs(price - 10) < 1e-10

    def test_at_expiration_put_otm(self):
        """At expiration, OTM put is worthless."""
        price = black_scholes(110, 100, 0, 0.05, 0.20, 0, "put")
        assert abs(price) < 1e-10

    def test_zero_vol_call(self):
        """Zero volatility: option worth present value of intrinsic."""
        S, K, T, r = 110, 100, 1, 0.05
        price = black_scholes(S, K, T, r, 0.0001, 0, "call")  # Near-zero vol
        expected = max(S - K * np.exp(-r * T), 0)
        assert abs(price - expected) < 0.1

    def test_high_vol_increases_price(self):
        """Higher volatility should increase option price."""
        base = black_scholes(100, 100, 1, 0.05, 0.20, 0, "call")
        high_vol = black_scholes(100, 100, 1, 0.05, 0.40, 0, "call")
        assert high_vol > base


class TestEuropeanGreeks:
    """Tests for European Greeks calculations."""

    def test_call_delta_bounds(self):
        """Call delta should be between 0 and 1."""
        greeks = european_greeks(100, 100, 1, 0.05, 0.20, 0, "call")
        assert 0 < greeks.delta < 1

    def test_put_delta_bounds(self):
        """Put delta should be between -1 and 0."""
        greeks = european_greeks(100, 100, 1, 0.05, 0.20, 0, "put")
        assert -1 < greeks.delta < 0

    def test_atm_call_delta(self):
        """ATM call delta should be around 0.5."""
        greeks = european_greeks(100, 100, 0.25, 0.05, 0.20, 0, "call")
        assert abs(greeks.delta - 0.5) < 0.1

    def test_gamma_positive(self):
        """Gamma should always be positive."""
        greeks_call = european_greeks(100, 100, 1, 0.05, 0.20, 0, "call")
        greeks_put = european_greeks(100, 100, 1, 0.05, 0.20, 0, "put")
        assert greeks_call.gamma > 0
        assert greeks_put.gamma > 0

    def test_gamma_same_for_call_put(self):
        """Gamma should be the same for call and put at same strike."""
        greeks_call = european_greeks(100, 100, 1, 0.05, 0.20, 0, "call")
        greeks_put = european_greeks(100, 100, 1, 0.05, 0.20, 0, "put")
        assert abs(greeks_call.gamma - greeks_put.gamma) < 1e-10

    def test_vega_positive(self):
        """Vega should always be positive."""
        greeks = european_greeks(100, 100, 1, 0.05, 0.20, 0, "call")
        assert greeks.vega > 0

    def test_vega_same_for_call_put(self):
        """Vega should be the same for call and put."""
        greeks_call = european_greeks(100, 100, 1, 0.05, 0.20, 0, "call")
        greeks_put = european_greeks(100, 100, 1, 0.05, 0.20, 0, "put")
        assert abs(greeks_call.vega - greeks_put.vega) < 1e-10

    def test_theta_typically_negative_for_long(self):
        """Theta should typically be negative for long options."""
        greeks = european_greeks(100, 100, 0.25, 0.05, 0.20, 0, "call")
        assert greeks.theta < 0  # Time decay hurts long positions

    def test_call_rho_positive(self):
        """Call rho should be positive (higher rates help calls)."""
        greeks = european_greeks(100, 100, 1, 0.05, 0.20, 0, "call")
        assert greeks.rho > 0

    def test_put_rho_negative(self):
        """Put rho should be negative (higher rates hurt puts)."""
        greeks = european_greeks(100, 100, 1, 0.05, 0.20, 0, "put")
        assert greeks.rho < 0

    def test_gamma_peaks_atm(self):
        """Gamma should be highest ATM."""
        gamma_atm = european_greeks(100, 100, 0.25, 0.05, 0.20, 0, "call").gamma
        gamma_itm = european_greeks(120, 100, 0.25, 0.05, 0.20, 0, "call").gamma
        gamma_otm = european_greeks(80, 100, 0.25, 0.05, 0.20, 0, "call").gamma
        assert gamma_atm > gamma_itm
        assert gamma_atm > gamma_otm


class TestEdgeCases:
    """Edge case tests."""

    def test_very_small_time(self):
        """Near expiration should not crash."""
        price = black_scholes(100, 100, 0.001, 0.05, 0.20, 0, "call")
        assert price >= 0

    def test_very_high_vol(self):
        """Very high volatility should not crash."""
        price = black_scholes(100, 100, 1, 0.05, 5.0, 0, "call")
        assert price > 0
        assert price < 100  # Can't be worth more than stock

    def test_negative_rate(self):
        """Negative interest rate should work."""
        price = black_scholes(100, 100, 1, -0.01, 0.20, 0, "call")
        assert price > 0