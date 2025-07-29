from fastapi import FastAPI, HTTPException, Query
from fastapi.security import HTTPBearer
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from datetime import datetime
import requests
import base64
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from supabase import create_client, Client
import re
import time
import random
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
from models.prompt import PromptRequest, ImagenRequest
from services.utils import extract_stock_symbol, get_symbol_from_coin_name
from firebase_config import db
from services.img_generation_functions import crear_prompt_optimizado, generar_imagen_huggingface, generar_imagen_fallback, sanitize_filename, subir_imagen_a_supabase

# Importaciones existentes del proyecto
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

# APIs
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"


# Directorio para imágenes
#IMAGENES_PATH = os.path.join(os.path.dirname(__file__), "imagenes")
#os.makedirs(IMAGENES_PATH, exist_ok=True)

# FastAPI App
app = FastAPI(
    title="🤖 BUDDY API Unificada", 
    description="API completa con NLP y generación de imágenes integrada",
    version="2.0.0"
)

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
    """Endpoint para generar resúmenes de noticias financieras"""
    data_chunks = []
    user_bio = ""

    if req.uid and db is not None:
        if not UID_REGEX.match(req.uid):
            raise HTTPException(status_code=400, detail="UID inválido.")
        
        try:
            doc_ref = db.collection("users").document(req.uid)
            doc = doc_ref.get()
            if doc.exists:
                user_data = doc.to_dict()
                user_bio = user_data.get("bio", "")
        except Exception as e:
            print(f"Error accediendo a Firebase: {e}")

    symbol = extract_stock_symbol(req.prompt)
    crypto_symbol = None
    if req.coin_name:
        crypto_symbol = get_symbol_from_coin_name(req.coin_name)
        if not crypto_symbol:
            return {"response": f"Criptomoneda '{req.coin_name}' no encontrada."}

    if symbol:
        stock_data = get_stock_data(symbol)
        if "error" not in stock_data:
            data_chunks.append(f"Datos de la acción {symbol}: {stock_data}")

    if crypto_symbol:
        crypto_data = get_crypto_price(crypto_symbol)
        if "error" not in crypto_data:
            data_chunks.append(f"Precio de {req.coin_name} ({crypto_symbol}): {crypto_data}")

    context = "\n".join(data_chunks) if data_chunks else req.prompt
    if user_bio:
        full_context = f"Contexto del usuario: {user_bio}\n\nSolicitud:\n\n{context}"
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
    
    original_prompt = req.prompt # Guardar el prompt original antes de modificarlo

    if user_bio:
        req.prompt = f"Este es el contexto del usuario: {user_bio}\n\nAhora responde a su solicitud:\n\n{req.prompt}"
    else:
        full_topic = req.topic

    try:
        content = generate_content(req.platform, req.topic, language=req.language, provider=provider)
        # Guardar la generación en Supabase
        try:
            data = {
                "user_id": req.uid, # Asumiendo que req.uid es el user_id de Firebase
                "used_model": provider, # O el modelo específico usado si es diferente
                "prompt": original_prompt, # Usar el prompt original
                "language": req.language,
                "output": content,
                "execution_time": 0.0 # Puedes calcular el tiempo de ejecución real aquí si lo necesitas
            }
            supabase.table('trazabilidad').insert(data).execute()
        except Exception as e:
            print(f"Error al guardar en Supabase: {e}")
            # Considera si quieres lanzar una excepción o simplemente loguear el error
        return GenerationResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-image")
