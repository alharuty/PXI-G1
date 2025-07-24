from fastapi import FastAPI, HTTPException  # <-- Importo HTTPException para manejo de errores en endpoints
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.crypto_utils import CRYPTO_LIST
from services.alpha_client import get_crypto_price, get_stock_data
from services.nlp_generator import generate_summary
import re
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str
    language: str
    coin_name: str | None = None

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


# =============================
# Endpoint GET para traer la última imagen generada
# =============================
@app.get("/last-image")
def get_last_image():
    """
    Obtiene la última imagen generada desde el microservicio de imágenes.
    FRONTEND: Debe llamar a este endpoint para obtener el nombre o URL de la última imagen generada.
    DEVUELVE: {"filename": <nombre o url de la imagen>}
    USO: El frontend debe construir la URL pública si solo se devuelve el nombre.
    """
    try:
        url = "http://localhost:8000/historial"  # <-- El microservicio de imágenes debe exponer este endpoint
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            imagenes = data.get("imagenes", [])
            if not imagenes:
                raise HTTPException(status_code=404, detail="No hay imágenes generadas.")  # <-- Si no hay imágenes, se devuelve un error 404
            last_image = imagenes[0]  # <-- Aquí se obtiene el nombre o URL de la última imagen generada
            # <-- OPCIONAL: Si tienes la URL pública en Supabase, devuélvela aquí en vez del nombre
            return {"filename": last_image}  # <-- El frontend debe usar este valor para mostrar la imagen
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)  # <-- Si el microservicio responde con error, se propaga el error
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # <-- Si ocurre cualquier excepción, se devuelve error 500
    
    
    
    
    #==========================================================================
    ###"DESCOMENTAR SI SE REQUIERE"###
    #==========================================================================
## Nuevo endpoint para generar imagen usando el microservicio de imágenes
# @app.post("/generate-image")
# async def generate_image(request: Request):
#     """
#     Recibe los datos necesarios para generar una imagen y llama al microservicio de imágenes.
#     """
#     try:
#         payload = await request.json()
#         # Cambia la URL si el microservicio corre en otro puerto o ruta
#         url = "http://localhost:8000/generar_imagen"
#         response = requests.post(url, json=payload)
#         if response.status_code == 200:
#             return response.json()
#         else:
#             raise HTTPException(status_code=response.status_code, detail=response.text)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))