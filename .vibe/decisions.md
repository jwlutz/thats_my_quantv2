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
- Total return: within 5% relative (close-to-close vs open-fill creates ~3-4% divergence)
- Sharpe: within 0.1 absolute

**Status: IMPLEMENTED** — Cross-engine tests passing as of 2026-02-12.

---

## Project Architecture Decisions (2026-02-12)

### D6: Monorepo Structure
**Decision:** Keep stone_age (data_feed/) and thats_my_quantv1 in same repo.
**Rationale:** They share strategy interfaces and will share more as they mature. Splitting adds coordination overhead for no benefit.

### D7: Visual Checkpoint via Results.plot()
**Decision:** Add `.plot()` method to Results class rather than standalone script.
**Rationale:** Results already has matplotlib imports. Every backtest result is one call away from a chart.

### D8: Data Source Priority
**Decision:** WRDS/CRSP first (free through UCLA), Polygon free tier as fallback.
**Rationale:** CRSP is gold standard for survivorship-bias-free US equity data. DataProvider ABC makes the switch painless.

### D9: Service Layer Deferred
**Decision:** Don't build service layer until MCP server phase.
**Rationale:** Designing prematurely means guessing wrong about what functions to expose. Service layer emerges naturally from "what tools does Claude need?"

### D10: MCP Framework Choice
**Decision:** Use official `mcp` Python SDK (FastMCP).
**Rationale:** Handles JSON-RPC transport, tool registration, schema generation. Rolling own is pointless complexity.

### D11: Service Layer Location
**Decision:** When built, lives at `thats_my_quant/service/` inside monorepo.
**Rationale:** Consistent with monorepo structure, single import path.