async def generate_image(req: ImagenRequest):
    """
    Genera imagen con manejo robusto de errores y fallbacks
    """
    try:
        print(f"🎯 Nueva solicitud de imagen: {req.tema}")
        print(f"👥 Audiencia: {req.audiencia} | 🎨 Estilo: {req.estilo} | 🌈 Colores: {req.colores}")
        
        # Crear prompt optimizado
        prompt_optimizado = crear_prompt_optimizado(req)
        print(f"✨ Prompt optimizado: {prompt_optimizado}")
        
        # Intentar generar imagen
        img_bytes = None
        error_message = None
        
        try:
            img_bytes = generar_imagen_huggingface(prompt_optimizado)
        except HTTPException as e:
            error_message = e.detail
            print(f"❌ Error en Hugging Face: {error_message}")
            
            # Intentar generar imagen placeholder
            img_bytes = generar_imagen_fallback(prompt_optimizado)
            if img_bytes is None:
                raise HTTPException(
                    status_code=503, 
                    detail=f"Servicio de imágenes no disponible: {error_message}"
                )
        
        # Convertir a base64
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        # Crear nombre único con sanitización
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tema_safe = sanitize_filename(req.tema)
        nombre_archivo = f"{timestamp}_{tema_safe}.png"
        
        print(f"📁 Nombre de archivo: {nombre_archivo}")
        
        # Guardar localmente
        #filepath_local = os.path.join(IMAGENES_PATH, nombre_archivo)
        #with open(filepath_local, "wb") as f:
        #    f.write(img_bytes)
        #print(f"💾 Imagen guardada: {filepath_local}")

        # Subir a Supabase (solo si no es placeholder)
        url_supabase = None
        if error_message is None:
            url_supabase = subir_imagen_a_supabase(nombre_archivo, img_bytes)
        
        # Preparar respuesta
        response = {
            "filename": nombre_archivo,
            "imagen": img_b64,
            "descripcion": prompt_optimizado,
        }
        
        if error_message:
            response["mensaje"] = f"⚠️ Imagen placeholder generada: {error_message}"
            response["is_placeholder"] = True
        else:
            response["mensaje"] = "✅ Imagen generada exitosamente"
            response["is_placeholder"] = False
            
        if url_supabase:
            response["url_supabase"] = url_supabase
        
        print(f"🎉 Respuesta preparada: {nombre_archivo}")
        return response
        
    except Exception as e:
        print(f"💥 Error crítico generando imagen: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Error crítico en generación de imagen: {str(e)}"
        )



@app.get("/")
def read_root():
    return {
        "message": "🤖 BUDDY API Unificada", 
        "version": "2.0.0",
        "status": "running",
        "architecture": "Servidor unificado - Una sola terminal",
        "services": {
            "nlp": "✅ Integrado",
            "images": "✅ Integrado", 
            "firebase": "✅" if db is not None else "❌ Deshabilitado",
            "supabase": "✅" if supabase else "❌"
        },
        "apis": {
            "groq": "✅" if os.getenv("GROQ_API_KEY") else "❌",
            "huggingface": "✅" if HUGGINGFACE_API_KEY else "❌",
            "alphavantage": "✅" if os.getenv("ALPHAVANTAGE_API_KEY") else "❌"
        },
        "endpoints": {
            "nlp": ["POST /news-nlp", "POST /generate"],
            "images": ["POST /generate-image", "GET /last-image", "GET /image-history", "GET /imagen/{nombre}"],
            "info": ["GET /", "GET /health"]
        }
    }

@app.get("/health")
def health_check():
    """Health check completo"""
    
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
    # Verificar APIs
    api_status = {}
    api_status["groq"] = "✅" if os.getenv("GROQ_API_KEY") else "❌"
    api_status["huggingface"] = "✅" if HUGGINGFACE_API_KEY else "❌" 
    api_status["alphavantage"] = "✅" if os.getenv("ALPHAVANTAGE_API_KEY") else "❌"
    
    # Verificar servicios
    service_status = {}
    service_status["firebase"] = "✅" if db is not None else "❌"
    service_status["supabase"] = "✅" if supabase else "❌"
    #service_status["image_storage"] = "✅" if os.path.exists(IMAGENES_PATH) else "❌"
    
    return {
        "status": "healthy", 
        "message": "🤖 BUDDY API Unificada funcionando correctamente",
        "timestamp": datetime.now().isoformat(),
        "apis": api_status,
        "services": service_status,
        "architecture": "unified_server"
    }

#@app.get("/stats")
#def get_stats():
#    """Estadísticas del sistema"""
#    try:
#        # Contar imágenes generadas
#        num_images = 0
#        if os.path.exists(IMAGENES_PATH):
#            num_images = len([f for f in os.listdir(IMAGENES_PATH) if f.endswith('.png')])
#        
#        return {
#            "images_generated": num_images,
#            "storage_path": IMAGENES_PATH,
#            "services_active": {
#                "nlp": True,
#                "images": True,
#                "firebase": db is not None,
#                "supabase": supabase is not None
#            }
#        }
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))
