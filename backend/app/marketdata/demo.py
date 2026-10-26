"""Versioned fictional fixture generator. Never used as a provider fallback."""
import math
import random
from datetime import datetime, timedelta, timezone

DATASET_VERSION = "fictional-eur-daily-v1"


def generate_bars(seed: int, base: float, count: int = 280) -> list[dict]:
    rng = random.Random(seed)
    day = datetime(2025, 9, 29, 16, tzinfo=timezone.utc)
    bars = []
    previous = base
    while len(bars) < count:
        if day.weekday() < 5:
            i = len(bars)
            opening = previous * (1 + rng.uniform(-0.005, 0.005))
            close = base * (1 + i * 0.0009 + 0.065 * math.sin(i / 17 + seed) + 0.025 * math.sin(i / 5))
            close *= 1 + rng.uniform(-0.006, 0.006)
            bars.append({"time": int(day.timestamp()), "open": round(opening, 2), "high": round(max(opening, close) * (1 + rng.uniform(0.003, 0.014)), 2), "low": round(min(opening, close) * (1 - rng.uniform(0.003, 0.014)), 2), "close": round(close, 2), "volume": rng.randint(120000, 950000), "final": True, "available_at": day.isoformat(), "revision": 1})
            previous = close
        day += timedelta(days=1)
    return bars


def visible_bars(bars: list[dict], as_of: int | None):
    return [b for b in bars if b["final"] and (as_of is None or b["time"] <= as_of)]
