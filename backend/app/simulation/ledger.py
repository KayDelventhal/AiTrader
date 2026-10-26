from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def book_fill(cash, positions, instrument_id, side, quantity, price, fee):
    """Exact single-currency accounting. No margin or negative positions."""
    cash, price, fee = money(cash), money(price), money(fee)
    quantity = int(quantity)
    if quantity <= 0 or price <= 0 or fee < 0:
        raise ValueError("Invalid fill")
    updated = {key: dict(value) for key, value in positions.items()}
    old = updated.get(instrument_id, {"quantity": 0, "cost_basis": "0.00", "realized_pnl": "0.00"})
    qty, basis, realized = old["quantity"], money(old["cost_basis"]), money(old["realized_pnl"])
    notional = money(quantity * price)
    if side == "BUY":
        if cash < notional + fee:
            raise ValueError("Insufficient available cash")
        cash -= notional + fee
        basis += notional + fee
        qty += quantity
    elif side == "SELL":
        if qty < quantity:
            raise ValueError("Insufficient position; short selling is disabled")
        released = basis if quantity == qty else money(basis * quantity / qty)
        cash += notional - fee
        realized += notional - fee - released
        basis -= released
        qty -= quantity
    else:
        raise ValueError("Unsupported side")
    updated[instrument_id] = {"quantity": qty, "cost_basis": str(basis), "realized_pnl": str(realized)}
    return str(money(cash)), updated


def fill_price(side, open_price, low, high, order_type="MARKET", trigger=None):
    """Applies only to an order active BEFORE this bar; no retroactive fills."""
    opening = Decimal(str(open_price))
    if order_type == "LIMIT":
        limit = Decimal(str(trigger))
        if side == "BUY":
            return min(opening, limit) if Decimal(str(low)) <= limit else None
        return max(opening, limit) if Decimal(str(high)) >= limit else None
    if order_type == "STOP":
        stop = Decimal(str(trigger))
        if side == "SELL":
            return min(opening, stop) if Decimal(str(low)) <= stop else None
        return max(opening, stop) if Decimal(str(high)) >= stop else None
    if order_type != "MARKET":
        raise ValueError("Unsupported order type")
    return opening
