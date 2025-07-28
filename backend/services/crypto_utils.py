import requests

def load_crypto_list():
    url = "https://api.coingecko.com/api/v3/coins/list"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return []

CRYPTO_LIST = load_crypto_list()

def detect_crypto_symbol(prompt: str) -> str | None:
    prompt = prompt.lower()
    for coin in CRYPTO_LIST:
        if coin["id"] in prompt or coin["symbol"] in prompt or coin["name"].lower() in prompt:
            return coin["symbol"].upper()
    return None
