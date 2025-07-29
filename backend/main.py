from fastapi import FastAPI, HTTPException, Query
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.crypto_utils import CRYPTO_LIST
from services.alpha_client import get_crypto_price, get_stock_data
from services.nlp_generator import generate_summary
from models.prompt import PromptRequest
from services.utils import extract_stock_symbol, get_symbol_from_coin_name
from firebase_config import db
from app.models import GenerationRequest, GenerationResponse
from app.agents import generate_content
from dotenv import load_dotenv
from DB.supabase_client import supabase
import re
import os
import requests

load_dotenv()

app = FastAPI(title="AI Content Generator")
security = HTTPBearer()

#Post para la creacion de trazabilidad

@app.post("/api/trazabilidad")
async def create_trazabilidad(
    user_id: str,
    used_model: str,
    prompt: str,
    language: str,
    output: str,
    execution_time: float
):
    try:
        data = {
            "user_id": user_id,
            "used_model": used_model,
            "prompt": prompt,
            "language": language,
            "output": output,
            "execution_time": execution_time
        }
        
        response = supabase.table('trazabilidad').insert(data).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#Post para la llamada de generación de imagenes

@app.post("/generate", response_model=GenerationResponse)
def generate(req: GenerationRequest, provider: str = Query("groq", enum=["groq", "ollama"])):
    user_bio = ""
    if hasattr(req, 'uid') and req.uid:
        if not UID_REGEX.match(req.uid):
            raise HTTPException(status_code=400, detail="UID inválido.")
        doc_ref = db.collection("users").document(req.uid)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=400, detail="Usuario no encontrado.")
        user_data = doc.to_dict()
        user_bio = user_data.get("bio", "")
    
    if user_bio:
        req.prompt = f"Este es el contexto del usuario: {user_bio}\n\nAhora responde a su solicitud:\n\n{req.prompt}"
    else:
        full_topic = req.topic

    try:
        content = generate_content(req.platform, req.topic, language=req.language, provider=provider)
        return GenerationResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

#Get para la llamada a trazabilidad y consultarla

@app.get("/api/trazabilidad/{user_id}")
async def get_trazabilidad_by_user(user_id: str):
    try:
        response = supabase.table('trazabilidad').select('*').eq('user_id', user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#Put para la edición de la tabla

@app.put("/api/trazabilidad/{id}")
async def update_trazabilidad(
    id: str,
    used_model: str = None,
    prompt: str = None,
    language: str = None,
    output: str = None,
    execution_time: float = None
):
    try:
        updates = {}
        if used_model: updates["used_model"] = used_model
        if prompt: updates["prompt"] = prompt
        if language: updates["language"] = language
        if output: updates["output"] = output
        if execution_time: updates["execution_time"] = execution_time
        
        response = supabase.table('trazabilidad').update(updates).eq('id', id).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    
    #Delete para eliminar registros de la base de datos
    
@app.delete("/api/trazabilidad/{id}")
async def delete_trazabilidad(id: str):
    try:
        response = supabase.table('trazabilidad').delete().eq('id', id).execute()
        return {"message": "Registro de trazabilidad eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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
