prompts = {
"twitter": {
        "es": "Crea un tweet llamativo sobre: {topic}",
        "en": "Create an engaging tweet about: {topic}",
        "fr": "Créez un tweet attrayant sur: {topic}",
        "it": "Crea un tweet accattivante su: {topic}"
    },
    "linkedin": {
        "es": "Escribe una publicación profesional de LinkedIn sobre: {topic}",
        "en": "Write a professional LinkedIn post about: {topic}",
        "fr": "Rédigez une publication LinkedIn professionnelle sur: {topic}",
        "it": "Scrivi un post professionale su LinkedIn riguardo: {topic}"
    },
    "instagram": {
        "es": "Genera un pie de foto creativo para Instagram sobre: {topic}",
        "en": "Generate a creative Instagram caption about: {topic}",
        "fr": "Générez une légende Instagram créative sur: {topic}",
        "it": "Genera una didascalia creativa per Instagram su: {topic}"
    },
    "email": {
        "es": "Escribe un email profesional sobre: {topic}",
        "en": "Write a professional email about: {topic}",
        "fr": "Rédigez un email professionnel sur: {topic}",
        "it": "Scrivi una email professionale su: {topic}"
    },
    "descripcion": {
        "es": "Escribe una descripción de producto para: {topic}",
        "en": "Write a product description for: {topic}",
        "fr": "Rédigez une description de produit pour: {topic}",
        "it": "Scrivi una descrizione del prodotto per: {topic}"
    }
}

def get_prompt(platform: str, topic: str, language: str = "es") -> str:
    plataform_templates = prompts.get(platform.lower())
    if not plataform_templates:
        raise ValueError("Plataforma no soportada")
    
    template = plataform_templates.get(language)
    if not template:
        raise ValueError("Idioma {language} no soportado")
    
    return template.format(topic=topic)