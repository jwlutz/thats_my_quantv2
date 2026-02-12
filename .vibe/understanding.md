# Project Understanding

**Project**: thats_my_quant
**Updated**: 2026-02-12

## What It Is

A quantitative backtesting and trading platform built from scratch. Two sibling projects in this repo:
- **stone_age** (`data_feed/`) — Streaming statistics engine, the "no AI" learning project
- **thats_my_quantv1** — Event-driven backtester + vectorized screening engine

Same strategy interface, different compute paths. Not parent-child.

---

## Stone Age Engine (`data_feed/`)

**Status**: Complete through Phase 6

| Component | Purpose |
|-----------|---------|
| `StreamProcessor` | Welford's running mean/variance, sliding windows, O(1) per tick |
| Pluggable metrics | `.add_ema()`, `.add_vwap()`, `.add_bollinger()`, `.add_rsi()`, `.add_macd()` — all return refs |
| `Engine` | Hash map routing, one StreamProcessor per symbol, auto-configured via setup |
| `CandleAggregator` | OHLCV from raw ticks, timestamp bucketing via `ts // interval * interval` |
| `AlpacaDataSource` | REST wrapper for historical bars, pagination, .env keys working |

**Tick format**: `{"symbol": "AAPL", "price": 150, "volume": 100, "timestamp": 0}`

---

## Backtester (`thats_my_quantv1/`)

**Status**: Core complete, 786+ tests passing

### Core Components

