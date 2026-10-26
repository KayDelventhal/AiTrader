import numpy as np
import pandas as pd


def sma(values, period):
    return pd.Series(values, dtype=float).rolling(period, min_periods=period).mean()


def ema(values, period):
    # Seed with the first complete SMA; recursive alpha = 2/(period+1).
    series = pd.Series(values, dtype=float)
    result = np.full(len(series), np.nan)
    if len(series) >= period:
        result[period - 1] = series.iloc[:period].mean()
        for i in range(period, len(series)):
            result[i] = result[i - 1] + 2 / (period + 1) * (series.iloc[i] - result[i - 1])
    return pd.Series(result)


def wilder(values, period):
    values = np.asarray(values, dtype=float)
    result = np.full(len(values), np.nan)
    if len(values) >= period:
        result[period - 1] = np.mean(values[:period])
        for i in range(period, len(values)):
            result[i] = (result[i - 1] * (period - 1) + values[i]) / period
    return pd.Series(result)


def rsi(values, period=14):
    delta = np.diff(np.asarray(values, dtype=float))
    gain = wilder(np.maximum(delta, 0), period)
    loss = wilder(np.maximum(-delta, 0), period)
    with np.errstate(divide="ignore", invalid="ignore"):
        result = 100 - 100 / (1 + gain / loss)
    result[(loss == 0) & (gain > 0)] = 100
    result[(gain == 0) & (loss > 0)] = 0
    result[(gain == 0) & (loss == 0)] = np.nan
    return pd.Series([np.nan] + result.tolist())


def compute(bars):
    if not bars:
        return {}
    close = pd.Series([b["close"] for b in bars])
    mean = sma(close, 20)
    std = close.rolling(20).std(ddof=0)
    macd = ema(close, 12) - ema(close, 26)
    valid = macd.dropna()
    signal = pd.Series(np.nan, index=macd.index)
    if len(valid):
        signal.loc[valid.index] = ema(valid.tolist(), 9).values
    high = pd.Series([b["high"] for b in bars])
    low = pd.Series([b["low"] for b in bars])
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    series = {"sma20": mean, "sma50": sma(close, 50), "ema20": ema(close, 20), "upper": mean + 2 * std, "lower": mean - 2 * std, "rsi": rsi(close), "macd": macd, "signal": signal, "atr": wilder(tr, 14)}
    return {name: [{"time": bars[i]["time"], "value": round(float(v), 6)} for i, v in enumerate(values) if np.isfinite(v)] for name, values in series.items()}


def signals(close, fast, slow):
    f, s = sma(close, fast), sma(close, slow)
    return (f > s) & (f.shift() <= s.shift()), (f < s) & (f.shift() >= s.shift())
