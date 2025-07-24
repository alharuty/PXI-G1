from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.crypto_utils import CRYPTO_LIST
from services.alpha_client import get_crypto_price, get_stock_data
from services.nlp_generator import generate_summary
import re
from dotenv import load_dotenv
import os
from models.prompt import PromptRequest
from services.utils import extract_stock_symbol, get_symbol_from_coin_name

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/news-nlp")
def generate(req: PromptRequest):
    data_chunks = []

    # Buscar símbolo bursátil si lo hay
    symbol = extract_stock_symbol(req.prompt)

    # Buscar símbolo de crypto si se indicó
    crypto_symbol = None
    if req.coin_name:
        crypto_symbol = get_symbol_from_coin_name(req.coin_name)
        if not crypto_symbol:
            return {"response": f"Criptomoneda '{req.coin_name}' no encontrada. Asegúrate de escribir el nombre exacto."}

    # Llamadas de datos
    if symbol:
        stock_data = get_stock_data(symbol)
        if "error" not in stock_data:
            data_chunks.append(f"Datos de la acción {symbol}: {stock_data}")

    if crypto_symbol:
        crypto_data = get_crypto_price(crypto_symbol)
        if "error" not in crypto_data:
            data_chunks.append(f"Precio de {req.coin_name} ({crypto_symbol}): {crypto_data}")

    if not data_chunks:
        resumen = generate_summary(req.prompt, language=req.language)
    else:
        texto = "\n".join(data_chunks)
        resumen = generate_summary(texto, language=req.language)

    return {"response": resumen}
