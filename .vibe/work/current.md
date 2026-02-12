# Current Task: MCP Server v1 (backtest tool)

## Status: In Progress

## Goal
Implement MCP server skeleton with `backtest` tool — the foundation for Claude to interact with the backtester.

## Design (Locked)
- **4 tools**: backtest, validate, scan, plot
- **2 ID namespaces**: `bt_xxx` (backtest), `sw_xxx` (sweep)
- **State**: In-memory dict (dies with process, fine for v1)
- **Cache**: Use YFinanceProvider's in-memory cache (parquet persistence is v2)
- **Error envelope**: `{"status": "ok/error", "data/error_code/message": ...}`
- **Auth**: None for v1 (local execution)

## Success Criteria
- [ ] Server starts without error
- [ ] `backtest` tool accepts strategy dict, returns `bt_xxx` ID + metrics
- [ ] Results stored in-memory, retrievable by ID
- [ ] Error envelope on success and failure
- [ ] Invalid strategy dict returns proper error (not crash)
- [ ] Test: round-trip RSI strategy → metrics match direct `Backtester.run()`

## Files to Create
```
thats_my_quantv1/service/
├── __init__.py
├── mcp_server.py    # FastMCP server + backtest tool
└── state.py         # BacktestStore (in-memory dict)
```

## Progress
- [ ] service/ folder structure
- [ ] state.py (BacktestStore)
- [ ] mcp_server.py with backtest tool
- [ ] Basic test
- [ ] Server starts and works

## Decisions Made
(will be updated as we go)

---

# Previous Task: Options Pricer Implementation

## Status: Complete ✅
~1,500 lines of code, 81 tests, all passing.
