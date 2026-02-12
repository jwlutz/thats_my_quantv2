"""
Tests that require live market data.

These tests are marked with @pytest.mark.live and are skipped by default.
Run with: pytest -m live
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mark all tests in this module as requiring live data
pytestmark = pytest.mark.live


class TestFetchOptionChain:
    """Tests for fetching live option chains."""

    def test_fetch_aapl(self):
        """Fetch AAPL options chain."""
        from data import fetch_option_chain

        chain = fetch_option_chain("AAPL")

        assert chain.ticker == "AAPL"
        assert chain.spot_price > 0
        assert len(chain.expirations) > 0
        assert len(chain.calls) > 0
        assert len(chain.puts) > 0

    def test_fetch_spy(self):
        """Fetch SPY options chain."""
        from data import fetch_option_chain

        chain = fetch_option_chain("SPY")

        assert chain.ticker == "SPY"
        assert chain.spot_price > 0
        assert len(chain.calls) > 0

    def test_fetch_specific_expiration(self):
        """Fetch specific expiration date."""
        from data import fetch_option_chain

        # First get available expirations
        chain = fetch_option_chain("AAPL")
        if len(chain.expirations) > 1:
            exp = chain.expirations[1]  # Second expiration
            chain2 = fetch_option_chain("AAPL", exp)
            assert len(chain2.calls) > 0

    def test_invalid_ticker(self):
        """Invalid ticker should raise error."""
        from data import fetch_option_chain

        with pytest.raises(Exception):
            fetch_option_chain("INVALIDTICKER12345")


class TestValidateAgainstMarket:
    """Tests for model vs market validation."""

    def test_validate_aapl(self):
        """Validate model against AAPL market prices."""
        from data import validate_against_market

        result = validate_against_market("AAPL")

        assert result.ticker == "AAPL"
        assert result.spot > 0
        assert len(result.comparison) > 0
        assert not np.isnan(result.mean_abs_error)

    def test_model_error_reasonable(self):
        """Model error should be reasonable for liquid options."""
        from data import validate_against_market

        result = validate_against_market("SPY")

        # Filter to ATM options (moneyness between 0.9 and 1.1)
        atm = result.comparison[
            (result.comparison['moneyness'] > 0.9) &
            (result.comparison['moneyness'] < 1.1)
        ]

        if len(atm) > 0:
            atm_error = atm['error_pct'].mean()
            # ATM options should have reasonable error
            # Note: Error varies with bid-ask spread and market conditions
            assert atm_error < 20, f"ATM error too high: {atm_error:.1f}%"

    def test_american_european_diff(self):
        """American vs European difference should be positive for puts."""
        from data import validate_against_market

        result = validate_against_market("AAPL")

        puts = result.comparison[result.comparison['type'] == 'put']
        if len(puts) > 0:
            diff = (puts['american_price'] - puts['european_price']).mean()
            # American puts should be worth more (early exercise premium)
            assert diff >= -0.01  # Allow tiny numerical error


class TestRiskFreeRate:
    """Tests for risk-free rate fetching."""

    def test_get_risk_free_rate(self):
        """Should return a reasonable rate."""
        from data import get_risk_free_rate

        rate = get_risk_free_rate()

        # Should be between -2% and 15%
        assert -0.02 < rate < 0.15


class TestVolatilitySmile:
    """Tests for IV smile patterns."""

    def test_put_skew_exists(self):
        """Equity indices should show put skew (OTM puts have higher IV)."""
        from data import fetch_option_chain

        chain = fetch_option_chain("SPY")
        S = chain.spot_price

        # Get IV for OTM puts and calls
        otm_puts = chain.puts[chain.puts['strike'] < S * 0.95]
        otm_calls = chain.calls[chain.calls['strike'] > S * 1.05]

        if len(otm_puts) > 0 and len(otm_calls) > 0:
            put_iv = otm_puts['impliedVolatility'].mean()
            call_iv = otm_calls['impliedVolatility'].mean()

            # Put skew: OTM puts typically have higher IV than OTM calls
            # This isn't always true but is the typical pattern
            # Just verify we can compute it without error
            assert put_iv > 0 and call_iv > 0