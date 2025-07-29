import streamlit as st
import json
from datetime import datetime

class ContentDisplay:
    def __init__(self):
        self.platform_icons = {
            "blog": "📰",
            "twitter": "🐦", 
            "instagram": "📸",
            "linkedin": "💼"
        }
    
    def render(self, content_response):
        """Renderiza el contenido generado con formato específico por plataforma"""
        if not content_response:
            st.info("No hay contenido para mostrar")
            return
        
        # Проверяем, является ли это RAG ответом
        if isinstance(content_response, dict) and "sources" in content_response:
            self._render_rag_content(content_response)
        else:
            self._render_regular_content(content_response)
    
    def _render_rag_content(self, rag_response):
        """Отображает RAG контент с источниками"""
        content = rag_response.get("content", "")
        sources = rag_response.get("sources", [])
        search_type = rag_response.get("search_type", "hybrid")
        total_sources = rag_response.get("total_sources", 0)
        topic = rag_response.get("topic", "")
        language = rag_response.get("language", "en")
        
        # Заголовок
        st.markdown(f"### 🧠 RAG Content: {topic}")
        
        # Информация о поиске
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Search Type", search_type.title())
        with col2:
            st.metric("Sources Used", total_sources)
        with col3:
            st.metric("Language", language.upper())
        with col4:
            word_count = len(content.split())
            st.metric("Words", word_count)
        
        # Основной контент
        st.markdown("#### 📄 Generated Content")
        st.markdown(content)
        
        # Источники
        if sources:
            st.markdown("#### 📚 Sources")
            for i, source in enumerate(sources, 1):
                with st.expander(f"Source {i}: {source.get('title', 'Unknown')}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Title:** {source.get('title', 'Unknown')}")
                        st.markdown(f"**Authors:** {', '.join(source.get('authors', []))}")
                        st.markdown(f"**Summary:** {source.get('summary', 'No summary available')}")
                        if source.get('link'):
                            st.markdown(f"**Link:** [{source['link']}]({source['link']})")
                    with col2:
                        relevance = source.get('relevance_score', 0)
                        st.metric("Relevance", f"{relevance:.3f}")
        
        # Действия
        self._render_rag_actions(content, rag_response)
    
    def _render_regular_content(self, content_response):
        """Отображает обычный контент"""
        content = content_response.get("content", "")
        metadata = content_response.get("metadata", {})
        
        # Obtener información de la plataforma del metadata o usar default
        platform = metadata.get("platform", "blog")
        
        # Header con información de la plataforma
        st.markdown(f"### {self.platform_icons.get(platform, '📝')} Contenido para {platform.title()}")
        
        # Mostrar metadata si está disponible
        if metadata:
            with st.expander("📊 Información del contenido"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    if "word_count" in metadata:
                        st.metric("Palabras", metadata["word_count"])
                with col2:
                    if "char_count" in metadata:
                        st.metric("Caracteres", metadata["char_count"])
                with col3:
                    if "estimated_read_time" in metadata:
                        st.metric("Tiempo lectura", f"{metadata['estimated_read_time']} min")
        
        # Mostrar contenido según la plataforma
        self._render_platform_specific(content, platform)
        
        # Acciones sobre el contenido
        self._render_actions(content, platform)
    
    def _render_rag_actions(self, content, rag_response):
        """Действия для RAG контента"""
        st.markdown("---")
        st.markdown("#### Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 Copy", key="copy_rag_btn"):
                st.write("📋 Content copied to clipboard")
        
        with col2:
            if st.button("💾 Download", key="download_rag_btn"):
                st.download_button(
                    label="📥 Download TXT",
                    data=content,
                    file_name=f"rag_content_{rag_response.get('topic', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
        
        with col3:
            if st.button("📊 Download Sources", key="download_sources_btn"):
                sources_data = json.dumps(rag_response.get("sources", []), indent=2)
                st.download_button(
                    label="📥 Download Sources JSON",
                    data=sources_data,
                    file_name=f"sources_{rag_response.get('topic', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
        
        with col4:
            if st.button("🔄 Regenerate", key="regenerate_rag_btn"):
                st.rerun()
    
    def _render_platform_specific(self, content, platform):
        """Renderiza el contenido con formato específico por plataforma"""
        if platform == "twitter":
            self._render_twitter_content(content)
        elif platform == "instagram":
            self._render_instagram_content(content)
        elif platform == "linkedin":
            self._render_linkedin_content(content)
        elif platform == "blog":
            self._render_blog_content(content)
        else:
            st.markdown(content)
    
    def _render_twitter_content(self, content):
        """Renderiza contenido de Twitter con preview"""
        st.markdown("#### Vista Previa de Tweet")
        
        # Simulación de tweet
        with st.container():
            st.markdown("""
            <div style="
                border: 1px solid #e1e8ed; 
                border-radius: 16px; 
                padding: 16px; 
                margin: 10px 0;
                background-color: white;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="
                        width: 32px; 
                        height: 32px; 
                        background-color: #1da1f2; 
                        border-radius: 50%; 
                        margin-right: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                    ">@</div>
                    <span style="font-weight: bold;">Mi Empresa</span>
                    <span style="color: #657786; margin-left: 4px;">@miempresa</span>
                </div>
                <div style="margin-bottom: 12px; line-height: 1.3;">
            """ + content + """
                </div>
                <div style="color: #657786; font-size: 14px;">
                    """ + datetime.now().strftime("%I:%M %p · %b %d, %Y") + """
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar análisis del tweet
        char_count = len(content)
        remaining = 280 - char_count
        
        col1, col2 = st.columns(2)
        with col1:
            if remaining >= 0:
                st.success(f"✅ Caracteres: {char_count}/280")
            else:
                st.error(f"❌ Excede por {abs(remaining)} caracteres")
        with col2:
            hashtag_count = content.count('#')
            st.info(f"🏷️ Hashtags: {hashtag_count}")
    
    def _render_instagram_content(self, content):
        """Renderiza contenido de Instagram con preview"""
        st.markdown("#### Vista Previa de Publicación Instagram")
        
        with st.container():
            st.markdown("""
            <div style="
                border: 1px solid #dbdbdb; 
                border-radius: 8px; 
                margin: 10px 0;
                background-color: white;
            ">
                <div style="padding: 16px; border-bottom: 1px solid #efefef;">
                    <div style="display: flex; align-items: center;">
                        <div style="
                            width: 32px; 
                            height: 32px; 
                            background: linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%); 
                            border-radius: 50%; 
                            margin-right: 12px;
                        "></div>
                        <span style="font-weight: 600;">miempresa</span>
                    </div>
                </div>
                <div style="
                    height: 300px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 18px;
                ">
                    📸 Imagen del contenido
                </div>
                <div style="padding: 16px;">
                    <div style="line-height: 1.4;">
            """ + content + """
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Análisis del contenido
        hashtag_count = content.count('#')
        mention_count = content.count('@')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Hashtags", hashtag_count)
        with col2:
            st.metric("Menciones", mention_count)
        with col3:
            st.metric("Líneas", len(content.split('\n')))
    
    def _render_linkedin_content(self, content):
        """Renderiza contenido de LinkedIn con preview"""
        st.markdown("#### Vista Previa de Publicación LinkedIn")
        
        with st.container():
            st.markdown("""
            <div style="
                border: 1px solid #e6e6e6; 
                border-radius: 8px; 
                margin: 10px 0;
                background-color: white;
            ">
                <div style="padding: 16px;">
                    <div style="display: flex; align-items: center; margin-bottom: 12px;">
                        <div style="
                            width: 48px; 
                            height: 48px; 
                            background-color: #0a66c2; 
                            border-radius: 50%; 
                            margin-right: 12px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-weight: bold;
                        ">ME</div>
                        <div>
                            <div style="font-weight: 600;">Mi Empresa</div>
                            <div style="color: #666; font-size: 14px;">CEO en Mi Empresa</div>
                            <div style="color: #666; font-size: 12px;">""" + datetime.now().strftime("%I:%M %p") + """</div>
                        </div>
                    </div>
                    <div style="line-height: 1.5; margin-bottom: 12px;">
            """ + content + """
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Análisis del contenido profesional
        word_count = len(content.split())
        sentences = content.count('.') + content.count('!') + content.count('?')
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Palabras", word_count)
        with col2:
            st.metric("Oraciones", sentences)
    
    def _render_blog_content(self, content):
        """Renderiza contenido de blog"""
        st.markdown("#### Artículo de Blog")
        
        # Renderizar contenido markdown
        st.markdown(content)
        
        # Análisis del artículo
        word_count = len(content.split())
        char_count = len(content)
        estimated_read_time = max(1, word_count // 200)
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Palabras", word_count)
        with col2:
            st.metric("Caracteres", char_count)
        with col3:
            st.metric("Tiempo lectura", f"{estimated_read_time} min")
    
    def _render_actions(self, content, platform):
        """Renderiza botones de acción para el contenido"""
        st.markdown("---")
        st.markdown("#### Acciones")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 Copiar", key="copy_btn"):
                st.write("📋 Contenido copiado al portapapeles")
                # En una implementación real, usarías JavaScript para copiar
        
        with col2:
            if st.button("💾 Descargar", key="download_btn"):
                st.download_button(
                    label="📥 Descargar TXT",
                    data=content,
                    file_name=f"contenido_{platform}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
        
        with col3:
            if st.button("🔄 Regenerar", key="regenerate_btn"):
                st.rerun()
        
        with col4:
            if st.button("⚙️ Editar", key="edit_btn"):
                self._render_editor(content)
    
    def _render_editor(self, content):
        """Renderiza editor de contenido"""
        st.markdown("#### ✏️ Editar Contenido")
        
        edited_content = st.text_area(
            "Edita tu contenido:",
            value=content,
            height=200,
            key="content_editor"
        )
        
        if st.button("💾 Guardar Cambios"):
            st.session_state.generated_content["content"] = edited_content
            st.success("¡Contenido actualizado!")
            st.rerun()