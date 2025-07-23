import os
import requests

ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

def get_stock_data(symbol: str) -> dict:
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        # El dato relevante suele estar en 'Global Quote'
        return data.get("Global Quote", {})
    return {"error": "Failed to fetch stock data"}

def get_crypto_price(symbol: str) -> dict:
    # symbol: BTC, ETH, etc. market fijo a USD
    url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={symbol}&market=USD&apikey={ALPHAVANTAGE_API_KEY}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        # El dato está en "Time Series (Digital Currency Daily)" el último registro
        ts = data.get("Time Series (Digital Currency Daily)", {})
        if ts:
            last_date = sorted(ts.keys(), reverse=True)[0]
            last_data = ts[last_date]
            price = last_data.get("4a. close (USD)")
            return {"price_usd": price, "date": last_date}
        return {"error": "No data for crypto"}
    return {"error": "Failed to fetch crypto data"}

def get_forex_rate(from_currency: str, to_currency: str) -> dict:
    url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency={to_currency}&apikey={ALPHAVANTAGE_API_KEY}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        rate_info = data.get("Realtime Currency Exchange Rate", {})
        if rate_info:
            return {
                "from_currency": rate_info.get("1. From_Currency Code"),
                "to_currency": rate_info.get("2. To_Currency Code"),
                "exchange_rate": rate_info.get("5. Exchange Rate"),
                "last_refreshed": rate_info.get("6. Last Refreshed"),
            }
        return {"error": "No forex data found"}
    return {"error": "Failed to fetch forex data"}
