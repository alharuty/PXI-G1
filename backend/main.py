from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
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
from time import time as time_now

# Importaciones del proyecto
from models.prompt import PromptRequest, ImagenRequest, SimpleGenerationRequest
from services.utils import extract_stock_symbol, get_symbol_from_coin_name
from services.crypto_utils import CRYPTO_LIST
from services.alpha_client import get_crypto_price, get_stock_data
from services.nlp_generator import generate_summary
from firebase_config import db
from services.img_generation_functions import (
    crear_prompt_optimizado, 
    generar_imagen_huggingface, 
    generar_imagen_fallback, 
    sanitize_filename, 
    subir_imagen_a_supabase
)
from app.models import GenerationRequest, GenerationResponse
from app.agents import generate_content as generate_content_agent
from DB.supabase_client import supabase

load_dotenv()

# =============================
# CONFIGURACIÓN FASTAPI
# =============================

app = FastAPI(
    title="🤖 BUDDY API Unificada", 
    description="API completa con NLP y generación de imágenes integrada",
    version="2.0.0"
)

# ⭐ CONFIGURACIÓN CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Variables globales
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
UID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{6,128}$")

# =============================
# ENDPOINTS PRINCIPALES
# =============================

@app.post("/generate")
async def generate_simple(req: SimpleGenerationRequest):
    """
    Endpoint simplificado para generar contenido de texto
    Compatible con el frontend TextGenerator.js
    """
    try:
        print(f"🎯 Solicitud de generación: {req.platform} | {req.topic} | {req.language}")
        
        # Validaciones básicas
        if not req.topic or not req.topic.strip():
            raise HTTPException(status_code=400, detail="Topic es requerido")
        
        if not req.platform:
            raise HTTPException(status_code=400, detail="Platform es requerida")
        
        # Obtener contexto del usuario si está disponible
        user_bio = ""
        if req.uid and db is not None:
            try:
                if UID_REGEX.match(req.uid):
                    doc_ref = db.collection("users").document(req.uid)
                    doc = doc_ref.get()
                    if doc.exists:
                        user_data = doc.to_dict()
                        user_bio = user_data.get("bio", "")
            except Exception as e:
                print(f"⚠️ Error accediendo a Firebase: {e}")
        
        # Agregar contexto del usuario si existe
        topic_with_context = req.topic
        if user_bio:
            topic_with_context = f"Contexto del usuario: {user_bio}\n\nTema: {req.topic}"
        
        start_time = time.time()
        # Generar contenido usando el sistema de agentes
        content = generate_content(
            platform=req.platform,
            topic=topic_with_context,
            language=req.language,
            provider="groq"
        )
        
        end_time = time.time() # Registrar el tiempo de finalización
        execution_time = end_time - start_time # Calcular el tiempo de ejecución

        # Guardar en trazabilidad si hay usuario
        if req.uid and supabase:
            try:
                data = {
                    "User_id": req.uid,
                    "used_model": "groq",
                    "Prompt": req.topic,  # Prompt original
                    "Language": req.language,
                    "Output": content,
                    "Execution_time": execution_time
                }
                print(f"DEBUG: Data to be inserted: {data}")
                supabase.table('Trazabilidad').insert(data).execute()
                print("✅ Guardado en trazabilidad")
            except Exception as e:
                print(f"⚠️ Error guardando en trazabilidad: {e}")
        
        return {"content": content}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"💥 Error generando contenido: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.post("/news-nlp")
def generate_news_nlp(req: PromptRequest):
    """Endpoint para generar resúmenes de noticias financieras"""
    start_time = time_now()
    
    try:
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
        
        # Calcular tiempo de ejecución
        execution_time = round(time_now() - start_time, 2)

        # Guardar en trazabilidad
        if supabase:
            try:
                supabase.table("Trazabilidad").insert({
                    "User_id": req.uid if req.uid else None,
                    "used_model": "groq",
                    "Prompt": req.prompt,
                    "Language": req.language,
                    "Output": resumen,
                    "Execution_time": execution_time
                }).execute()
                print("📊 Registro de trazabilidad guardado en Supabase")
            except Exception as e:
                print(f"❌ Error guardando trazabilidad en Supabase: {e}")

        return {"response": resumen}
        
    except Exception as e:
        print(f"Error en news-nlp: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_simple_content(request: dict):
    """
    Endpoint simplificado para generar contenido de texto
    Compatible con el frontend TextGenerator.js
    """
    try:
        platform = request.get('platform', 'twitter')
        topic = request.get('topic', '')
        language = request.get('language', 'es')
        
        print(f"🎯 Solicitud de generación: {platform} | {topic} | {language}")
        
        # Validaciones básicas
        if not topic or not topic.strip():
            raise HTTPException(status_code=400, detail="Topic es requerido")
        
        if not platform:
            raise HTTPException(status_code=400, detail="Platform es requerida")
        
        # Generar contenido usando el sistema de agentes
        content = generate_content_agent(
            platform=platform,
            topic=topic,
            language=language,
            provider="groq"
        )
        
        return {"content": content}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"💥 Error generando contenido: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/generate-image")
async def generate_image(req: ImagenRequest):
    """Genera imagen con manejo robusto de errores y fallbacks"""
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

# =============================
# ENDPOINTS DE TRAZABILIDAD
# =============================

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

@app.get("/api/trazabilidad/{user_id}")
async def get_trazabilidad_by_user(user_id: str):
    try:
        response = supabase.table('trazabilidad').select('*').eq('user_id', user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@app.delete("/api/trazabilidad/{id}")
async def delete_trazabilidad(id: str):
    try:
        response = supabase.table('trazabilidad').delete().eq('id', id).execute()
        return {"message": "Registro de trazabilidad eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================
# ENDPOINTS DE INFORMACIÓN
# =============================

@app.get("/")
def read_root():
    return {
        "message": "🤖 BUDDY API Unificada", 
        "version": "2.0.0",
        "status": "running",
        "architecture": "Servidor unificado",
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
            "text": ["POST /generate", "POST /news-nlp"],
            "images": ["POST /generate-image"],
            "trazabilidad": ["POST /api/trazabilidad", "GET /api/trazabilidad/{user_id}"],
            "info": ["GET /", "GET /health"]
        }
    }

@app.get("/health")
def health_check():
    """Health check completo"""
    
    # Verificar APIs
    api_status = {}
    api_status["groq"] = "✅" if os.getenv("GROQ_API_KEY") else "❌"
    api_status["huggingface"] = "✅" if HUGGINGFACE_API_KEY else "❌" 
    api_status["alphavantage"] = "✅" if os.getenv("ALPHAVANTAGE_API_KEY") else "❌"
    
    # Verificar servicios
    service_status = {}
    service_status["firebase"] = "✅" if db is not None else "❌"
    service_status["supabase"] = "✅" if supabase else "❌"
    
    return {
        "status": "healthy", 
        "message": "🤖 BUDDY API Unificada funcionando correctamente",
        "timestamp": datetime.now().isoformat(),
        "apis": api_status,
        "services": service_status,
        "architecture": "unified_server",
        "cors": "configurado para localhost:3000"
    }

# =============================
# ENDPOINT DE PRUEBA CORS
# =============================

@app.options("/generate")
async def options_generate():
    """Handle OPTIONS request for CORS preflight"""
    return {"message": "OK"}
