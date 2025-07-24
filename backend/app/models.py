from pydantic import BaseModel
from enum import Enum

class Language(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    IT = "it"

class GenerationRequest(BaseModel):
    platform: str
    topic: str
    language: Language = Language.ES

class GenerationResponse(BaseModel):
    content: str