| Component | Description |
|-----------|-------------|
| `backtester.py` | Event-driven bar-by-bar simulation, 884 lines (manageable, don't decompose) |
| `RoundTrip` | DCA support, MAE/MFE tracking, `average_fill_price` vs `cost_basis` separation |
| `FillModel` | ABC with `FixedSlippage`, `VolumeProportional`, `SqrtImpactSlippage` (Almgren σ·√(Q/V)) |
| `FillTiming` | Enum: `CURRENT_BAR_CLOSE` (default, backward compat), `NEXT_BAR_OPEN` (SME-recommended) |
| Exit Rules | `Calculation + Condition` pattern (same as entry). `CompositeExitRule` first-to-trigger-wins |
| `CalculationBasedExit` | Indicator-driven exits: `CalculationBasedExit(RSI(14), GreaterThan(70))` |
| Position Sizing | `PositionSizer` classes owned by Strategy. Separate PortfolioManager deferred. |

### Vectorized Engine

| Metric | Value |
|--------|-------|
| File | `vectorized.py` (~870 lines) |
| Tests | 69 passing |
| Total tests | 786+ passing |
| Cross-engine parity | RSI indicator match, trade count exact, returns within 5%, Sharpe within 0.1 |

---

## Architecture (Three-Tier)

```
┌─────────────────────────────────────────────────────────────────┐
│  ADAPTERS                                                       │
│  MCP Server | REST API | WebSocket (live UI) | CLI | Python    │
│  Core never knows who's calling                                 │
├─────────────────────────────────────────────────────────────────┤
│  SERVICE                                                        │
│  Thin API: create_strategy, run_backtest, get_indicators,      │
│  place_trade                                                    │
├─────────────────────────────────────────────────────────────────┤
│  CORE                                                           │
│  Pure Python library: Engine, indicators, position tracker,     │
│  strategy runner, backtester                                    │
│  from thats_my_quant import Engine, Backtest                   │
└─────────────────────────────────────────────────────────────────┘
```

### Dual Compute Paths

| Path | Use Case | Engine |
|------|----------|--------|
| Batch backtesting | Fast screening, parameter sweeps | pandas/numpy vectorized |
| Live trading / sim | Tick-by-tick, O(1), can't look ahead | stone_age streaming |
| **Shared** | Strategy interface, position tracker, fill models, results analysis | — |

---

## SME Guidance (Locked-In Decisions)

| Decision | Rationale |
|----------|-----------|
| Fill at next-bar open for daily bars | Same-bar close = lookahead bias |
| Slippage: σ·√(Q/V) for validation | Fixed for screening, add 10-20bps to vectorized screener |
| Deflated Sharpe Ratio > Monte Carlo | Primary statistical gate |
| PBO via CSCV > heatmap eyeballing | PBO > 0.40 = suspicious, > 0.55 = reject. Uses Bailey et al. CSCV algorithm |
| CPCV for OOS estimation | Gold standard for generalization testing, tighter CIs than WFE |
| No HMMs for regime detection | Unstable OOS. Observable indicators only. |
| Survivorship bias awareness | 20%+ CAGR → <8% on momentum strategies |
| Adjusted prices for backtesting | Unadjusted for price filters and dollar volume sizing |
| Storage: Parquet + DuckDB | For sweep results |

---

## Build Status

| Feature | Status |
|---------|--------|
| Streaming engine (stone_age) | ✅ Phases 1-6 |
| Alpaca data source | ✅ |
| Event-driven backtester | ✅ 786+ tests |
| FillModel + MAE/MFE | ✅ |
| Exit rule refactor | ✅ |
| Fill timing config | ✅ |
| SqrtImpactSlippage | ✅ |
| Vectorized screening engine | ✅ 69 tests, cross-engine validated |
| RSI Calculation class | ✅ Parity proven |
| Visual checkpoint (matplotlib) | ✅ Results.plot() |
| Deflated Sharpe Ratio (DSR) | ✅ `paramsweep.py` |
| Purged K-Fold CV | ✅ `paramsweep.py` |
| Parameter Sweep (5 diagnostics) | ✅ `paramsweep.py` |
| Walk-Forward Analysis | ✅ `walkforward.py` |
| Monte Carlo (trade shuffle) | ✅ `results.py` |
| Permutation Test | ✅ `results.py` |
| Bootstrap Paths | ✅ `results.py` |
| Regime Tagger | ✅ `regime.py` |
| PBO via CSCV | ✅ `pbo.py` | Bailey et al. (2014) algorithm |
| Neighborhood Degradation | ✅ `pbo.py` | NDR at d=1 and d=2 |
| RobustnessVerdict | ✅ `pbo.py` | Traffic light system (GREEN/YELLOW/RED) |
| CPCV (OOS Performance Estimation) | ✅ `pbo.py` | 12,870 paths for tight CIs |
| MCP server | ❌ |
| Position sizing as separate layer | ⚠️ Partial |
| Adjusted vs unadjusted prices | ❌ Data layer |
| Polygon integration | ❌ |
| Survivorship bias / universe snapshots | ❌ |
| Terminal UI (vibecoded) | ❌ |
| Options pricer | ✅ European + American + Greeks + IV + live data + 5 plots |

---

## Build Order From Here

1. ~~**Visual checkpoint**~~ ✅ `Results.plot()` implemented — unified 2-panel dashboard (equity + drawdown)

2. ~~**Robustness suite**~~ ✅ — DSR ✅, permutation test ✅, bootstrap CI ✅, WFE ✅, PBO ✅, NDR ✅, CPCV ✅, RobustnessVerdict ✅

3. **MCP server** — Use official `mcp` Python SDK (FastMCP). Service layer emerges naturally from "what tools does Claude need?" Build as `thats_my_quant/service/` when needed.

4. **Terminal UI** — vibecoded React + lightweight-charts. Chat left, chart right.

5. **Polygon data layer** — Check WRDS/CRSP first (free through UCLA, gold standard for survivorship-bias-free data). If access takes >1 week, build against Polygon free tier and swap in CRSP later. DataProvider ABC makes switch painless.

6. ~~**Options pricer**~~ ✅ — `options_pricer/` complete (69 tests passing)

---

## Architecture Decisions (2026-02-12)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Repo structure | Monorepo | stone_age + thats_my_quantv1 stay together |
| Visual checkpoint | `Results.plot()` method | Already has matplotlib, one call away |
| Data source priority | WRDS/CRSP → Polygon fallback | CRSP is gold standard, free through UCLA |
| Service layer | Defer to MCP phase | Design emerges from "what tools does Claude need?" |
| MCP framework | Official `mcp` SDK (FastMCP) | Handles JSON-RPC, no value in rolling own |
| Service location | `thats_my_quant/service/` | When built, inside monorepo |

---

## Product Vision

**thats_my_quant** = natural language → strategy → backtest → execution

- Streaming-native (same code path backtest and live)
- Transparent engine (not a black box)
- Target audience: students and aspiring quants

**Revenue model**:
- Subscription: $10-20/mo students, $50+ serious
- Future: opt-in prop desk model (user shares strategy, you allocate capital, split profits)

---

## Key Files Quick Reference

| Purpose | File |
|---------|------|
| Main backtester | `thats_my_quantv1/backtester/backtester.py` |
| Vectorized engine | `thats_my_quantv1/backtester/vectorized.py` |
| Strategy definition | `thats_my_quantv1/backtester/strategy.py` |
| Exit rules | `thats_my_quantv1/backtester/exitrule.py` |
| Fill models | `thats_my_quantv1/backtester/fill_model.py` |
| RSI Calculation | `thats_my_quantv1/backtester/calculation.py` |
| Public API | `thats_my_quantv1/backtester/__init__.py` |
| Streaming stats | `data_feed/streamprocessor.py` |
| Multi-symbol router | `data_feed/engine.py` |
| Candle aggregator | `data_feed/candle.py` |
| European options | `options_pricer/european.py` |
| American options | `options_pricer/american.py` |
| IV solver | `options_pricer/implied_vol.py` |
| Options visuals | `options_pricer/visuals.py` |

---

## Glossary

| Term | Definition |
|------|------------|
| RoundTrip | Complete position lifecycle from first entry to final exit, supports DCA and partial exits |
| Calculation | Data extraction component (e.g., `RSI(14)` computes RSI value) |
| Condition | Decision logic component (e.g., `GreaterThan(70)`) |
| Welford's Algorithm | Numerically stable online algorithm for running mean/variance in O(1) |
| DSR | Deflated Sharpe Ratio — adjusts for multiple testing |
| CPCV | Combinatorial Purged Cross-Validation — OOS performance with 12,870 paths for tight CIs |
| CSCV | Combinatorially Symmetric Cross-Validation — algorithm for computing PBO |
| PBO | Probability of Backtest Overfitting — fraction of combinations where IS-optimal underperforms OOS median |
| NDR | Neighborhood Degradation Ratio — robustness metric: mean(Sharpe in neighborhood) / Sharpe(optimal) |
| MAE/MFE | Maximum Adverse/Favorable Excursion |
| WFE | Walk-Forward Efficiency |
