# Codebase Understanding

Generated: 2026-02-11

## Summary
A monorepo containing two related quantitative trading projects: `thats_my_quantv1` (a modular transaction-based backtesting framework validated against Backtrader) and `data_feed` (a streaming statistics engine for real-time trading metrics).

## Architecture
- **Type**: Python quantitative trading toolkit (backtesting + streaming analytics)
- **Languages**: Python 3.11+
- **Entry points**:
  - `thats_my_quantv1/examples/demo.py` - Backtester demo
  - `data_feed/engine.py` - Streaming stats engine
- **Organization**: Two independent subprojects, each with its own git repo

---

## Components

### thats_my_quantv1/backtester

#### Backtester Engine
- **Path**: `thats_my_quantv1/backtester/backtester.py`
- **Purpose**: Main simulation engine that runs strategies over historical data
- **Key classes**: `Backtester`
- **Depends on**: Strategy, Portfolio, DataProvider, Results

#### Strategy
- **Path**: `thats_my_quantv1/backtester/strategy.py`
- **Purpose**: Bundles entry rules, exit rules, position sizer, and universe
- **Key classes**: `Strategy`
- **Depends on**: EntryRule, ExitRule, PositionSizer, DataProvider

#### Portfolio
- **Path**: `thats_my_quantv1/backtester/portfolio.py`
- **Purpose**: Manages cash, positions (RoundTrips), and transaction history
- **Key classes**: `Portfolio`
- **Depends on**: RoundTrip, Transaction, TransactionCost

#### Transaction & RoundTrip
- **Path**: `thats_my_quantv1/backtester/transaction.py`, `roundtrip.py`
- **Purpose**: Immutable trade records and position lifecycle tracking (supports DCA, partial exits)
- **Key classes**: `Transaction` (frozen dataclass), `RoundTrip`
- **Depends on**: None (base classes)

#### Entry Rules
- **Path**: `thats_my_quantv1/backtester/entryrule.py`, `calculation.py`, `condition.py`
- **Purpose**: Composable entry signal generation using Calculation + Condition pattern
- **Key classes**: `EntryRule`, `CompositeEntryRule`, `Signal`, `Calculation` (ABC), `Condition` (ABC)
- **Depends on**: DataProvider

#### Exit Rules
- **Path**: `thats_my_quantv1/backtester/exitrule.py`
- **Purpose**: Define when to close positions (stop loss, profit target, trailing stop, time-based)
- **Key classes**: `ExitRule` (ABC), `StopLossExit`, `ProfitTargetExit`, `TrailingStopExit`, `TimeBasedExit`, `CompositeExitRule`
- **Depends on**: RoundTrip

#### Position Sizers
- **Path**: `thats_my_quantv1/backtester/positionsizer.py`
- **Purpose**: Calculate position sizes (fixed dollar, percent portfolio, risk parity, etc.)
- **Key classes**: `PositionSizer` (ABC), `FixedDollarAmount`, `PercentPortfolio`, `RiskParity`, `EqualWeight`, `FixedShares`
- **Depends on**: Portfolio

#### Data Provider
- **Path**: `thats_my_quantv1/backtester/dataprovider.py`, `yfinance_provider.py`
- **Purpose**: Abstract data interface with yfinance implementation (prices, OHLCV, earnings, fundamentals)
- **Key classes**: `DataProvider` (ABC), `YFinanceProvider`
- **Depends on**: yfinance, pandas

#### Results
- **Path**: `thats_my_quantv1/backtester/results.py`
- **Purpose**: Performance metrics, visualization, and reporting
- **Key classes**: `Results`
- **Depends on**: Portfolio, pandas, matplotlib

---

### data_feed (Streaming Statistics Engine)

#### StreamProcessor
- **Path**: `data_feed/streamprocessor.py`
- **Purpose**: O(1) streaming statistics using Welford's algorithm (mean, variance, std)
- **Key classes**: `StreamProcessor`, `EMA`, `VWAP`, `BollingerBands`, `RSI`, `MACD`
- **Depends on**: Candle

#### Engine
- **Path**: `data_feed/engine.py`
- **Purpose**: Multi-symbol tick router (hash map of symbol -> StreamProcessor)
- **Key classes**: `Engine`
- **Depends on**: StreamProcessor

#### Candle Aggregator
- **Path**: `data_feed/candle.py`
- **Purpose**: Aggregate raw ticks into OHLCV candles by time bucket
- **Key classes**: `Candle`, `CandleAggregator`
- **Depends on**: None

---

## Data Flow

