"""Sales report API ¡ª intentionally slow for optimization exercise."""
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class Order:
    id: int
    user_id: int
    product: str
    amount: float
    month: str

# Simulated "database" with 10k records
def _load_orders() -> list[Order]:
    orders = []
    products = ["Widget", "Gadget", "Doodad"]
    months = ["2024-01", "2024-02", "2024-03"]
    for i in range(10000):
        orders.append(Order(
            id=i,
            user_id=i % 500,
            product=products[i % 3],
            amount=10.0 + (i % 100),
            month=months[i % 3],
        ))
    return orders

# BUG: loaded on every request instead of once
def get_report(month: Optional[str] = None):
    orders = _load_orders()  # BUG: regenerates every call
    if month:
        orders = [o for o in orders if o.month == month]
    
    # BUG: nested loops ¡ª O(n*m) instead of single pass
    total = 0.0
    by_product = {}
    for p in ["Widget", "Gadget", "Doodad"]:
        for o in orders:
            if o.product == p:
                total += o.amount
                by_product[p] = by_product.get(p, 0.0) + o.amount
    
    # BUG: sort then list comp for no reason
    sorted_orders = sorted(orders, key=lambda o: o.amount, reverse=True)
    report = []
    for o in sorted_orders:
        report.append(o)
    
    return {
        "total": total,
        "by_product": by_product,
        "top_orders": [
            {"id": o.id, "amount": o.amount} for o in report[:5]
        ],
    }
