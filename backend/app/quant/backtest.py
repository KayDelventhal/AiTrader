import hashlib
import json
import numpy as np
import pandas as pd
from app.quant.indicators import signals
from app.marketdata.demo import DATASET_VERSION


class VectorbtResearchAdapter:
    def run(self, bars, spec):
        import vectorbt as vbt
        index = pd.to_datetime([b["time"] for b in bars], unit="s", utc=True)
        close = pd.Series([b["close"] for b in bars], index=index)
        opening = pd.Series([b["open"] for b in bars], index=index)
        entry, exit_ = signals(close.to_numpy(), spec["fast"], spec["slow"])
        # Decide at close. Earliest execution is the NEXT fixture bar's open.
        entries = pd.Series(entry.shift(1, fill_value=False).to_numpy(), index=index)
        exits = pd.Series(exit_.shift(1, fill_value=False).to_numpy(), index=index)
        kwargs = dict(entries=entries, exits=exits, price=opening, size=spec["size"], init_cash=10000, direction="longonly", freq="1D")
        pf = vbt.Portfolio.from_signals(close, fees=spec["fees_bps"] / 10000, slippage=spec["slippage_bps"] / 10000, **kwargs)
        stress = vbt.Portfolio.from_signals(close, fees=(spec["fees_bps"] + 10) / 10000, slippage=(spec["slippage_bps"] + 10) / 10000, **kwargs)
        equity = pf.value()
        records = []
        for r in pf.orders.records.to_dict("records"):
            i = int(r["idx"])
            records.append({"time": int(bars[i]["time"]), "signal_time": int(bars[i - 1]["time"]), "side": "BUY" if int(r["side"]) == 0 else "SELL", "quantity": float(r["size"]), "price": float(r["price"]), "fees": float(r["fees"])})
        closed = pf.trades.closed
        def finite(value):
            return float(value) if np.isfinite(value) else None
        return {"engine": "vectorbt", "engine_version": vbt.__version__, "dataset": DATASET_VERSION, "snapshot_hash": hashlib.sha256(json.dumps(bars, sort_keys=True).encode()).hexdigest(), "currency": "EUR", "initial_cash": "10000.00", "final_equity": round(float(equity.iloc[-1]), 2), "return_pct": float(pf.total_return()) * 100, "max_drawdown_pct": float(pf.max_drawdown()) * 100, "closed_trades": int(closed.count()), "win_rate_pct": finite(closed.win_rate() * 100) if closed.count() else None, "stress_return_pct": float(stress.total_return()) * 100, "orders": records, "equity": [{"time": bars[i]["time"], "value": round(float(value), 2)} for i, value in enumerate(equity)], "benchmark": [{"time": bars[i]["time"], "value": round(10000 * b["close"] / bars[0]["close"], 2)} for i, b in enumerate(bars)], "assumptions": ["Fictional EUR daily bars; synthetic weekday calendar, not an exchange calendar.", "Close crossover signals execute at the next bar open with explicit fees and slippage.", "Fixed whole-share position size; long-only; no borrowing.", "Full-sample exploratory result, not an out-of-sample validation or live performance claim.", "No bid/ask depth, corporate actions, dividends or FX. Buy-and-hold benchmark excludes trading costs."]}
