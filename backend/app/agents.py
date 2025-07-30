from app.config import get_llm
from app.prompts import get_prompt

def generate_content(platform: str, topic: str, language: str = "es", provider: str = "groq") -> str:
    llm = get_llm(provider=provider)
    prompt = get_prompt(platform, topic, language)
    # Instruccion especifica para la deteccion del idioma
    language_instruction = {
        "es": "Responde en español: ",
        "en": "Answer in English: ",
        "fr": "Répondez en français: ",
        "it": "Rispondi in italiano: "
    }.get(language, "Responde en español: ")

    full_prompt = language_instruction + prompt
    response = llm.invoke(full_prompt)
    return response
