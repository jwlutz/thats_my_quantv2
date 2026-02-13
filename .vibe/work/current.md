# Current Task: Backtester Audit Fix Implementation
**Started:** 2026-02-12
**Status:** Complete

## Task
Document and fix all issues identified in the comprehensive backtester audit.

## Success Criteria
- [x] All CRITICAL and HIGH issues documented with rationale
- [x] C1: Default fill_timing changed to NEXT_BAR_OPEN
- [x] H1: EqualWeight position sizer fixed
- [x] H2: TrailingStopExit state leak fixed
- [x] M1: Delisted stock handling fixed
- [x] M2: CAGR calculation standardized (documented)
- [x] Documentation updates for H3, H4, M4, L3, C3
- [x] All 936 tests pass (1 skipped)
- [x] Adversarial review completed
- [x] Code simplification pass completed

## Changes Made

### Phase 1: Documentation
- Created `.vibe/audit/2026-02-12-comprehensive-audit.md`

### Phase 2: Implementation
- **backtester.py**: Changed default fill_timing to NEXT_BAR_OPEN, added survivorship bias warning
- **positionsizer.py**: Fixed EqualWeight to divide by remaining_slots instead of max_positions
- **exitrule.py**: Removed _peak_prices dict from TrailingStopExit, uses RoundTrip.mfe instead
- **exitrule.py**: Added documentation for StopLossExit cost_basis behavior
- **results.py**: Added documentation for Monte Carlo dollar P&L limitation
- **vectorized.py**: Added documentation for win rate open position behavior
- **risks.md**: Added new risks R6-R10, documented resolved risks from audit
- **test_montecarlo.py**: Fixed test isolation bug (create_mock_results was polluting Results class)

## Decisions Made

### D1: Fill Timing Default
- **Decision:** Change default from CURRENT_BAR_CLOSE to NEXT_BAR_OPEN
- **Rationale:** NEXT_BAR_OPEN is more realistic for daily bars; prevents look-ahead bias

### D2: EqualWeight Implementation
- **Decision:** Calculate based on remaining slots, not total max_positions
- **Rationale:** True equal weighting means each position gets equal portion of available capital

### D3: TrailingStopExit State
- **Decision:** Use RoundTrip.mfe instead of maintaining separate _peak_prices dict
- **Rationale:** MFE already tracks maximum favorable excursion; eliminates state leak bug

### D4: CAGR Standardization
- **Decision:** Standardize on calendar days (365.25) in both engines
- **Rationale:** Matches financial industry convention; Results class is the "source of truth"

### D5: Delisted Stock Handling
- **Decision:** Force-close at $0 with reason "delisted"
- **Rationale:** Proper accounting; records loss transaction; clears from open_roundtrips

## Files Modified
- `backtester/backtester.py` - fill_timing default, survivorship bias warning
- `backtester/positionsizer.py` - EqualWeight remaining_slots fix
- `backtester/exitrule.py` - TrailingStopExit mfe fix, StopLossExit docs
- `backtester/results.py` - Monte Carlo documentation
- `backtester/vectorized.py` - win rate documentation
- `.vibe/risks.md` - new risks and resolved risks
- `.vibe/audit/2026-02-12-comprehensive-audit.md` - comprehensive audit report
- `tests/test_montecarlo.py` - test isolation fix

---

# Previous Task: MCP Server v1 (backtest tool)

## Status: Complete

## Goal
Implement MCP server skeleton with `backtest` tool.

## Files Created
```
thats_my_quantv1/service/
├── __init__.py
├── mcp_server.py
└── state.py

thats_my_quantv1/tests/
└── test_mcp_service.py
```