import os
import re
import time
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import os
from datetime import datetime
import base64
from dotenv import load_dotenv
import re
import time
from time import time as time_now
from backend.app.agents import generate_content
from backend.app.arXiv import ArxivExtractor
from backend.app.models import (
    GenerationRequest, 
    GenerationResponse
)
from backend.app.rag_generator import RAGGenerator
from backend.app.vector_store_config import create_vector_store, get_storage_status
from .firebase_config import db
from backend.models.prompt import PromptRequest, ImagenRequest, SimpleGenerationRequest
from backend.services.utils import extract_stock_symbol, get_symbol_from_coin_name
from backend.services.alpha_client import get_crypto_price, get_stock_data
from backend.services.crypto_utils import CRYPTO_LIST
from backend.services.nlp_generator import generate_summary
from backend.services.img_generation_functions import (
    crear_prompt_optimizado, 
    generar_imagen_huggingface, 
    generar_imagen_fallback, 
    sanitize_filename, 
    subir_imagen_a_supabase
)
from backend.app.agents import generate_content as generate_content_agent
from backend.DB.supabase_client import supabase
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="🤖 BUDDY API Unificada", 
    description="API completa con NLP y generación de imágenes integrada",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# UID validation regex
UID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{6,128}$")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # print("🚀 FastAPI application starting...")
    # print("📖 Swagger documentation: http://localhost:8001/docs")
    # print("✅ Application ready to work!")

    yield

#Shutdown
    print("🛑 Application stopping...")

#Vector database (configurable storage - local, qdrant_local, or qdrant_cloud)
try:
    vector_store = create_vector_store()
    storage_status = get_storage_status()
    print(f"✅ Using {storage_status['current_storage']} storage")
except Exception as e:
    print(f"❌ Error creating vector store: {e}")
    print("🔄 Falling back to local storage")
    from app.local_vector_store import SimpleHuggingFaceStore
    vector_store = SimpleHuggingFaceStore(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        chunk_size=512,
        chunk_overlap=50
    )

# RAG generator
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("⚠️ Warning: GROQ_API_KEY not found. RAG endpoints will not work.")
    print("   Please set: $env:GROQ_API_KEY='your-api-key'")
    rag_generator = None
else:
    rag_generator = RAGGenerator(api_key=groq_api_key)

