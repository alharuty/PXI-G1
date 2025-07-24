from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str
    language: str
    coin_name: str | None = None
    uid: str | None = None
