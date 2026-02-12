# Current Task: MCP Server Tool Specification

## Status: Complete (Spec Ready for Review)

## Deliverable
`.vibe/mcp_tools_spec.md` — Full tool registry with schemas, no implementation code.

## What Was Produced
- **15 tools** across 5 categories
- **4 design decisions** with rationale (D1-D4)
- **JSON schemas** for all inputs/outputs
- **3 user flow examples** showing tool sequences
- **5 open questions** for implementation phase

## Tool Categories
1. **Core Backtest Flow** (4 tools): create_strategy, run_backtest, get_backtest_results, list_available_tickers
2. **Robustness & Validation** (4 tools): validate_strategy, run_monte_carlo, run_permutation_test, run_walk_forward
3. **Parameter Sweeps** (2 tools): run_parameter_sweep, get_sweep_status
4. **Visualization** (4 tools): plot_equity_curve, plot_monte_carlo_fan, plot_parameter_heatmap, plot_regime_performance, plot_overfitting_dashboard
5. **Regime Analysis** (1 tool): analyze_regime_performance

## Key Design Decisions
- **D1**: Strategy via structured JSON (not code) — uses existing `Strategy.from_dict()`
- **D2**: Sync for single backtests, async for sweeps
- **D3**: Return data inline, plots as base64
- **D4**: `validate_strategy` = compound tool (PBO + NDR + CPCV + Verdict)

## Next Steps
1. Review spec, mark any changes
2. Implement with FastMCP SDK at `thats_my_quantv1/service/mcp_server.py`

---

# Previous Task: Add CPCV (Combinatorial Purged CV) for OOS Performance Estimation

## Status: Complete

## Context
D20 was wrong - SME says CPCV is gold standard for OOS estimation, not just ML strategies.
- PBO answers: "Is my parameter optimization overfit?"
- CPCV answers: "Does this strategy generalize to unseen data?"
- WFE answers: "How much performance degrades OOS?" (single rolling window, coarser)

CPCV gives many more train/test paths (12,870 vs ~5-10 for WFE), so tighter CIs.

## Success Criteria
- [x] `compute_cpcv()` accepts T×1 return series (error if T×N with N>1)
- [x] Returns mean OOS Sharpe, std, and 95% CI across all combinations
- [x] Uses same block splitting as PBO (S=16 default, C(16,8)=12,870 paths)
- [x] Test: Dominant strategy → tight positive OOS Sharpe distribution
- [x] Test: Pure noise → mean ~0, CI straddles zero
- [x] Test: Directional agreement with WFE (both positive or both negative)
- [x] D20 updated to correct SME guidance
- [x] understanding.md updated
- [x] No test regressions (921 passed, 1 skipped, 1 pre-existing flaky)

## Interface Decision
If T×N matrix passed with N>1: **raise ValueError**
Rationale: CPCV evaluates ONE strategy. PBO evaluates N strategies. Mixing interfaces is confusing.
User must select column explicitly: `compute_cpcv(returns[:, i])`

## Files Changed
- `thats_my_quantv1/backtester/pbo.py` - Added CPCVResult + compute_cpcv() (~80 lines)
- `thats_my_quantv1/tests/test_pbo.py` - Added 18 CPCV tests (60 total now)
- `thats_my_quantv1/backtester/__init__.py` - Exported compute_cpcv, CPCVResult
- `.vibe/decisions.md` - Fixed D20 to correct SME guidance
- `.vibe/understanding.md` - Updated CPCV status to ✅

## Progress
- [x] Task tracking created
- [x] CPCV implementation (~80 lines reusing PBO block machinery)
- [x] CPCV tests (18 new tests)
- [x] Exports updated
- [x] D20 fixed (now correctly documents CPCV as gold standard for OOS)
- [x] understanding.md updated
- [x] Tests passing (921 passed)

---

# Previous Task: PBO via CSCV + Neighborhood Degradation

## Status: Complete
(see git history)