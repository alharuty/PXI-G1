#!/usr/bin/env python3
"""
ArXiv Search and RAG Comparison Frontend
Interface similar to the provided image with RAG vs Simple comparison
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8001"

# Page config
st.set_page_config(
    page_title="ArXiv Search & RAG Comparison",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .search-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #e1e5e9;
        margin-bottom: 2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .results-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #e1e5e9;
        margin-bottom: 2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .article-item {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e1e5e9;
        margin: 1rem 0;
    }
    .rag-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #e1e5e9;
        margin-bottom: 2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .response-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e1e5e9;
        margin: 1rem 0;
    }
    .comparison-box {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'selected_articles' not in st.session_state:
    st.session_state.selected_articles = []

def check_api_status():
    """Check API connection status"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# Header
st.markdown("""
<div class="main-header">
    <h1>🔍 Búsqueda y descarga de artículos de arXiv</h1>
    <p>Search and download articles from arXiv with RAG comparison</p>
</div>
""", unsafe_allow_html=True)

# API Status Check
api_status = check_api_status()
if not api_status:
    st.error("❌ API no disponible. Por favor, asegúrate de que el servidor esté ejecutándose en http://localhost:8001")
    st.stop()

# Section 1: ArXiv Search
st.markdown("""
<div class="search-section">
    <h2>🔍 Búsqueda de artículos</h2>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    topic = st.text_input(
        "Tema para buscar en arXiv:",
        value="Mathematics",
        placeholder="e.g., quantum computing, machine learning"
    )

with col2:
    max_results = st.number_input(
        "Cantidad de artículos:",
        min_value=1,
        max_value=20,
        value=2,
        step=1
    )

with col3:
    st.write("")  # Spacer
    search_button = st.button("🔍 Buscar artículos", type="primary", use_container_width=True)

# Search functionality
if search_button and topic:
    with st.spinner("Buscando artículos en arXiv..."):
        try:
            params = {
                'topic': topic,
                'max_results': max_results,
                'download_pdfs': True,
                'extract_text': True
            }
            
            response = requests.get(f"{API_BASE}/arxiv/search", params=params)
            
            if response.status_code == 200:
                result = response.json()
                articles = result.get('articles', result.get('documents', []))
                st.session_state.search_results = articles
                st.success(f"✅ Encontrados {len(articles)} artículos")
            else:
                st.error(f"Error en la búsqueda: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Section 2: Search Results
if st.session_state.search_results:
    st.markdown("""
    <div class="results-section">
        <h2>📄 Resultados de la búsqueda</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Display articles
    for i, article in enumerate(st.session_state.search_results):
        with st.container():
            st.markdown(f"""
            <div class="article-item">
                <h3>{i+1}. {article.get('title', 'Sin título')}</h3>
                <p><strong>Autores:</strong> {', '.join(article.get('authors', []))}</p>
                <p><strong>Resumen:</strong> {article.get('abstract', 'Sin resumen')}</p>
                <p><strong>arXiv ID:</strong> {article.get('arxiv_id', 'N/A')}</p>
                <p><strong>Publicado:</strong> {article.get('published_date', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_art1, col_art2, col_art3 = st.columns([1, 1, 1])
            
            with col_art1:
                if article.get('pdf_url'):
                    st.link_button("📥 Descargar PDF", article['pdf_url'])
            
            with col_art2:
                if article.get('browser_url'):
                    st.link_button("🌐 Ver en arXiv", article['browser_url'])
            
            with col_art3:
                selected = st.checkbox(
                    f"Agregar a la base de datos",
                    key=f"select_{i}",
                    value=False
                )
                if selected:
                    if i not in st.session_state.selected_articles:
                        st.session_state.selected_articles.append(i)
                else:
                    if i in st.session_state.selected_articles:
                        st.session_state.selected_articles.remove(i)
    
    # Add selected articles to vector database
    if st.session_state.selected_articles:
        if st.button("📥 Agregar seleccionados a la base vectorial", type="primary"):
            with st.spinner("Agregando artículos a la base de datos..."):
                try:
                    selected_articles = [st.session_state.search_results[i] for i in st.session_state.selected_articles]
                    
                    # Create search result format
                    search_result = {
                        'topic': topic,
                        'search_date': datetime.now().isoformat(),
                        'total_found': len(selected_articles),
                        'documents': selected_articles
                    }
                    
                    response = requests.post(f"{API_BASE}/vector/add_articles_from_search", json=search_result)
                    
                    if response.status_code == 200:
                        st.success(f"✅ {len(selected_articles)} artículos agregados a la base de datos")
                        st.session_state.selected_articles = []
                        st.rerun()
                    else:
                        st.error("Error al agregar artículos")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Section 3: Knowledge Base Query with RAG Comparison
st.markdown("""
<div class="rag-section">
    <h2>❓ Preguntas sobre la base de conocimientos</h2>
    <p>Introduce una pregunta sobre los artículos cargados</p>
</div>
""", unsafe_allow_html=True)

# Query input
query = st.text_input(
    "Tu pregunta:",
    value="what is the Pythagorean theorem",
    placeholder="e.g., what is quantum computing?"
)

# Hardcode parameters
top_k = 5
temperature = 0.7
max_tokens = 1024

# Get answer button
if st.button("🤖 Obtener respuesta", type="primary", use_container_width=True):
    if query:
        with st.spinner("Generando respuestas..."):
            try:
                # Get RAG vs Simple comparison
                params = {
                    'query': query,
                    'top_k': top_k,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
                
                response = requests.get(f"{API_BASE}/rag/compare", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display comparison
                    st.markdown("### 📊 Comparación de Respuestas")
                    
                    col_resp1, col_resp2 = st.columns(2)
                    
                    with col_resp1:
                        st.markdown("#### 🤖 Respuesta con RAG")
                        rag_response = result.get('rag_response', {})
                        
                        # Get source documents info
                        source_docs = result.get('source_documents', [])
                        documents_used = rag_response.get('documents_used', 0)
                        
                        response_text = rag_response.get('response', 'Sin respuesta')
                        
                        # Add source information if documents were used
                        if documents_used > 0 and source_docs:
                            response_text += "\n\n**📚 Fuentes utilizadas:**\n"
                            for i, doc in enumerate(source_docs[:3], 1):  # Show first 3 sources
                                title = doc.get('title', 'Sin título')
                                score = doc.get('score', 0)
                                response_text += f"{i}. {title} (score: {score:.3f})\n"
                        
                        st.markdown(f"""
                        <div class="response-box">
                            {response_text}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_resp2:
                        st.markdown("#### 🧠 Respuesta Simple")
                        simple_response = result.get('simple_response', {})
                        st.markdown(f"""
                        <div class="response-box">
                            {simple_response.get('response', 'Sin respuesta')}
                        </div>
                        """, unsafe_allow_html=True)
                        
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Por favor, introduce una pregunta")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🔬 ArXiv Search & RAG Comparison | Powered by Groq LLM & HuggingFace</p>
    <p>Búsqueda de artículos científicos con comparación RAG vs Simple</p>
</div>
""", unsafe_allow_html=True) 