prompts = {
    "twitter": "Crea un tweet llamativo sobre: {topic}",
    "linkedin": "Escribe una publicación profesional de LinkedIn sobre: {topic}",
    "instagram": "Genera un pie de foto creativo para Instagram sobre: {topic}",
    "email": "Escribe un email profesional sobre: {topic}",
    "descripcion": "Escribe una descripción de producto para: {topic}"
}

def get_prompt(platform: str, topic: str) -> str:
    template = prompts.get(platform.lower())
    if not template:
        raise ValueError("Plataforma no soportada")
    return template.format(topic=topic)