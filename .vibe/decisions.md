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

---

## Statistical Validation Decisions (2026-02-12)

### D12: Deflated Sharpe Ratio as Primary Gate
**Decision:** DSR per Bailey & López de Prado (2014) is the primary statistical significance test for parameter sweeps.
**Rationale:** DSR answers "is this Sharpe ratio significant given how many combinations we tested?" — the core multiple testing problem in backtesting.
**Implementation:**
- Uses extreme value theory for expected max Sharpe under null
- Corrects for non-normality (skewness, kurtosis)
- p-value thresholds: <0.01 (highly sig), <0.05 (sig), <0.10 (marginal)
- Location: `paramsweep.py:deflated_sharpe_ratio()`

### D13: Purged K-Fold (Not CPCV) for Initial CV
**Decision:** Implemented Purged K-Fold with embargo, not full Combinatorial Purged CV.
**Rationale:** CPCV generates N-choose-K train/test combinations (~100x more backtests). PurgedKFold is sufficient for parameter sweep diagnostics. CPCV deferred until PBO implementation.
**Implementation:**
- 5 sequential folds (configurable)
- purge_pct: removes training data near test boundary
- embargo_pct: gap after test set
- Location: `paramsweep.py:PurgedKFold`

### D14: Three Monte Carlo Methods for Different Questions
**Decision:** Implemented three distinct resampling methods, each answering a different question.
**Rationale:** They're not interchangeable — each tests a specific hypothesis.
**Implementation:**
1. `monte_carlo()` — Trade sequence shuffling. Tests: "Is P&L order-dependent?" Useful for detecting trend-following vs mean-reversion characteristics.
2. `permutation_test()` — Sign randomization on daily returns. Tests: "Is Sharpe significantly different from zero?" Quick filter before deeper analysis.
3. `bootstrap_paths()` — Resampling with replacement. Produces: confidence intervals for return, drawdown, Sharpe. Answers: "How uncertain are these metrics?"
- Location: `results.py`

### D15: Walk-Forward Analysis as Operational Simulation
**Decision:** WFA is explicitly positioned as operational simulation, NOT primary validation.
**Rationale:** Per López de Prado (2018), WFA answers "how would live execution have looked?" — not "is this strategy real?" That's what DSR and CPCV answer.
**Implementation:**
- Rolling or anchored training windows
- Stitched OOS equity curve
- Walk-Forward Efficiency (WFE) per step
- Parameter drift tracking
- Location: `walkforward.py:WalkForward`

### D16: Regime Tagger Uses Observable Indicators Only
**Decision:** Regime detection uses SPY vs SMA (trend) and VIX percentile (volatility). No HMMs.
**Rationale:** Per SME guidance: HMMs are unstable out-of-sample. Observable indicators are reproducible and have no hidden state estimation problems.
**Implementation:**
- Trend: SPY > 200-day SMA = bull, else bear
- Volatility: VIX > 75th percentile (trailing 252 days) = high vol
- Stores continuous signals alongside binary labels (future HMM upgrade path)
- Location: `regime.py:RegimeTagger`

---

## PBO Implementation Decisions (2026-02-12)

### D17: CSCV Algorithm for PBO (NOT CPCV)
**Decision:** Use Bailey et al. (2014) CSCV algorithm, not Lopez de Prado (2018) CPCV.
**Rationale:** CSCV operates on T×N return matrix directly — no purging/embargo needed. CPCV is for ML model validation where labels have temporal extent. They solve different problems.
**Implementation:**
- Input: T×N return matrix from parameter sweep (T time periods, N configurations)
- Split into S=16 contiguous blocks (giving C(16,8)=12,870 combinations)
- For each combination: IS half → find optimal config n* → compute OOS rank of n*
- Logit: λ = log(rank / (N - rank))
- PBO = fraction of combinations where λ < 0
- Location: `pbo.py`

### D18: Neighborhood Degradation Specification
**Decision:** Use Chebyshev distance d≤2 with separate metrics for d=1 and d=2 shells.
**Rationale:** Option B (ε-ball with interpolation) introduces artifacts on discrete grids. Chebyshev distance is natural for grid-based parameter sweeps.
**Implementation:**
- NDR(d) = mean(Sharpe in d-shell) / Sharpe(p*)
- CV(d) = std(Sharpe in d-shell) / mean(Sharpe in d-shell)
- Thresholds: NDR(d=1) > 0.80 = robust, 0.50-0.80 = investigate, < 0.50 = fragile
- Low NDR + high CV is especially dangerous (some neighbors catastrophic)
- Location: `pbo.py` or `paramsweep.py`

### D19: Traffic Light Verdict System
**Decision:** Tiered reporting with GREEN/YELLOW/RED verdicts, no single hard gate.
**Rationale:** No single metric should be a kill switch. DSR p=0.06 + PBO=0.15 beats DSR p=0.04 + PBO=0.60.
**Implementation:**
- GREEN (deploy): DSR p < 0.05 AND PBO < 0.40 AND NDR(d=1) > 0.70 AND permutation p < 0.05
- YELLOW (investigate): Any one marginal (DSR 0.05-0.10, PBO 0.40-0.55, NDR 0.50-0.70)
- RED (reject): DSR p > 0.10 OR PBO > 0.55 OR NDR < 0.50
- Location: `RobustnessReport` class

### D20: CPCV Implemented as Gold Standard for OOS Estimation (CORRECTED)
**Decision:** Implement CPCV for OOS performance estimation. It is NOT just for ML strategies.
**Rationale:** SME correction: PBO, CPCV, and WFE answer different questions:
- PBO: "Is my parameter optimization overfit?" (tests selection bias)
- CPCV: "Does this strategy generalize to unseen data?" (OOS performance estimate)
- WFE: "How much performance degrades OOS?" (single rolling window, coarser)
CPCV averages over 12,870 train/test paths vs WFE's ~5-10 steps, giving tighter confidence intervals. One walkforward can get lucky or unlucky; CPCV averages out that noise.
**Implementation:**
- Reuses block splitting from PBO (same CSCV machinery)
- Takes T×1 return series (ONE strategy, not T×N like PBO)
- Returns mean OOS Sharpe, std, 95% CI
- Location: `pbo.py:compute_cpcv()`
- Raises ValueError if T×N with N>1 passed (use compute_pbo for that)
