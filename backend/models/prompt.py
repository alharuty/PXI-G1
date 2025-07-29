from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str
    language: str
    coin_name: str | None = None
    uid: str | None = None

class ImagenRequest(BaseModel):
    tema: str
    audiencia: str
    estilo: str
    colores: str
    detalles: str = ""

class SimpleGenerationRequest(BaseModel):
    platform: str
    topic: str
    language: str 
    uid: str | None = None
