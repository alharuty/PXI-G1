from fastapi import FastAPI, HTTPException
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

# =============================
# CONFIGURACIÓN
# =============================
load_dotenv()

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

# FastAPI
app = FastAPI(
    title="🎨 Microservicio de Generación de Imágenes",
    description="Servicio independiente para generar imágenes con IA",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio local para backup
IMAGENES_PATH = os.path.join(os.path.dirname(__file__), "imagenes")
os.makedirs(IMAGENES_PATH, exist_ok=True)

# =============================
# MODELOS
# =============================
class ImagenRequest(BaseModel):
    tema: str
    audiencia: str
    estilo: str
    colores: str
    detalles: str = ""

# =============================
# FUNCIONES AUXILIARES
# =============================
def crear_prompt_optimizado(req: ImagenRequest) -> str:
    """Crea un prompt optimizado para Stable Diffusion"""
    
    # Mapeo de estilos
    style_mapping = {
        "digital art": "digital art, concept art, artstation trending",
        "realista": "photorealistic, high quality, detailed",
        "dibujo animado": "cartoon style, animated, colorful",
        "acrilico": "acrylic painting, artistic, textured",
        "acuarela": "watercolor painting, soft, flowing",
        "pixel art": "pixel art, retro, 8-bit style"
    }
    
    # Mapeo de colores
    color_mapping = {
        "colores vivos": "vibrant colors, bright, saturated",
        "colores pastel": "pastel colors, soft tones, muted",
        "blanco y negro": "black and white, monochrome",
        "tonos calidos": "warm colors, orange, red, yellow tones",
        "tonos frios": "cool colors, blue, green, purple tones"
    }
    
    # Mapeo de audiencias
    audience_mapping = {
        "niños": "child-friendly, cute, innocent",
        "adolescentes": "modern, trendy, youth-oriented",
        "adultos": "professional, sophisticated, mature",
        "adultos mayores": "classic, traditional, elegant",
        "deportistas": "dynamic, energetic, sporty"
    }
    
    # Construir prompt
    style = style_mapping.get(req.estilo, req.estilo)
    colors = color_mapping.get(req.colores, req.colores)
    audience = audience_mapping.get(req.audiencia, req.audiencia)
    
    prompt = f"{req.tema}, {style}, {colors}, {audience}"
    
    if req.detalles:
        prompt += f", {req.detalles}"
    
    # Agregar términos de calidad
    prompt += ", high quality, detailed, masterpiece"
    
    return prompt

def generar_imagen_huggingface(prompt_text: str):
    """Genera imagen usando Hugging Face"""
    if not HUGGINGFACE_API_KEY:
        raise HTTPException(status_code=500, detail="HUGGINGFACE_API_KEY no configurada")
    
    try:
        # Traducir a inglés
        prompt_en = GoogleTranslator(source='auto', target='en').translate(prompt_text)
        print(f"🔤 Prompt traducido: {prompt_en}")
    except Exception as e:
        print(f"⚠️ Error traduciendo: {e}")
        prompt_en = prompt_text

    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt_en}
    
    print(f"🎨 Generando imagen con Hugging Face...")
    print(f"📝 Prompt: {prompt_en}")
    
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
        # Subir archivo
        res = supabase.storage.from_('imagenes').upload(
            nombre_archivo, 
            img_bytes, 
            {"content-type": "image/png"}
        )
        
        # Obtener URL pública
        url = supabase.storage.from_('imagenes').get_public_url(nombre_archivo)
        print(f"☁️ Imagen subida a Supabase: {url}")
        return url
        
    except Exception as e:
        print(f"❌ Error subiendo a Supabase: {e}")
        return None

# =============================
# ENDPOINTS
# =============================

@app.get("/")
async def root():
    return {
        "message": "🎨 Microservicio de Generación de Imágenes",
        "status": "running",
        "version": "1.0.0",
        "huggingface": "✅" if HUGGINGFACE_API_KEY else "❌",
        "supabase": "✅" if supabase else "❌"
    }

@app.post("/generar_imagen")
async def generar_imagen(req: ImagenRequest):
    """
    Endpoint principal para generar imágenes
    """
    try:
        print(f"🎯 Nueva solicitud de imagen: {req.tema}")
        print(f"👥 Audiencia: {req.audiencia}")
        print(f"🎨 Estilo: {req.estilo}")
        print(f"🌈 Colores: {req.colores}")
        
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
        
        # Guardar localmente (backup)
        filepath_local = os.path.join(IMAGENES_PATH, nombre_archivo)
        with open(filepath_local, "wb") as f:
            f.write(img_bytes)
        print(f"💾 Imagen guardada localmente: {filepath_local}")
        
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

@app.get("/historial")
async def ver_historial():
    """Lista todas las imágenes generadas (ordenadas por fecha, más reciente primero)"""
    try:
        if not os.path.exists(IMAGENES_PATH):
            return {"imagenes": []}
        
        archivos = [f for f in os.listdir(IMAGENES_PATH) if f.endswith('.png')]
        archivos_ordenados = sorted(archivos, reverse=True)  # Más reciente primero
        
        print(f"📋 Historial: {len(archivos_ordenados)} imágenes encontradas")
        return {"imagenes": archivos_ordenados}
        
    except Exception as e:
        print(f"❌ Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/imagen/{nombre}")
async def descargar_imagen(nombre: str):
    """Descarga una imagen específica"""
    filepath = os.path.join(IMAGENES_PATH, nombre)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return FileResponse(filepath, media_type="image/png")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "image-generation"}
