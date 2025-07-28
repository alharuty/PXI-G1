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
    Genera imagen directamente en el servidor principal (sin microservicio)
    """
    try:
        print(f"🎯 Nueva solicitud de imagen: {req.tema}")
        print(f"👥 Audiencia: {req.audiencia} | 🎨 Estilo: {req.estilo} | 🌈 Colores: {req.colores}")
        
        # Crear prompt optimizado
        prompt_optimizado = crear_prompt_optimizado(req)
        print(f"✨ Prompt optimizado: {prompt_optimizado}")
        
        # Generar imagen
        img_bytes = generar_imagen_huggingface(prompt_optimizado)
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        # Crear nombre único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tema_safe = req.tema.replace(' ', '_').replace('/', '_')[:30]
        nombre_archivo = f"{timestamp}_{tema_safe}.png"
        
        # Guardar localmente
        filepath_local = os.path.join(IMAGENES_PATH, nombre_archivo)
        with open(filepath_local, "wb") as f:
            f.write(img_bytes)
        print(f"💾 Imagen guardada: {filepath_local}")
        
        # Subir a Supabase
        url_supabase = subir_imagen_a_supabase(nombre_archivo, img_bytes)
        
        response = {
            "filename": nombre_archivo,
            "imagen": img_b64,
            "descripcion": prompt_optimizado,
            "mensaje": "✅ Imagen generada exitosamente"
        }
        
        if url_supabase:
            response["url_supabase"] = url_supabase
        
        print(f"🎉 Imagen generada: {nombre_archivo}")
        return response
        
    except Exception as e:
        print(f"💥 Error generando imagen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/last-image")
def get_last_image():
    """Obtiene la última imagen generada"""
    try:
        if not os.path.exists(IMAGENES_PATH):
            raise HTTPException(status_code=404, detail="No hay imágenes generadas.")
        
        archivos = [f for f in os.listdir(IMAGENES_PATH) if f.endswith('.png')]
        if not archivos:
            raise HTTPException(status_code=404, detail="No hay imágenes generadas.")
        
        archivos_ordenados = sorted(archivos, reverse=True)
        last_image = archivos_ordenados[0]
        
        print(f"📷 Última imagen: {last_image}")
        return {"filename": last_image}
        
    except Exception as e:
        print(f"❌ Error obteniendo última imagen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/image-history")
def get_image_history():
    """Lista todas las imágenes generadas (ordenadas por fecha)"""
    try:
        if not os.path.exists(IMAGENES_PATH):
            return {"imagenes": []}
        
        archivos = [f for f in os.listdir(IMAGENES_PATH) if f.endswith('.png')]
        archivos_ordenados = sorted(archivos, reverse=True)  # Más reciente primero
        
        print(f"📋 Historial: {len(archivos_ordenados)} imágenes")
        return {"imagenes": archivos_ordenados}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/imagen/{nombre}")
async def descargar_imagen(nombre: str):
    """Descarga una imagen específica"""
    filepath = os.path.join(IMAGENES_PATH, nombre)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return FileResponse(filepath, media_type="image/png")

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