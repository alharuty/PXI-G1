from pydantic import BaseModel

class GenerationRequest(BaseModel):
    platform: str
    topic: str

class GenerationResponse(BaseModel):
    content: str
