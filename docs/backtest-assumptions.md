# Backtest assumptions

The actual vectorbt Community engine runs fixed-size long-only SMA crossover experiments. Default fast/slow periods are 20/50; entry/exit crossovers need complete warm-up. A close-based signal is shifted one row forward and executed at the following fixture open. Whole-share size is known before the fill. Cash starts at EUR 10,000.

Default fees are 10 bps and slippage 5 bps. A second calculation adds 10 bps to each to show adverse cost sensitivity. The manual simulator's EUR 1 minimum fee is a different explicit fill contract and is not silently applied to vectorbt.

Outputs include total return, maximum drawdown, closed trades, win rate (null when undefined), equity, raw benchmark values, orders/fees, versions and snapshot hash. The displayed equity chart currently shows the strategy; benchmark comparison UI is pending. No CAGR, Sharpe, Sortino, train/test split, optimization, or walk-forward performance is claimed.

Fixture bars use a synthetic weekday calendar, have no corporate actions, and are all in EUR. Missing real FX, bid/ask depth, exchange calendars, survivorship-aware universes, and realistic liquidity prohibit treating these numbers as investment evidence.

Indicator definitions: SMA arithmetic full-window mean; EMA seeded by first full SMA with alpha=2/(n+1); Wilder RSI uses averaged gains/losses then alpha=1/n, a flat series is undefined; MACD=EMA12−EMA26, signal=EMA9 of valid MACD; Bollinger=SMA20±2 population standard deviations; ATR is Wilder14 of true ranges. Tests use independent small reference values.
