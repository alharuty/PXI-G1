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

# Importaciones existentes del proyecto
from services.crypto_utils import CRYPTO_LIST
from services.alpha_client import get_crypto_price, get_stock_data
from services.nlp_generator import generate_summary
from models.prompt import PromptRequest
from services.utils import extract_stock_symbol, get_symbol_from_coin_name
from firebase_config import db

load_dotenv()

# =============================
# CONFIGURACIÓN UNIFICADA
# =============================

# APIs
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase conectado")
else:
    supabase = None
    print("⚠️ Supabase no configurado")

# Directorio para imágenes
IMAGENES_PATH = os.path.join(os.path.dirname(__file__), "imagenes")
os.makedirs(IMAGENES_PATH, exist_ok=True)

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

# =============================
# MODELOS PYDANTIC
# =============================

class ImagenRequest(BaseModel):
    tema: str
    audiencia: str
    estilo: str
    colores: str
    detalles: str = ""

# =============================
# FUNCIONES DE GENERACIÓN DE IMÁGENES
# =============================

def crear_prompt_optimizado(req: ImagenRequest) -> str:
    """Crea un prompt optimizado para Stable Diffusion"""
    
    style_mapping = {
        "digital art": "digital art, concept art, artstation trending",
        "realista": "photorealistic, high quality, detailed",
        "dibujo animado": "cartoon style, animated, colorful",
        "acrilico": "acrylic painting, artistic, textured",
        "acuarela": "watercolor painting, soft, flowing",
        "pixel art": "pixel art, retro, 8-bit style"
    }
    
    color_mapping = {
        "colores vivos": "vibrant colors, bright, saturated",
        "colores pastel": "pastel colors, soft tones, muted",
        "blanco y negro": "black and white, monochrome",
        "tonos calidos": "warm colors, orange, red, yellow tones",
        "tonos frios": "cool colors, blue, green, purple tones"
    }
    
    audience_mapping = {
        "niños": "child-friendly, cute, innocent",
        "adolescentes": "modern, trendy, youth-oriented",
        "adultos": "professional, sophisticated, mature",
        "adultos mayores": "classic, traditional, elegant",
        "deportistas": "dynamic, energetic, sporty"
    }
    
    style = style_mapping.get(req.estilo, req.estilo)
    colors = color_mapping.get(req.colores, req.colores)
    audience = audience_mapping.get(req.audiencia, req.audiencia)
    
    prompt = f"{req.tema}, {style}, {colors}, {audience}"
    
    if req.detalles:
        prompt += f", {req.detalles}"
    
    prompt += ", high quality, detailed, masterpiece"
    
    return prompt

# =============================
# FUNCIONES MEJORADAS DE GENERACIÓN DE IMÁGENES
# =============================

def generar_imagen_huggingface(prompt_text: str, max_retries: int = 3):
    """Genera imagen usando Hugging Face con reintentos y mejor manejo de errores"""
    if not HUGGINGFACE_API_KEY:
        raise HTTPException(status_code=500, detail="HUGGINGFACE_API_KEY no configurada")
    
    # Traducir prompt
    try:
        prompt_en = GoogleTranslator(source='auto', target='en').translate(prompt_text)
        print(f"🔤 Prompt traducido: {prompt_en}")
    except Exception as e:
        print(f"⚠️ Error traduciendo: {e}")
        prompt_en = prompt_text

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt_en}
    
    for intento in range(max_retries):
        try:
            print(f"🎨 Generando imagen con Hugging Face (intento {intento + 1}/{max_retries})...")
            
            # Timeout progresivo: 60s, 90s, 120s
            timeout = 60 + (intento * 30)
            
            response = requests.post(
                HUGGINGFACE_API_URL, 
                headers=headers, 
                json=payload, 
                timeout=timeout
            )
            
            if response.status_code == 200:
                print("✅ Imagen generada exitosamente")
                return response.content
            
            elif response.status_code == 503:
                # Modelo cargándose
                print("⏳ Modelo cargándose, esperando...")
                time.sleep(10 + (intento * 5))
                continue
                
            elif response.status_code == 429:
                # Rate limit
                wait_time = 30 + (intento * 10)
                print(f"⏱️ Rate limit alcanzado, esperando {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            else:
                print(f"❌ Error Hugging Face: {response.status_code} - {response.text}")
                if intento == max_retries - 1:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Error generando imagen después de {max_retries} intentos: {response.text}"
                    )
                
        except ReadTimeout:
            print(f"⏰ Timeout en intento {intento + 1}")
            if intento == max_retries - 1:
                raise HTTPException(
                    status_code=504, 
                    detail=f"Timeout generando imagen después de {max_retries} intentos. El modelo puede estar sobrecargado."
                )
            
            # Esperar antes del siguiente intento
            wait_time = 30 + (intento * 15)
            print(f"⏳ Esperando {wait_time}s antes del siguiente intento...")
            time.sleep(wait_time)
            
        except ConnectionError:
            print(f"🌐 Error de conexión en intento {intento + 1}")
            if intento == max_retries - 1:
                raise HTTPException(
                    status_code=503, 
                    detail="Error de conexión con Hugging Face. Servicio no disponible."
                )
            time.sleep(10 + (intento * 5))
            
        except RequestException as e:
            print(f"📡 Error de request en intento {intento + 1}: {e}")
            if intento == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")
            time.sleep(5 + (intento * 2))

