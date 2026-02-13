# Codebase Risks

## Active Risks

### R6: Survivorship Bias (User Responsibility)
**Severity:** High (Data-dependent)
**Location:** All backtest paths
**Description:** Backtester uses whatever stock universe is provided. If the universe only contains currently-trading stocks, results are inflated due to excluding delisted stocks, bankruptcies, and mergers. Momentum strategies show 20%+ CAGR on survivor data vs <8% on bias-free data.
**Mitigation:** Documented in Backtester class docstring. Users must provide point-in-time constituent lists for accurate results.

### R7: Adjusted Data Assumption
**Severity:** Medium (Data-dependent)
**Location:** All price data paths
**Description:** Backtester assumes price data is adjusted for splits and dividends. Using unadjusted data produces incorrect results (2:1 split appears as 50% loss).
**Mitigation:** Documented in Backtester class docstring. Most data providers return adjusted prices by default.

### R8: Monte Carlo Uses Dollar P&Ls
**Severity:** Low
**Location:** results.py:1054
**Description:** Monte Carlo simulation shuffles dollar P&Ls, not percentage returns. This doesn't capture sequence-of-returns risk for strategies with dynamic position sizing.
**Mitigation:** Documented in code. Accurate for fixed position sizes; consider percentage returns for dynamic sizing.

### R9: Win Rate Includes Open Positions
**Severity:** Low
**Location:** vectorized.py:196
**Description:** Positions still open at backtest end are included in win rate using last price. Win rate depends somewhat on arbitrary choice of end date.
**Mitigation:** Documented in function docstring. Generally acceptable for most backtests.

### R10: StopLoss Uses Cost Basis
**Severity:** Low (Intentional behavior)
**Location:** exitrule.py:86
**Description:** StopLossExit uses cost_basis_per_share (includes commissions/slippage), making effective stop slightly tighter than specified percentage.
**Mitigation:** Documented in class docstring. Intentional - protects against total capital loss.

## Resolved Risks (2026-02-12 Audit)

### R3: Options Pricer - BAW Approximation Error
**Severity:** Low
**Location:** options_pricer/american.py
**Description:** Barone-Adesi-Whaley approximation has ~0.1% error for ATM/ITM options, but can be 2-5% for far OTM options (e.g., $0.04 absolute error on a $1 option).
**Mitigation:** Documented in docstrings. For OTM options requiring precision, use `binomial_tree(steps=500)` instead.

### R5: Options Pricer - Binomial Tree Steps
**Severity:** Low
**Location:** options_pricer/american.py
**Description:** Binomial tree with default 100 steps has ~$0.01 numerical error. With 500 steps, error drops to ~$0.001.
**Mitigation:** Default is 100 steps (fast). Use `steps=500` for pricing, `steps=200` for Greeks (finite difference needs speed).

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

### Fill Timing Default (Resolved 2026-02-12)
**Original Risk:** Default CURRENT_BAR_CLOSE fill timing caused look-ahead bias on daily bars (~10-30bps/trade inflation).
**Resolution:** Changed default to NEXT_BAR_OPEN in backtester.py:60. More realistic execution timing.

### EqualWeight Position Sizer (Resolved 2026-02-12)
**Original Risk:** EqualWeight divided available_cash by max_positions, causing unequal allocations (first position got full weight, last got 1/max_positions).
**Resolution:** Changed to divide by remaining_slots (max_positions - open_positions) in positionsizer.py:279.

### TrailingStopExit State Leak (Resolved 2026-02-12)
**Original Risk:** TrailingStopExit stored peak prices in _peak_prices dict that persisted across backtests.
**Resolution:** Removed _peak_prices dict; now uses RoundTrip.mfe to calculate peak price dynamically in exitrule.py:133-144.

### Delisted Stock Handling (Resolved 2026-02-12)
**Original Risk:** Delisted positions were left open with $0 value but not properly closed (loss not recorded).
**Resolution:** Force-close delisted positions at $0 with reason "delisted" in backtester.py:890-903.

### CAGR Calculation Inconsistency (Resolved 2026-02-12)
**Original Risk:** Vectorized engine used trading days (252), Results class used calendar days (365.25), causing ~2-3% CAGR difference.
**Resolution:** Documented in vectorized.py that Results class is the "source of truth"; vectorized CAGR is an approximation for parameter sweeps.

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
