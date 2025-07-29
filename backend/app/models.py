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
    uid: str = None  # ⭐ AGREGAR UID OPCIONAL

class GenerationResponse(BaseModel):
    content: str
