# Codebase Risks

## Active Risks

### R3: Options Pricer - BAW Approximation Error
**Severity:** Low
**Location:** options_pricer/american.py
**Description:** Barone-Adesi-Whaley approximation has ~0.1% error vs binomial tree. Users may not realize they're using an approximation.
**Mitigation:** Documented in docstrings. For precise pricing, use `binomial_tree(steps=500)` instead of `baw_american()`.

### R4: Options Pricer - American IV Performance
**Severity:** Low
**Location:** options_pricer/implied_vol.py
**Description:** American option IV solving uses binomial tree in a root-finding loop, making it 10-50x slower than European IV.
**Mitigation:** Documented in code. For batch IV calculations on American options, consider using European approximation first.

### R2: Numba Dependency Optional
**Severity:** Low
**Location:** thats_my_quantv1/backtester/vectorized.py:26-30
**Description:** Numba is optional - code falls back to pure Python. Performance degrades significantly without Numba.
**Mitigation:** Pure Python fallback exists. Performance tests verify <100ms even without Numba for typical workloads.

## Resolved Risks

### Metric Function Divergence (Resolved)
**Original Risk:** Vectorized metrics could produce different results than Results.py, making sweep rankings meaningless.
**Resolution:** Comprehensive tests verify byte-identical results for Sharpe, CAGR, max drawdown. Same ddof=1, same annualization factor, same edge case handling.

### RSI Mismatch with StreamProcessor (Resolved)
**Original Risk:** RSI implementation could diverge from StreamProcessor, causing strategy behavior differences between screening and production.
**Resolution:** Test verifies vectorized_rsi matches StreamProcessor.RSI within 0.5 tolerance across various price patterns.

### Cross-Engine Validation Tests Pending (Resolved)
**Original Risk:** Three cross-engine validation tests were skipped pending event-driven backtester test fixtures.
**Resolution:** Implemented RSI Calculation class in calculation.py that matches vectorized_rsi exactly. Four cross-engine tests now pass:
1. Indicator parity: RSI Calculation matches vectorized_rsi within 0.5 tolerance
2. Trade count: Exact match between engines (3 trades each)
3. Total return: Within 5% relative tolerance (accounts for close-to-close vs open fill differences)
4. Sharpe ratio: Within 0.1 absolute tolerance
Key fix: Changed vectorized_rsi to return NaN for day 0 (instead of 0) to prevent spurious entry signals on uncomputed RSI.
