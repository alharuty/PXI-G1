import streamlit as st

class FormGenerator:
    def render_config_form(self):
        st.subheader("Configuración del Modelo")
        
        model_type = st.selectbox(
            "Modelo de IA",
            ["Auto", "Ollama (Local)", "Groq", "HuggingFace"],
            help="Selecciona el modelo de IA a utilizar"
        )
        
        return {"model_type": model_type}
    
    def render_content_form(self):
        topic = st.text_input(
            "📝 Tema del contenido",
            placeholder="Ej: Inteligencia Artificial en el marketing digital"
        )
        
        platform = st.selectbox(
            "📱 Plataforma",
            ["blog", "twitter", "instagram", "linkedin"],
            format_func=lambda x: {
                "blog": "📰 Blog",
                "twitter": "🐦 Twitter/X", 
                "instagram": "📸 Instagram",
                "linkedin": "💼 LinkedIn"
            }[x]
        )
        
        audience = st.selectbox(
            "👥 Audiencia",
            ["general", "technical", "marketing", "educational", "children"],
            format_func=lambda x: {
                "general": "👥 General",
                "technical": "🔧 Técnica",
                "marketing": "📈 Marketing",
                "educational": "📚 Educativa",
                "children": "👶 Infantil"
            }[x]
        )
        
        tone = st.selectbox(
            "🎭 Tono",
            ["professional", "casual", "friendly", "formal", "humorous"]
        )
        
        length = st.selectbox(
            "📏 Longitud",
            ["short", "medium", "long"],
            format_func=lambda x: {
                "short": "Corto",
                "medium": "Medio", 
                "long": "Largo"
            }[x]
        )
        
        keywords = st.text_input(
            "🏷️ Palabras clave (separadas por comas)",
            placeholder="IA, marketing, automatización"
        )
        
        language = st.selectbox(
            "🌍 Idioma",
            ["es", "en", "fr", "it"],
            format_func=lambda x: {
                "es": "🇪🇸 Español",
                "en": "🇺🇸 English",
                "fr": "🇫🇷 Francés",
                "it": "🇮🇹 Italiano"
             }[x]
        )
        
        return {
            "topic": topic,
            "platform": platform,
            "audience": audience,
            "tone": tone,
            "length": length,
            "keywords": keywords.split(",") if keywords else [],
            "language": language
        }