@app.get("/")
def root():
    """Root endpoint for checking server status"""
    return {
        "message": "🤖 BUDDY API Unificada con RAG Científico",
        "status": "running",
        "version": "2.0.0",
        "services": {
            "nlp": "✅ Integrado",
            "images": "✅ Integrado", 
            "rag": "✅ Integrado",
            "vector_db": "✅ Integrado",
            "firebase": "✅" if db is not None else "❌ Deshabilitado",
            "supabase": "✅" if supabase else "❌"
        },
        "endpoints": {
            "generate": "/generate",
            "arxiv_search": "/arxiv/search",
            "vector_add": "/vector/add_articles_from_search",
            "rag_generate": "/rag/generate",
            "rag_compare": "/rag/compare",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check():
    """Server health check"""
    return {"status": "healthy", "message": "Server is running normally"}


@app.get("/arxiv/search")
def search_arxiv_papers_get(
    topic: str = Query(..., description="Topic for article search"),
    max_results: int = Query(5, ge=1, le=50, description="Maximum number of results"),
    download_pdfs: bool = Query(True, description="Whether to download PDF files"),
    extract_text: bool = Query(True, description="Whether to extract full text from PDF"),
    days_back: int = Query(365, ge=1, le=3650, description="Number of days back for search"),
    categories: str = Query(None, description="arXiv categories separated by comma")
):
    """Búsqueda de artículos científicos en arXiv"""
    print(f"🔍 Búsqueda de artículos: topic='{topic}', count={max_results}")
    
    try:
        # Parse categories if specified
        category_list = None
        if categories:
            category_list = [cat.strip() for cat in categories.split(",")]
            print(f"📂 Category filter: {category_list}")
        
        # Create arXiv extractor
        extractor = ArxivExtractor()
        
        # Execute search
        results = extractor.search_and_download(
            topic=topic,
            max_results=max_results,
            download_pdfs=download_pdfs,
            extract_text=extract_text,
            output_dir="arxiv_papers"
        )
        
        print(f"✅ Found {results['total_found']} articles for topic '{topic}'")
        return results
        
    except Exception as e:
        print(f"❌ Error searching articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching articles: {str(e)}")

@app.post("/vector/add_articles_from_search")
def add_articles_from_search(search_result: Dict):
    """Agregar artículos a la base de datos vectorial"""
    print(f"📥 Adding articles from search result...")
    
    try:
        documents = search_result.get('documents', [])
        if not documents:
            raise HTTPException(status_code=400, detail="No documents found in search result")
        
        print(f"📥 Found {len(documents)} documents to add")
        
        # Clean and validate data
        cleaned_articles = []
        for doc in documents:
            cleaned_article = {}
            for key, value in doc.items():
                if isinstance(value, str):
                    if key == 'full_text':
                        cleaned_article[key] = value[:50000]  # Limit to 50KB
                    else:
                        cleaned_article[key] = value[:1000]   # Limit other fields
                else:
                    cleaned_article[key] = value
            cleaned_articles.append(cleaned_article)
        
        processed = vector_store.add_documents(cleaned_articles)
        print(f"✅ Processed {processed} articles")
        
        return {
            "search_metadata": {
                "topic": search_result.get('topic', ''),
                "search_date": search_result.get('search_date', ''),
                "total_found": search_result.get('total_found', 0)
            },
            "vector_results": {
                "processed": processed,
                "total_documents": len(vector_store.documents)
            }
        }
    except Exception as e:
        print(f"❌ Error adding articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding articles: {str(e)}")

@app.get("/vector/search")
def search_vector_store(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results"),
    similarity_threshold: float = Query(0.5, ge=0.0, le=1.0, description="Similarity threshold")
):
    """Buscar en la base de datos vectorial"""
    print(f"🔍 Search in vector database: '{query}'")
    
    try:
        results = vector_store.search(
            query=query,
            top_k=top_k,
            min_score=similarity_threshold
        )
        
        print(f"✅ Found {len(results)} relevant fragments")
        return {
            "query": query,
            "total_found": len(results),
            "results": results
        }
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/vector/statistics")
def get_vector_store_statistics():
    """Estadísticas de la base de datos vectorial"""
    print("📊 Getting vector database statistics...")
    
    try:
        stats = vector_store.get_statistics()
        storage_status = get_storage_status()
        print(f"✅ Statistics received: {stats.get('total_documents', 0)} documents")
        return {
            "statistics": stats,
            "storage_config": storage_status
        }
    except Exception as e:
        print(f"❌ Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@app.post("/rag/generate")
def generate_rag_response(
    query: str = Query(..., description="User query for RAG generation"),
    top_k: int = Query(5, ge=1, le=10, description="Number of documents to retrieve"),
    temperature: float = Query(0.7, ge=0.0, le=2.0, description="Generation temperature"),
    max_tokens: int = Query(1024, ge=100, le=4096, description="Maximum tokens to generate"),
    stream: bool = Query(False, description="Whether to stream the response")
):
    """Generar respuesta RAG usando documentos recuperados"""
    print(f"🤖 RAG generation for query: '{query}'")
    
    if not rag_generator:
        raise HTTPException(status_code=500, detail="RAG generator not initialized. Please set GROQ_API_KEY.")
    
    try:
        # Search in vector database
        retrieved_docs = vector_store.search(
            query=query,
            top_k=top_k,
            min_score=0.1
        )
        
        if not retrieved_docs:
            print("⚠️ No relevant documents found, generating simple response")
            response = rag_generator.generate_simple_response(
                query=query,
                temperature=temperature,
                max_tokens=max_tokens
            )
            response["documents_retrieved"] = 0
            return response
        
        print(f"📚 Retrieved {len(retrieved_docs)} relevant documents")
        
        # Generate RAG response
        response = rag_generator.generate_rag_response(
            query=query,
            retrieved_documents=retrieved_docs,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        response["documents_retrieved"] = len(retrieved_docs)
        response["source_documents"] = retrieved_docs
        
        return response
        
    except Exception as e:
        print(f"❌ RAG generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG generation error: {str(e)}")

@app.get("/rag/compare")
def compare_rag_vs_simple(
    query: str = Query(..., description="Query to compare RAG vs simple generation"),
    top_k: int = Query(5, ge=1, le=10, description="Number of documents to retrieve"),
    temperature: float = Query(0.7, ge=0.0, le=2.0, description="Generation temperature"),
    max_tokens: int = Query(1024, ge=100, le=4096, description="Maximum tokens to generate")
):
    """Comparar respuesta RAG vs respuesta simple"""
    print(f"⚖️ Comparing RAG vs Simple for query: '{query}'")
    
    if not rag_generator:
        raise HTTPException(status_code=500, detail="RAG generator not initialized.")
    
    try:
        # Get RAG response
        retrieved_docs = vector_store.search(
            query=query,
            top_k=top_k,
            min_score=0.1
        )
        
        rag_response = rag_generator.generate_rag_response(
            query=query,
            retrieved_documents=retrieved_docs,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        # Get simple response
        simple_response = rag_generator.generate_simple_response(
            query=query,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "query": query,
            "rag_response": {
                "response": rag_response.get("response", ""),
                "documents_used": len(retrieved_docs),
                "model": rag_response.get("model", ""),
                "usage": rag_response.get("usage", {})
            },
            "simple_response": {
                "response": simple_response.get("response", ""),
                "model": simple_response.get("model", ""),
                "usage": simple_response.get("usage", {})
            },
            "comparison": {
                "rag_has_documents": len(retrieved_docs) > 0,
                "rag_response_length": len(rag_response.get("response", "")),
                "simple_response_length": len(simple_response.get("response", ""))
            }
        }
        
    except Exception as e:
        print(f"❌ Comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")

# =============================
# ENDPOINTS EXISTENTES
# =============================

@app.post("/news-nlp")
def generate_news_nlp(req: PromptRequest):
    """Endpoint para generar resúmenes de noticias financieras"""
    start_time = time_now()
    
    try:
        data_chunks = []
        user_bio = ""

        if req.uid and db is not None:
            if not UID_REGEX.match(req.uid):
                raise HTTPException(status_code=400, detail="UID inválido.")
            
            try:
                doc_ref = db.collection("users").document(req.uid)
                doc = doc_ref.get()
                if doc.exists:
                    user_data = doc.to_dict()
                    user_bio = user_data.get("bio", "")
            except Exception as e:
                print(f"Error accediendo a Firebase: {e}")

        symbol = extract_stock_symbol(req.prompt)
        crypto_symbol = None
        if req.coin_name:
            crypto_symbol = get_symbol_from_coin_name(req.coin_name)
            if not crypto_symbol:
                return {"response": f"Criptomoneda '{req.coin_name}' no encontrada."}

        if symbol:
            stock_data = get_stock_data(symbol)
            if "error" not in stock_data:
                data_chunks.append(f"Datos de la acción {symbol}: {stock_data}")

        if crypto_symbol:
            crypto_data = get_crypto_price(crypto_symbol)
            if "error" not in crypto_data:
                data_chunks.append(f"Precio de {req.coin_name} ({crypto_symbol}): {crypto_data}")

        context = "\n".join(data_chunks) if data_chunks else req.prompt
        if user_bio:
            full_context = f"Contexto del usuario: {user_bio}\n\nSolicitud:\n\n{context}"
        else:
            full_context = context

        resumen = generate_summary(full_context, language=req.language)
        
        execution_time = round(time_now() - start_time, 2)

        if supabase:
            try:
                supabase.table("Trazabilidad").insert({
                    "User_id": req.uid if req.uid else None,
                    "used_model": "groq",
                    "Prompt": req.prompt,
                    "Language": req.language,
                    "Output": resumen,
                    "Execution_time": execution_time
                }).execute()
                print("📊 Registro de trazabilidad guardado en Supabase")
            except Exception as e:
                print(f"❌ Error guardando trazabilidad en Supabase: {e}")

        return {"response": resumen}
        
    except Exception as e:
        print(f"Error en news-nlp: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-image")
async def generate_image(req: ImagenRequest):
    """Genera imagen con manejo robusto de errores y fallbacks"""
    try:
        print(f"🎯 Nueva solicitud de imagen: {req.tema}")
        
        prompt_optimizado = crear_prompt_optimizado(req)
        print(f"✨ Prompt optimizado: {prompt_optimizado}")
        
        img_bytes = None
        error_message = None
        
        try:
            img_bytes = generar_imagen_huggingface(prompt_optimizado)
        except HTTPException as e:
            error_message = e.detail
            print(f"❌ Error en Hugging Face: {error_message}")
            
            img_bytes = generar_imagen_fallback(prompt_optimizado)
            if img_bytes is None:
                raise HTTPException(
                    status_code=503, 
                    detail=f"Servicio de imágenes no disponible: {error_message}"
                )
        
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tema_safe = sanitize_filename(req.tema)
        nombre_archivo = f"{timestamp}_{tema_safe}.png"
        
        url_supabase = None
        if error_message is None:
            url_supabase = subir_imagen_a_supabase(nombre_archivo, img_bytes)
        
        response = {
            "filename": nombre_archivo,
            "imagen": img_b64,
            "descripcion": prompt_optimizado,
        }
        
        if error_message:
            response["mensaje"] = f"⚠️ Imagen placeholder generada: {error_message}"
            response["is_placeholder"] = True
        else:
            response["mensaje"] = "✅ Imagen generada exitosamente"
            response["is_placeholder"] = False
            
        if url_supabase:
            response["url_supabase"] = url_supabase
        
        return response
        
    except Exception as e:
        print(f"💥 Error crítico generando imagen: {e}")
        raise HTTPException(status_code=500, detail=f"Error crítico en generación de imagen: {str(e)}")

# =============================
# CORS OPTIONS
# =============================

@app.options("/{path:path}")
async def options_handler():
    """Handle OPTIONS requests for CORS"""
    return {"message": "OK"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting BUDDY API with RAG support...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

