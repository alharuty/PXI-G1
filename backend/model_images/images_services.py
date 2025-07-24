
"""
main.py - Backend FastAPI para generación de imágenes con Hugging Face (Stable Diffusion XL)

Este backend expone una API para enviar prompts a Hugging Face, genera la imagen y la guarda.
Las imágenes se guardan en la carpeta 'imagenes' y se mantiene un historial.
Ahora, también se suben a Firebase Storage automáticamente.

Requisitos:
- fastapi
- uvicorn
- python-dotenv
- deep-translator
- requests
- firebase-admin
"""

# =============================
# ÍNDICE DE CAMBIOS REALIZADOS
# =============================
# 1. Integración de Firebase Admin SDK para subir imágenes a Cloud Storage
# 2. Nueva función subir_imagen_a_firebase para subir imágenes generadas
# 3. Modificación del endpoint /generar_imagen para usar Firebase Storage
# 4. El guardado local de imágenes se deja comentado como referencia
# 5. Comentarios explicativos en cada sección y cambio realizado


# =============================
# 1. Importar librerías necesarias
# =============================

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

# 1. Integración de Supabase Storage para subir imágenes
from supabase import create_client, Client


# =============================
# 2. Configuración de Hugging Face y Supabase
# =============================
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

# Inicialización de Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =============================
# 3. Inicializar FastAPI y CORS
# =============================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


IMAGENES_PATH = os.path.join(os.path.dirname(__file__), "imagenes")
os.makedirs(IMAGENES_PATH, exist_ok=True)

# =============================
# 4. Esquema de entrada
# =============================
class ImagenRequest(BaseModel):
    tema: str
    audiencia: str
    estilo: str
    colores: str
    detalles: str = ""


# =============================
# 5. Función para generar imagen con Hugging Face
# =============================
def generar_imagen_huggingface(prompt_text):
    """
    Recibe un texto descriptivo (prompt), lo traduce al inglés si es necesario,
    y lo envía a la API de Hugging Face para generar una imagen.
    Devuelve los bytes de la imagen generada.
    """
    try:
        prompt_en = GoogleTranslator(source='auto', target='en').translate(prompt_text)
        print(f"[DEBUG] Prompt traducido: {prompt_en}")
    except Exception as e:
        print(f"[DEBUG] Error traduciendo prompt: {e}. Usando texto original.")
        prompt_en = prompt_text

    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
    }
    payload = {"inputs": prompt_en}
    print("[DEBUG] Enviando petición a Hugging Face...", HUGGINGFACE_API_URL)
    print("[DEBUG] Headers:", headers)
    print("[DEBUG] Payload:", payload)
    response = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload)
    print("[DEBUG] Código de respuesta:", response.status_code)
    if response.status_code == 200:
        return response.content  # bytes de la imagen
    else:
        print("Respuesta de Hugging Face:", response.status_code, response.text)
        raise HTTPException(status_code=500, detail=f"Error Hugging Face: {response.text}")

# =============================
# 6. Función para subir imagen a Supabase Storage
# =============================
def subir_imagen_a_supabase(nombre_archivo, img_bytes):
    """
    Sube los bytes de una imagen a Supabase Storage en el bucket 'imagenes'.
    Devuelve la URL pública de la imagen subida.
    """
    # Sube la imagen al bucket 'imagenes'
    res = supabase.storage.from_('imagenes').upload(nombre_archivo, img_bytes, {"content-type": "image/png"})
    res_json = res.json()
    if res_json.get('error'):
        raise Exception(res_json['error']['message'])
    # Obtiene la URL pública
    url = supabase.storage.from_('imagenes').get_public_url(nombre_archivo)
    return url


# =============================
# 7. Endpoint para generar imagen (modificado para Supabase Storage)
# =============================
@app.post("/generar_imagen")
async def generar_imagen(req: ImagenRequest):
    """
    Recibe los datos para generar una imagen, la genera usando Hugging Face,
    la sube a Supabase Storage y devuelve la URL pública junto con la imagen en base64.
    También deja comentado el guardado local como referencia.
    """
    descripcion = f"Ilustración sobre {req.tema} para {req.audiencia}, estilo {req.estilo}, colores {req.colores}. {req.detalles}"
    img_bytes = generar_imagen_huggingface(descripcion)
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"{timestamp}_{req.tema.replace(' ','_')}.png"

    # Subir imagen a Supabase Storage
    url_supabase = subir_imagen_a_supabase(nombre_archivo, img_bytes)

    # Guardado local (opcional, solo para referencia, ahora comentado)
    # with open(os.path.join(IMAGENES_PATH, nombre_archivo), "wb") as f:
    #     f.write(img_bytes)

    return {
        "filename": nombre_archivo,
        "imagen": img_b64,
        "descripcion": descripcion,
        "url_supabase": url_supabase
    }

# =============================
# 8. Endpoint para ver historial
# =============================
@app.get("/historial")
async def ver_historial():
    archivos = sorted(os.listdir(IMAGENES_PATH), reverse=True)
    return {"imagenes": archivos}

# =============================
# 9. Endpoint para descargar imagen
# =============================
@app.get("/imagen/{nombre}")
async def descargar_imagen(nombre: str):
    filepath = os.path.join(IMAGENES_PATH, nombre)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return FileResponse(filepath, media_type="image/png")

# =============================
# 10. Endpoint raíz
# =============================
@app.get("/")
async def root():
    return {"mensaje": "API de generación de imágenes con Hugging Face (Stable Diffusion XL)"}
