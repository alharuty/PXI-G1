from app.config import get_llm
from app.prompts import get_prompt

def generate_content(platform: str, topic: str) -> str:
    llm = get_llm()
    prompt = get_prompt(platform, topic)
    response = llm.invoke(prompt)
    return response
