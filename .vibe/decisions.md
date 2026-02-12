# Architecture Decisions

## Vectorized Screening Engine (2026-02-12)

### Context
Built a fast parameter sweep engine to screen thousands of strategy combinations. The vectorized engine trades accuracy for speed - it's a filter, not a replacement for the event-driven backtester.

### Decisions

#### D1: Metric Functions Must Be Byte-Identical to Results.py
**Decision:** `_sharpe`, `_cagr`, `_max_drawdown` use identical formulas to Results class.
**Rationale:** If metrics diverge, sweep rankings become meaningless. You'd spend hours debugging "why does vectorized say this strategy is good but the full backtester says it's bad."
**Implementation:**
- ddof=1 for std (matching pandas default)
- 252 trading days per year
- Sharpe = CAGR / volatility (not the standard mean/std*sqrt(N))
- Zero std edge case returns 0.0 (threshold 1e-15)

#### D2: RSI Implementation Matches StreamProcessor
**Decision:** vectorized_rsi produces values within 0.5 tolerance of StreamProcessor.RSI
**Rationale:** Ensures strategies behave consistently between screening and live trading.
**Implementation:**
- First tick returns 0 (no RSI until second price)
- Uses EMA with alpha = 2/(period+1) for gains/losses
- np.diff() without prepend to match delta calculation

#### D3: Numba with Pure Python Fallback
**Decision:** resolve_signals uses Numba @njit when available, falls back to pure Python.
**Rationale:** Numba provides 10-100x speedup but isn't available everywhere (CI, some environments).
**Implementation:** try/except around numba import, duplicate function definitions.

#### D4: Fixed Slippage Model for Screening
**Decision:** Use fixed percentage slippage (default 0.1%) rather than SqrtImpact.
**Rationale:** Screening needs speed. Realistic execution modeling happens in the event-driven backtester for top candidates.

#### D5: NEXT_BAR_OPEN as Default Fill Timing
**Decision:** Positions are delayed by one bar (signal on bar N, fill at bar N+1).
**Rationale:** Avoids look-ahead bias on daily bars. Matches event-driven backtester behavior.

### Validation Contract
The ultimate test: run identical RSI strategy through both engines on same data.
- Trade count: exact match
- Total return: within 1% relative
- Sharpe: within 0.1 absolute

Cross-engine tests are scaffolded (skipped) pending event-driven backtester test fixtures.
