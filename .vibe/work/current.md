# Current Task: Implement PBO via CSCV + Neighborhood Degradation

## Status: Complete

## Success Criteria
- [x] `pbo.py` implements Bailey et al. (2014) CSCV algorithm
- [x] PBO accepts T×N return matrix, returns PBO scalar + logit distribution
- [x] S=16 blocks by default, C(16,8)=12,870 combinations
- [x] NDR computed at d=1 and d=2 Chebyshev distance
- [x] CV (coefficient of variation) computed for each shell
- [x] Unit tests verify: edge cases, known values, integration with paramsweep
- [x] No test regressions (903 passed, 1 flaky pre-existing failure)

## Implementation Plan

### Task 1: PBO via CSCV (~200 lines)
Location: `thats_my_quantv1/backtester/pbo.py`

Algorithm:
1. Accept return matrix M of shape (T, N)
2. Split M row-wise into S=16 contiguous blocks
3. Generate all C(S, S/2) = C(16,8) combinations
4. For each combination:
   - IS = concatenate S/2 blocks (preserve order)
   - OOS = remaining S/2 blocks
   - Compute Sharpe for all N strategies on IS data
   - Identify n* = argmax(IS Sharpe)
   - Compute Sharpe for all N strategies on OOS data
   - Compute rank of n* in OOS Sharpe ranking
   - Compute logit: λ = log(rank / (N - rank))
5. PBO = fraction of combinations where λ < 0

### Task 2: Neighborhood Degradation (~50 lines)
Location: `thats_my_quantv1/backtester/pbo.py`

Algorithm:
1. Accept parameter sweep results DataFrame with param columns + Sharpe
2. Find optimal parameter vector p*
3. Compute Chebyshev distance for all grid points
4. For d=1 shell: NDR(1) = mean(Sharpe) / Sharpe(p*), CV(1)
5. For d=2 shell: NDR(2) = mean(Sharpe) / Sharpe(p*), CV(2)
6. Return NDRResult dataclass

### Task 3: Tests
Location: `thats_my_quantv1/tests/test_pbo.py`

Test cases:
- Known PBO values (synthetic return matrix)
- Edge case: all identical returns → PBO undefined
- Edge case: one dominant strategy → verify warning
- NDR with simple 3×3 grid
- Integration with actual paramsweep output

## Files to Create/Change
- `thats_my_quantv1/backtester/pbo.py` - NEW
- `thats_my_quantv1/tests/test_pbo.py` - NEW
- `thats_my_quantv1/backtester/__init__.py` - Add exports

## Progress
- [x] Documentation updated with SME corrections
- [x] pbo.py created (370 lines)
- [x] test_pbo.py created (42 tests)
- [x] Tests passing (903 total, 42 new PBO tests)
- [x] Exports added to __init__.py
