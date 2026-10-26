from decimal import Decimal
import numpy as np
import pytest
from app.quant.indicators import sma, ema, rsi, compute, signals
from app.simulation.ledger import book_fill, fill_price
from app.marketdata.demo import generate_bars, visible_bars
from app.quant.backtest import VectorbtResearchAdapter


def test_sma_and_ema_independent_values():
    values = [1, 2, 3, 4, 5]
    np.testing.assert_allclose(sma(values, 3), [np.nan, np.nan, 2, 3, 4], equal_nan=True)
    np.testing.assert_allclose(ema(values, 3), [np.nan, np.nan, 2, 3, 4], equal_nan=True)
    np.testing.assert_allclose(ema([1, 2, 3, 7], 3), [np.nan, np.nan, 2, 4.5], equal_nan=True)


def test_wilder_rsi_known_seed_and_update():
    # Changes +1, -1, +2 => average gain 1, loss 1/3 => RSI 75.
    # Next change -1 => gains 2/3, losses 5/9 => RSI 600/11.
    result = rsi([10, 11, 10, 12, 11], 3)
    assert result.iloc[3] == pytest.approx(75)
    assert result.iloc[4] == pytest.approx(600 / 11)
    assert rsi([1, 2, 3, 4], 3).iloc[-1] == 100
    assert rsi([4, 3, 2, 1], 3).iloc[-1] == 0
    assert np.isnan(rsi([1, 1, 1, 1], 3).iloc[-1])


def test_macd_atr_warmup_and_finite_output():
    bars = [{"time": i + 1, "open": float(i + 10), "close": float(i + 10), "high": float(i + 11), "low": float(i + 9), "volume": 10} for i in range(50)]
    result = compute(bars)
    assert result["macd"][0]["time"] == 26
    assert result["macd"][0]["value"] == pytest.approx(7)
    assert result["signal"][0]["time"] == 34
    assert result["signal"][0]["value"] == pytest.approx(7)
    assert result["atr"][0]["value"] == 2
    assert compute([]) == {}


def test_exact_ledger_acceptance_a13():
    cash, positions = book_fill("1000", {}, "DEMO", "BUY", 2, "100", "1")
    assert cash == "799.00"
    assert positions["DEMO"]["cost_basis"] == "201.00"
    cash, positions = book_fill(cash, positions, "DEMO", "SELL", 2, "110", "1")
    assert cash == "1018.00"
    assert positions["DEMO"]["realized_pnl"] == "18.00"
    assert positions["DEMO"]["quantity"] == 0


def test_partial_sell_preserves_basis():
    cash, positions = book_fill("1000", {}, "X", "BUY", 3, "100", "1")
    cash, positions = book_fill(cash, positions, "X", "SELL", 1, "110", "1")
    assert positions["X"]["cost_basis"] == "200.67"
    cash, positions = book_fill(cash, positions, "X", "SELL", 2, "110", "1")
    assert positions["X"]["cost_basis"] == "0.00"
    assert cash == "1027.00"


@pytest.mark.parametrize("args", [("1", {}, "X", "BUY", 2, "100", "1"), ("1000", {}, "X", "SELL", 1, "100", "1"), ("1000", {}, "X", "BUY", 0, "100", "1"), ("1000", {}, "X", "BUY", 1, "-100", "1"), ("1000", {}, "X", "BUY", 1, "100", "-1"), ("1000", {}, "X", "SHORT", 1, "100", "1")])
def test_ledger_rejects_invalid_fills(args):
    with pytest.raises(ValueError):
        book_fill(*args)


def test_limit_stop_gap_semantics_a31():
    assert fill_price("BUY", 103, 101, 105, "LIMIT", 100) is None
    assert fill_price("BUY", 98, 97, 102, "LIMIT", 100) == Decimal("98")
    assert fill_price("SELL", 90, 88, 94, "STOP", 95) == Decimal("90")
    assert fill_price("SELL", 110, 105, 112, "LIMIT", 108) == Decimal("110")
    assert fill_price("BUY", 110, 105, 112, "STOP", 108) == Decimal("110")
    with pytest.raises(ValueError):
        fill_price("BUY", 1, 1, 1, "UNSUPPORTED")


def test_no_future_price_changes_past_signal_a14():
    original = np.arange(1, 101, dtype=float)
    changed = original.copy(); changed[70:] = 10000
    a = signals(original, 5, 20)
    b = signals(changed, 5, 20)
    for x, y in zip(a, b):
        np.testing.assert_array_equal(x.iloc[:70].to_numpy(), y.iloc[:70].to_numpy())


def test_deterministic_bars_ohlc_and_replay():
    bars = generate_bars(7, 100)
    assert bars == generate_bars(7, 100)
    assert len({b["time"] for b in bars}) == len(bars)
    assert all(b["low"] <= min(b["open"], b["close"]) <= max(b["open"], b["close"]) <= b["high"] for b in bars)
    assert all(b["volume"] >= 0 for b in bars)
    assert len(visible_bars(bars, bars[40]["time"])) == 41


def test_real_vectorbt_execution_and_cost_sensitivity():
    spec = {"fast": 5, "slow": 15, "size": 2, "fees_bps": 10, "slippage_bps": 5}
    result = VectorbtResearchAdapter().run(generate_bars(7, 100, 150), spec)
    assert result["engine"] == "vectorbt"
    assert result["orders"]
    assert all(o["signal_time"] < o["time"] for o in result["orders"])
    assert result["stress_return_pct"] < result["return_pct"]
    assert len(result["snapshot_hash"]) == 64
    assert len(result["equity"]) == 150
