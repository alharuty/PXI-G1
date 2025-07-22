import requests
import os

FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN")

def get_stock_data(symbol: str) -> dict:
    # Ejemplo para acciones
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch stock data"}

def get_crypto_price(symbol: str) -> dict:
    # Finnhub crypto endpoint ejemplo
    url = f"https://finnhub.io/api/v1/crypto/candle?symbol={symbol}&resolution=1&count=1&token={FINNHUB_TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch crypto data"}
