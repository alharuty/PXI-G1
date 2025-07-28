import re
from services.crypto_utils import CRYPTO_LIST

def extract_stock_symbol(text: str) -> str | None:
    match = re.search(r'\b([A-Z]{1,5})\b', text)
    if match:
        return match.group(1)
    return None

def get_symbol_from_coin_name(name: str) -> str | None:
    name = name.lower()
    for coin in CRYPTO_LIST:
        if coin["name"].lower() == name:
            return coin["symbol"].upper()
    return None
