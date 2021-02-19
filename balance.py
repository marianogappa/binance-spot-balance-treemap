import os
import json
from binance.client import Client

# This is the ONLY interaction with Binance: getting your balances and the current market status.
client = Client(os.environ.get('BINANCE_RO_API_KEY'), os.environ.get('BINANCE_RO_SECRET'))
account = client.get_account()
tickers = client.get_ticker()

def getTickerMapIn(symbol, tickers):
    return {
        t["symbol"][:-len(symbol)] : {"$": float(t["lastPrice"]), "%": float(t["priceChangePercent"])}
        for t in tickers if t["symbol"][-len(symbol):] == symbol
    }

balances = {b["asset"] : float(b["free"])+float(b["locked"]) for b in account["balances"]}
in_btc = getTickerMapIn("BTC", tickers)
in_bnb = getTickerMapIn("BNB", tickers)
in_usdt = getTickerMapIn("USDT", tickers)

# Calculate balances in BTC, and 24-hour % changes.
balances_in_btc = {}
for k, v in balances.items():
    if k == "BTC":
        balances_in_btc[k] = {"$": v, "%": in_usdt["BTC"]["%"]}
    elif k == "USDT":
        balances_in_btc[k] = {"$": v * (1/in_usdt["BTC"]["$"]), "%": 0}
    elif in_btc.get(k):
        balances_in_btc[k] = {"$": v*in_btc[k]["$"], "%": in_btc[k]["%"]}
    elif not in_btc.get(k) and in_bnb.get(k):
        btc_pct = in_btc["BNB"]["%"] / 100.0 + 1
        bnb_pct = in_bnb[k]["%"] / 100.00 + 1
        pct = (btc_pct * bnb_pct - 1) * 100
        balances_in_btc[k] = {"$": v*in_bnb[k]["$"]*in_btc["BNB"]["$"], "%": pct}

# Filter out balances that are too small.
relevant_balances_in_bnb = { k: v for k, v in balances_in_btc.items() if v["$"] > 0.05 }

# Output results in a format that can be read by a local HTML file.
# Note that CSV/JSON formats will fail with CORS if you try to read them from a local HTML file.
print("var data = ")
data = [{"name": "Origin", "parent": "", "value": None, "percent": None}]
for k, v in relevant_balances_in_bnb.items():
    data.append({"name": k, "parent": "Origin", "value": v["$"], "percent": v["%"]})

print(json.dumps(data))