### Backtester Flow
```
Strategy Definition
       |
       v
Backtester.run()
       |
       +---> Preload Data (YFinanceProvider)
       |
       v
For each trading day:
       |
       +---> Check Exits (ExitRule.should_exit)
       |         |
       |         v
       |     Portfolio.close_position / reduce_position
       |
       +---> Generate Signals (EntryRule.should_enter)
       |         |
       |         +---> Calculation.calculate()
       |         +---> Condition.check()
       |         v
       |     List[Signal] sorted by priority
       |
       +---> Process Entries
       |         |
       |         +---> PositionSizer.calculate_shares()
       |         v
       |     Portfolio.open_position()
       |
       v
Results (metrics, equity curve, visualizations)
```

### Streaming Engine Flow
```
Raw Tick Data {symbol, price, volume, timestamp}
       |
       v
Engine.update(tick)
       |
       +---> Route to StreamProcessor[symbol]
       |
       v
StreamProcessor.update(tick)
       |
       +---> Welford update (mean, variance, M2)
       +---> Update min/max
       +---> Update window (if configured)
       +---> Update attached metrics (EMA, VWAP, RSI, etc.)
       +---> Update candle aggregator (if attached)
       |
       v
Live Statistics Available
```

---

## Patterns

- **Calculation + Condition**: Entry rules separate data extraction (Calculation) from decision logic (Condition) for reusability
- **Composite Pattern**: `CompositeEntryRule` (AND logic), `CompositeExitRule` (first-match-wins priority)
- **ABC + Factory**: Abstract base classes with `create_*()` factory functions for YAML serialization
- **Transaction-based P&L**: Every buy/sell is a `Transaction`; `RoundTrip` groups related transactions for accurate cost basis
- **Welford's Algorithm**: O(1) streaming mean/variance with numerical stability
- **Immutable Records**: `Transaction` uses frozen dataclass for data integrity
- **Caching**: DataProvider caches OHLCV and earnings data for performance

---

## Risks

### 🟡 Warning

1. **YFinanceProvider timezone issues** - `get_bar()` returns Series instead of dict when index has duplicates; timezone-aware vs timezone-naive comparison issues in `get_earnings_data()` (documented in [FIXES_NEEDED.md](thats_my_quantv1/additional_docs/FIXES_NEEDED.md))

2. **No look-ahead bias validation** - While the design attempts point-in-time accuracy, there's no automated check to ensure calculations don't accidentally use future data

3. **Single-threaded** - Both backtester and streaming engine are single-threaded; may be bottleneck for large universes or high-frequency data

4. **yfinance rate limits** - Heavy reliance on yfinance which has API rate limits; no offline data storage yet

### 📝 TODOs / Future Ideas

- Phase 4/5 of backtester still to complete (see [to_do.md](thats_my_quantv1/additional_docs/to_do.md))
- Data feed: Phases 3-8 incomplete (EMA, VWAP, multi-symbol, candle aggregation, live ingestion)
- Future: vectorize with numba, ML strategies, MCP integration for AI agents
- Future: survivorship-bias-free data, delisted securities, corporate actions

---

## Glossary

- **RoundTrip**: A complete position lifecycle from first entry to final exit, supporting DCA and partial exits
- **Calculation**: Data extraction component (e.g., `DayChange` extracts `(close-open)/open`)
- **Condition**: Decision logic component (e.g., `LessThan(-0.02)` checks if value < -2%)
- **Signal**: Entry signal with ticker, date, type, metadata, and priority
- **Welford's Algorithm**: Numerically stable online algorithm for computing running mean and variance in O(1)
- **VWAP**: Volume-Weighted Average Price
- **EMA**: Exponential Moving Average
- **DCA**: Dollar Cost Averaging - adding to positions over time
- **CompositeExitRule**: Priority-ordered exit rules where first match wins

---

## Test Coverage

| Component | Tests | Status |
|-----------|-------|--------|
| Transaction | 21 | Passing |
| RoundTrip | 40+ | Passing |
| TransactionCost | 40+ | Passing |
| Portfolio | 33 | Passing |
| YFinanceProvider | 37 | Passing |
| Calculation | 39 | Passing |
| Condition | 44 | Passing |
| EntryRule | 27 | Passing |
| ExitRule | 57 | Passing |
| **Total** | **379** | **100%** |

---

## Key Files Quick Reference

| Purpose | File |
|---------|------|
| Main engine | `thats_my_quantv1/backtester/backtester.py` |
| Strategy definition | `thats_my_quantv1/backtester/strategy.py` |
| Public API | `thats_my_quantv1/backtester/__init__.py` |
| Example usage | `thats_my_quantv1/examples/demo.py` |
| Spec/design doc | `thats_my_quantv1/SPEC.md` |
| Streaming stats | `data_feed/streamprocessor.py` |
| Multi-symbol router | `data_feed/engine.py` |
| Project config | `thats_my_quantv1/pyproject.toml` |
