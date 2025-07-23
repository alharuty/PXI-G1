from fastapi import FastAPI, HTTPException, Query
from app.models import GenerationRequest, GenerationResponse
from app.agents import generate_content
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="AI Content Generator")

@app.post("/generate", response_model=GenerationResponse)
def generate(req: GenerationRequest, provider: str = Query("groq", enum=["groq", "ollama"])):
    try:
        content = generate_content(req.platform, req.topic, provider=provider)
        return GenerationResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