def generar_imagen_fallback(prompt_text: str):
    """Función fallback - crea una imagen placeholder"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Crear imagen placeholder
        img = Image.new('RGB', (512, 512), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Texto en la imagen
        text_lines = [
            "Imagen no disponible",
            "Servicio temporalmente",
            "fuera de línea",
            "",
            f"Prompt: {prompt_text[:50]}..."
        ]
        
        y_offset = 150
        for line in text_lines:
            bbox = draw.textbbox((0, 0), line)
            text_width = bbox[2] - bbox[0]
            x = (512 - text_width) // 2
            draw.text((x, y_offset), line, fill='darkblue')
            y_offset += 30
        
        # Convertir a bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
        
    except ImportError:
        # Si PIL no está disponible, crear una imagen muy básica
        print("⚠️ PIL no disponible para placeholder")
        return None

# =============================
# ENDPOINTS DE NLP (EXISTENTES)
# =============================

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

@app.post("/generate")
def generate_content(request: dict):
    """Endpoint unificado para generar contenido"""
    platform = request.get('platform', 'general')
    topic = request.get('topic', '')
    
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    
    prompt = f"Create content for {platform} about: {topic}"
    content = generate_summary(prompt, language="es")
    
    return {"content": content}

# =============================
# ENDPOINTS DE IMÁGENES (INTEGRADOS)
# =============================

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
        filepath_local = os.path.join(IMAGENES_PATH, nombre_archivo)
        with open(filepath_local, "wb") as f:
            f.write(img_bytes)
        print(f"💾 Imagen guardada: {filepath_local}")
        
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

def sanitize_filename(filename: str) -> str:
    """Sanitiza un nombre de archivo"""
    filename = filename.lower()
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    filename = filename.strip('_')
    filename = filename[:30]
    
    if not filename:
        filename = "imagen"
    
    return filename

def generar_imagen_huggingface(prompt_text: str):
    """Genera imagen usando Hugging Face"""
    if not HUGGINGFACE_API_KEY:
        raise HTTPException(status_code=500, detail="HUGGINGFACE_API_KEY no configurada")
    
    try:
        prompt_en = GoogleTranslator(source='auto', target='en').translate(prompt_text)
        print(f"🔤 Prompt traducido: {prompt_en}")
    except Exception as e:
        print(f"⚠️ Error traduciendo: {e}")
        prompt_en = prompt_text

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt_en}
    
    print(f"🎨 Generando imagen con Hugging Face...")
    
    response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload, timeout=60)
    
    if response.status_code == 200:
        print("✅ Imagen generada exitosamente")
        return response.content
    else:
        print(f"❌ Error Hugging Face: {response.status_code} - {response.text}")
        raise HTTPException(status_code=500, detail=f"Error generando imagen: {response.text}")

def subir_imagen_a_supabase(nombre_archivo: str, img_bytes: bytes):
    """Sube imagen a Supabase Storage"""
    if not supabase:
        print("⚠️ Supabase no disponible, saltando upload")
        return None
    
    try:
        res = supabase.storage.from_('imagenes').upload(
            nombre_archivo, 
            img_bytes, 
            {"content-type": "image/png"}
        )
        
        url = supabase.storage.from_('imagenes').get_public_url(nombre_archivo)
        print(f"☁️ Imagen subida a Supabase: {url}")
        return url
        
    except Exception as e:
        print(f"❌ Error subiendo a Supabase: {e}")
        return None

# =============================
# ENDPOINTS DE NLP (EXISTENTES)
# =============================

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

@app.post("/generate")
def generate_content(request: dict):
    """Endpoint unificado para generar contenido"""
    platform = request.get('platform', 'general')
    topic = request.get('topic', '')
    
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    
    prompt = f"Create content for {platform} about: {topic}"
    content = generate_summary(prompt, language="es")
    
    return {"content": content}

# =============================
# ENDPOINTS DE IMÁGENES (INTEGRADOS)
# =============================

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
        filepath_local = os.path.join(IMAGENES_PATH, nombre_archivo)
        with open(filepath_local, "wb") as f:
            f.write(img_bytes)
        print(f"💾 Imagen guardada: {filepath_local}")
        
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

def sanitize_filename(filename: str) -> str:
    """Sanitiza un nombre de archivo"""
    filename = filename.lower()
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    filename = filename.strip('_')
    filename = filename[:30]
    
    if not filename:
        filename = "imagen"
    
    return filename

def generar_imagen_huggingface(prompt_text: str):
    """Genera imagen usando Hugging Face"""
    if not HUGGINGFACE_API_KEY:
        raise HTTPException(status_code=500, detail="HUGGINGFACE_API_KEY no configurada")
    
    try:
        prompt_en = GoogleTranslator(source='auto', target='en').translate(prompt_text)
        print(f"🔤 Prompt traducido: {prompt_en}")
    except Exception as e:
        print(f"⚠️ Error traduciendo: {e}")
        prompt_en = prompt_text

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt_en}
    
    print(f"🎨 Generando imagen con Hugging Face...")
    
    response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload, timeout=60)
    
    if response.status_code == 200:
        print("✅ Imagen generada exitosamente")
        return response.content
    else:
        print(f"❌ Error Hugging Face: {response.status_code} - {response.text}")
        raise HTTPException(status_code=500, detail=f"Error generando imagen: {response.text}")

def subir_imagen_a_supabase(nombre_archivo: str, img_bytes: bytes):
    """Sube imagen a Supabase Storage"""
    if not supabase:
        print("⚠️ Supabase no disponible, saltando upload")
        return None
    
    try:
        res = supabase.storage.from_('imagenes').upload(
            nombre_archivo, 
            img_bytes, 
            {"content-type": "image/png"}
        )
        
        url = supabase.storage.from_('imagenes').get_public_url(nombre_archivo)
        print(f"☁️ Imagen subida a Supabase: {url}")
        return url
        
    except Exception as e:
        print(f"❌ Error subiendo a Supabase: {e}")
        return None

# =============================
# ENDPOINTS DE INFORMACIÓN
# =============================

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
    
    # Verificar APIs
    api_status = {}
    api_status["groq"] = "✅" if os.getenv("GROQ_API_KEY") else "❌"
    api_status["huggingface"] = "✅" if HUGGINGFACE_API_KEY else "❌" 
    api_status["alphavantage"] = "✅" if os.getenv("ALPHAVANTAGE_API_KEY") else "❌"
    
    # Verificar servicios
    service_status = {}
    service_status["firebase"] = "✅" if db is not None else "❌"
    service_status["supabase"] = "✅" if supabase else "❌"
    service_status["image_storage"] = "✅" if os.path.exists(IMAGENES_PATH) else "❌"
    
    return {
        "status": "healthy", 
        "message": "🤖 BUDDY API Unificada funcionando correctamente",
        "timestamp": datetime.now().isoformat(),
        "apis": api_status,
        "services": service_status,
        "architecture": "unified_server"
    }

@app.get("/stats")
def get_stats():
    """Estadísticas del sistema"""
    try:
        # Contar imágenes generadas
        num_images = 0
        if os.path.exists(IMAGENES_PATH):
            num_images = len([f for f in os.listdir(IMAGENES_PATH) if f.endswith('.png')])
        
        return {
            "images_generated": num_images,
            "storage_path": IMAGENES_PATH,
            "services_active": {
                "nlp": True,
                "images": True,
                "firebase": db is not None,
                "supabase": supabase is not None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))