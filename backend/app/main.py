from fastapi import FastAPI, HTTPException
from app.models import GenerationRequest, GenerationResponse
from app.agents import generate_content

app = FastAPI(title="AI Content Generator")

@app.post("/generate", response_model=GenerationResponse)
def generate(req: GenerationRequest):
    try:
        content = generate_content(req.platform, req.topic)
        return GenerationResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
