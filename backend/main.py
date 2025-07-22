from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.finnhub_client import get_stock_data
from services.nlp_generator import generate_summary
import re
from dotenv import load_dotenv

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

def extract_stock_symbol(text: str) -> str | None:
    # regex simple para buscar símbolos comunes (mayúsculas 1-5 letras)
    match = re.search(r'\b([A-Z]{1,5})\b', text)
    if match:
        return match.group(1)
    return None

@app.post("/generate")
def generate(req: PromptRequest):
    symbol = extract_stock_symbol(req.prompt)
    
    if symbol:
        stock_data = get_stock_data(symbol)
        if "error" in stock_data:
            # Si no encontró datos para ese símbolo, solo genera resumen simple
            resumen = generate_summary(req.prompt, language=req.language)
        else:
            texto = f"Datos del símbolo {symbol}: {stock_data}. Consulta: {req.prompt}"
            resumen = generate_summary(texto, language=req.language)
    else:
        # No hay símbolo, se genera resumen directo del prompt
        resumen = generate_summary(req.prompt, language=req.language)

    return {"response": resumen}
