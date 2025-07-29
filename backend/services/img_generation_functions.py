from dotenv import load_dotenv
import os
from fastapi import FastAPI, HTTPException, Request
from deep_translator import GoogleTranslator
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
import time
import requests
import re
import supabase
from supabase import create_client
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.prompt import ImagenRequest

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

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