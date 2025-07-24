from fastapi import FastAPI, HTTPException
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
from firebase_config import db

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{6,128}$")

@app.post("/news-nlp")
def generate(req: PromptRequest):
    data_chunks = []
    user_bio = ""

    if req.uid:
        if not UID_REGEX.match(req.uid):
            raise HTTPException(status_code=400, detail="UID inválido.")
        
        doc_ref = db.collection("users").document(req.uid)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
        user_data = doc.to_dict()
        user_bio = user_data.get("bio", "")

    # Detectar símbolo de acción
    symbol = extract_stock_symbol(req.prompt)

    # Buscar símbolo de criptomoneda si se indicó
    crypto_symbol = None
    if req.coin_name:
        crypto_symbol = get_symbol_from_coin_name(req.coin_name)
        if not crypto_symbol:
            return {"response": f"Criptomoneda '{req.coin_name}' no encontrada. Asegúrate de escribir el nombre exacto."}

    # Obtener datos financieros
    if symbol:
        stock_data = get_stock_data(symbol)
        if "error" not in stock_data:
            data_chunks.append(f"Datos de la acción {symbol}: {stock_data}")

    if crypto_symbol:
        crypto_data = get_crypto_price(crypto_symbol)
        if "error" not in crypto_data:
            data_chunks.append(f"Precio de {req.coin_name} ({crypto_symbol}): {crypto_data}")

    # Construir contexto para el resumen
    context = "\n".join(data_chunks) if data_chunks else req.prompt

    if user_bio:
        full_context = f"Este es el contexto del usuario: {user_bio}\n\nAhora responde a su solicitud:\n\n{context}"
    else:
        full_context = context

    resumen = generate_summary(full_context, language=req.language)

    return {"response": resumen}
