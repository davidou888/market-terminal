import csv, random
from datetime import datetime, timedelta

symbols = {
    "GOOGL": 100.00,
    "AMZN":  200.00,
    "TSLA":  200.00,
    "NVDA":  100.00,
}

def generate_csv(symbol, start_price, n=390, volatility=0.003):
    random.seed(hash(symbol))
    prices = [start_price]
    for _ in range(n - 1):
        drift = random.gauss(0.0002, volatility)
        prices.append(round(prices[-1] * (1 + drift), 2))

    start = datetime(2026, 3, 6, 9, 0, 0)
    rows = []
    for i, p in enumerate(prices):
        ts = start + timedelta(minutes=i)
        rows.append({"date": ts.strftime("%Y-%m-%d %H:%M:%S"), "close_price": p})
    return rows

for sym, price in symbols.items():
    rows = generate_csv(sym, price)
    path = f"data/{sym}.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "close_price"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] {sym}: {len(rows)} points | start={rows[0]['close_price']} → end={rows[-1]['close_price']}")
