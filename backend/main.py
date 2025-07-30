import os
import re
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
        "message": "AI Content Generator API is running!",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate",
            "arxiv_search_get": "/arxiv/search (GET)",
            "docs": "/docs",
            "redoc": "/redoc"
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
    categories: str = Query(None, description="arXiv categories separated by comma (e.g., cs.AI,quant-ph)")
):
    """
    GET endpoint for searching scientific articles in arXiv
    
    Args:
        topic: Search topic
        max_results: Maximum number of results (1-50)
        download_pdfs: Whether to download PDF files
        extract_text: Whether to extract full text from PDF
        days_back: Number of days back for search
        categories: arXiv categories separated by comma
        
    Returns:
        List of found articles with metadata
    """
    print(f"🔍 GET request for article search: topic='{topic}', count={max_results}")
    
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
        
        # Debug: Print found articles
        if 'documents' in results:
            for i, article in enumerate(results['documents']):
                print(f"  Found Article {i+1}:")
                print(f"    Title: {article.get('title', 'MISSING')}")
                print(f"    ArXiv ID: {article.get('arxiv_id', 'MISSING')}")
                print(f"    Authors: {article.get('authors', 'MISSING')}")
                print(f"    Full text length: {len(article.get('full_text', ''))}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching articles: {str(e)}")



@app.post("/vector/add_articles_from_search")
def add_articles_from_search(search_result: Dict):
    """
    Adds articles from search result to vector database
    
    Args:
        search_result: Search result with documents field
        
    Returns:
        Processing result
    """
    print(f"🔍 Adding articles from search result...")
    print(f"🔍 Search result keys: {list(search_result.keys())}")
    
    # Extract documents from search result
    documents = search_result.get('documents', [])
    if not documents:
        raise HTTPException(status_code=400, detail="No documents found in search result")
    
    print(f"🔍 Found {len(documents)} documents to add")
    
    # Debug: Print document details
    for i, doc in enumerate(documents):
        print(f"  Document {i+1}:")
        print(f"    Type: {type(doc)}")
        print(f"    Keys: {list(doc.keys()) if isinstance(doc, dict) else 'NOT A DICT'}")
        print(f"    Title: {doc.get('title', 'MISSING')}")
        print(f"    ArXiv ID: {doc.get('arxiv_id', 'MISSING')}")
        print(f"    Authors: {doc.get('authors', 'MISSING')}")
        print(f"    Full text length: {len(doc.get('full_text', ''))}")
    
    try:
        # Clean and validate data
        cleaned_articles = []
        for doc in documents:
            cleaned_article = {}
            for key, value in doc.items():
                if isinstance(value, str):
                    # Limit text size and clean special characters
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
    similarity_threshold: float = Query(0.5, ge=0.0, le=1.0, description="Similarity threshold"),
    use_hybrid_search: bool = Query(True, description="Use hybrid search (vector + keyword)"),
    search_type: str = Query("general", enum=["general", "definitions", "concepts"], description="Type of search")
):
    """
    Enhanced search articles in vector database
    
    Args:
        query: Search query
        top_k: Number of results
        similarity_threshold: Similarity threshold
        use_hybrid_search: Use hybrid search
        search_type: Type of search (general, definitions, concepts)
        
    Returns:
        List of found articles with relevance
    """
    print(f"🔍 Enhanced search in vector database: '{query}' (type: {search_type})")
    
    try:
        # Modify query based on search type
        if search_type == "definitions":
            modified_query = f"definition explanation what is {query}"
            similarity_threshold = min(similarity_threshold, 0.3)  # Lower threshold for definitions
            top_k = top_k * 2  # Get more candidates for filtering
        elif search_type == "concepts":
            modified_query = f"concept {query} key terms important"
        else:
            modified_query = query
        
        results = vector_store.search(
            query=modified_query,
            top_k=top_k,
            use_hybrid=use_hybrid_search,
            min_score=similarity_threshold  # Use similarity_threshold as min_score
        )
        
        # Post-process results based on search type
        if search_type == "definitions":
            # Filter for results that likely contain definitions
            filtered_results = []
            for result in results:
                text = result.get('text_snippet', '').lower()
                has_definition = any(term in text for term in [
                    'is ', 'are ', 'means ', 'refers to', 'defined as', 
                    'definition', 'explanation', 'refers to'
                ])
                
                if has_definition or result.get('has_definitions', False):
                    filtered_results.append(result)
            results = filtered_results[:top_k // 2]  # Return original top_k
        
        elif search_type == "concepts":
            # Enhance results with concept analysis
            for result in results:
                text = result.get('text_snippet', '')
                # Extract potential concepts from text
                concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
                concepts = [c for c in concepts if len(c) > 3 and c.lower() not in ['title', 'authors', 'abstract', 'full text']]
                result['extracted_concepts'] = concepts[:5]  # Top 5 concepts
        
        print(f"✅ Found {len(results)} relevant fragments")
        return {
            "query": query,
            "total_found": len(results),
            "search_type": f"enhanced_{search_type}",
            "results": results
        }
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")



@app.get("/vector/statistics")
def get_vector_store_statistics():
    """
    Returns vector database statistics and storage configuration
    
    Returns:
        Vector database statistics and storage config
    """
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

@app.delete("/vector/clear")
def clear_vector_store():
    """
    Clears vector database
    
    Returns:
        Clear result
    """
    print("🗑️ Clearing vector database...")
    
    try:
        vector_store.clear()
        print("✅ Vector database cleared")
        return {"message": "Vector database cleared", "status": "success"}
    except Exception as e:
        print(f"❌ Clear error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Clear error: {str(e)}")


# Combined search and vectorize endpoint removed - using separate endpoints instead

@app.post("/rag/generate")
def generate_rag_response(
    query: str = Query(..., description="User query for RAG generation"),
    top_k: int = Query(5, ge=1, le=10, description="Number of documents to retrieve"),
    temperature: float = Query(0.7, ge=0.0, le=2.0, description="Generation temperature"),
    max_tokens: int = Query(1024, ge=100, le=4096, description="Maximum tokens to generate"),
    stream: bool = Query(False, description="Whether to stream the response")
):
    """
    Generate RAG response using retrieved documents and Groq LLM
    
    Args:
        query: User's question
        top_k: Number of documents to retrieve
        temperature: Generation temperature
        max_tokens: Maximum tokens to generate
        stream: Whether to stream response
        
    Returns:
        RAG response with source documents
    """
    print(f"🤖 RAG generation for query: '{query}'")
    
    if not rag_generator:
        raise HTTPException(status_code=500, detail="RAG generator not initialized. Please set GROQ_API_KEY environment variable.")
    
    try:
        # Step 1: Search in vector database
        print("🔍 Searching vector database...")
        retrieved_docs = vector_store.search(
            query=query,
            top_k=top_k,
            min_score=0.1  # Lower threshold for search
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
        
        # Step 2: Generate RAG response
        print("🧠 Generating RAG response with Groq...")
        response = rag_generator.generate_rag_response(
            query=query,
            retrieved_documents=retrieved_docs,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        # Add metadata
        response["documents_retrieved"] = len(retrieved_docs)
        response["source_documents"] = retrieved_docs
        
        print(f"✅ RAG response generated successfully")
        
        # Add document analysis
        if rag_generator:
            analysis = rag_generator.analyze_retrieved_documents(query, retrieved_docs)
            response["document_analysis"] = analysis
        
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
    """
    Compare RAG response vs simple LLM response
    
    Args:
        query: User's question
        top_k: Number of documents to retrieve
        temperature: Generation temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Comparison of both responses
    """
    print(f"🔄 Comparing RAG vs Simple for query: '{query}'")
    
    if not rag_generator:
        raise HTTPException(status_code=500, detail="RAG generator not initialized. Please set GROQ_API_KEY environment variable.")
    
    try:
        # Get RAG response
        print("🤖 Generating RAG response...")
        retrieved_docs = vector_store.search(
            query=query,
            top_k=top_k,
            min_score=0.1  # Lower threshold for search
        )
        
        rag_response = rag_generator.generate_rag_response(
            query=query,
            retrieved_documents=retrieved_docs,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        # Get simple response
        print("🧠 Generating simple response...")
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

@app.get("/rag/analyze_documents")
def analyze_retrieved_documents(
    query: str = Query(..., description="Query to analyze documents for"),
    top_k: int = Query(5, ge=1, le=10, description="Number of documents to retrieve"),
    similarity_threshold: float = Query(0.5, ge=0.0, le=1.0, description="Similarity threshold")
):
    """
    Analyze retrieved documents for a query
    
    Args:
        query: User's question
        top_k: Number of documents to retrieve
        similarity_threshold: Similarity threshold
        
    Returns:
        Analysis of retrieved documents
    """
    print(f"🔍 Analyzing documents for query: '{query}'")
    
    if not rag_generator:
        raise HTTPException(status_code=500, detail="RAG generator not initialized. Please set GROQ_API_KEY environment variable.")
    
    try:
        # Search in vector database
        print("🔍 Searching vector database...")
        retrieved_docs = vector_store.search(
            query=query,
            top_k=top_k,
            min_score=similarity_threshold
        )
        
        if not retrieved_docs:
            return {
                "query": query,
                "message": "No documents found",
                "analysis": {
                    "total_documents": 0,
                    "has_relevant_content": False,
                    "topics_found": []
                }
            }
        
        print(f"📚 Retrieved {len(retrieved_docs)} documents for analysis")
        
        # Analyze documents
        analysis = rag_generator.analyze_retrieved_documents(query, retrieved_docs)
        
        return {
            "query": query,
            "total_documents_retrieved": len(retrieved_docs),
            "analysis": analysis
        }
        
    except Exception as e:
        print(f"❌ Document analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document analysis error: {str(e)}")

security = HTTPBearer()

# Variables globales
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
UID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{6,128}$")

@app.post("/generate")
async def generate_simple(req: SimpleGenerationRequest):
    """
    Endpoint simplificado para generar contenido de texto
    Compatible con el frontend TextGenerator.js
    """
    try:
        print(f"🎯 Solicitud de generación: {req.platform} | {req.topic} | {req.language}")
        
        # Validaciones básicas
        if not req.topic or not req.topic.strip():
            raise HTTPException(status_code=400, detail="Topic es requerido")
        
        if not req.platform:
            raise HTTPException(status_code=400, detail="Platform es requerida")
        
        # Obtener contexto del usuario si está disponible
        user_bio = ""
        if req.uid and db is not None:
            try:
                if UID_REGEX.match(req.uid):
                    doc_ref = db.collection("users").document(req.uid)
                    doc = doc_ref.get()
                    if doc.exists:
                        user_data = doc.to_dict()
                        user_bio = user_data.get("bio", "")
            except Exception as e:
                print(f"⚠️ Error accediendo a Firebase: {e}")
        
        # Agregar contexto del usuario si existe
        topic_with_context = req.topic
        if user_bio:
            topic_with_context = f"Contexto del usuario: {user_bio}\n\nTema: {req.topic}"
        
        start_time = time.time()
        # Generar contenido usando el sistema de agentes
        content = generate_content(
            platform=req.platform,
            topic=topic_with_context,
            language=req.language,
            provider="groq"
        )
        
        end_time = time.time() # Registrar el tiempo de finalización
        execution_time = end_time - start_time # Calcular el tiempo de ejecución

        # Guardar en trazabilidad si hay usuario
        if req.uid and supabase:
            try:
                data = {
                    "User_id": req.uid,
                    "used_model": "groq",
                    "Prompt": req.topic,  # Prompt original
                    "Language": req.language,
                    "Output": content,
                    "Execution_time": execution_time
                }
                print(f"DEBUG: Data to be inserted: {data}")
                supabase.table('Trazabilidad').insert(data).execute()
                print("✅ Guardado en trazabilidad")
            except Exception as e:
                print(f"⚠️ Error guardando en trazabilidad: {e}")
        
        return {"content": content}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"💥 Error generando contenido: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


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
        
        # Calcular tiempo de ejecución
        execution_time = round(time_now() - start_time, 2)

        # Guardar en trazabilidad
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
        print(f"👥 Audiencia: {req.audiencia} | 🎨 Estilo: {req.estilo} | 🌈 Colores: {req.colores}")
        
        # Crear prompt optimizado
        prompt_optimizado = crear_prompt_optimizado(req)
        print(f"✨ Prompt optimizado: {prompt_optimizado}")
        
        # Intentar generar imagen
        img_bytes = None
        error_message = None
        
        try:
            img_bytes = generar_imagen_huggingface(prompt_optimizado)
        except HTTPException as e:
            error_message = e.detail
            print(f"❌ Error en Hugging Face: {error_message}")
            
            # Intentar generar imagen placeholder
            img_bytes = generar_imagen_fallback(prompt_optimizado)
            if img_bytes is None:
                raise HTTPException(
                    status_code=503, 
                    detail=f"Servicio de imágenes no disponible: {error_message}"
                )
        
        # Convertir a base64
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        # Crear nombre único con sanitización
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tema_safe = sanitize_filename(req.tema)
        nombre_archivo = f"{timestamp}_{tema_safe}.png"
        
        print(f"📁 Nombre de archivo: {nombre_archivo}")
        
        # Subir a Supabase (solo si no es placeholder)
        url_supabase = None
        if error_message is None:
            url_supabase = subir_imagen_a_supabase(nombre_archivo, img_bytes)
        
        # Preparar respuesta
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
        
        print(f"🎉 Respuesta preparada: {nombre_archivo}")
        return response
        
    except Exception as e:
        print(f"💥 Error crítico generando imagen: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Error crítico en generación de imagen: {str(e)}"
        )

# =============================
# ENDPOINTS DE TRAZABILIDAD
# =============================

@app.post("/api/trazabilidad")
async def create_trazabilidad(
    user_id: str,
    used_model: str,
    prompt: str,
    language: str,
    output: str,
    execution_time: float
):
    try:
        data = {
            "user_id": user_id,
            "used_model": used_model,
            "prompt": prompt,
            "language": language,
            "output": output,
            "execution_time": execution_time
        }
        
        response = supabase.table('trazabilidad').insert(data).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/trazabilidad/{user_id}")
async def get_trazabilidad_by_user(user_id: str):
    try:
        response = supabase.table('trazabilidad').select('*').eq('user_id', user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/trazabilidad/{id}")
async def update_trazabilidad(
    id: str,
    used_model: str = None,
    prompt: str = None,
    language: str = None,
    output: str = None,
    execution_time: float = None
):
    try:
        updates = {}
        if used_model: updates["used_model"] = used_model
        if prompt: updates["prompt"] = prompt
        if language: updates["language"] = language
        if output: updates["output"] = output
        if execution_time: updates["execution_time"] = execution_time
        
        response = supabase.table('trazabilidad').update(updates).eq('id', id).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/trazabilidad/{id}")
async def delete_trazabilidad(id: str):
    try:
        response = supabase.table('trazabilidad').delete().eq('id', id).execute()
        return {"message": "Registro de trazabilidad eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================
# ENDPOINTS DE INFORMACIÓN
# =============================

@app.get("/")
def read_root():
    return {
        "message": "🤖 BUDDY API Unificada", 
        "version": "2.0.0",
        "status": "running",
        "architecture": "Servidor unificado",
        "services": {
            "nlp": "✅ Integrado",
            "images": "✅ Integrado", 
            "firebase": "✅" if db is not None else "❌ Deshabilitado",
            "supabase": "✅" if supabase else "❌"
        },
        "apis": {
            "groq": "✅" if os.getenv("GROQ_API_KEY") else "❌",
            "huggingface": "✅" if HUGGINGFACE_API_KEY else "❌",
            "alphavantage": "✅" if os.getenv("ALPHAVANTAGE_API_KEY") else "❌"
        },
        "endpoints": {
            "text": ["POST /generate", "POST /news-nlp"],
            "images": ["POST /generate-image"],
            "trazabilidad": ["POST /api/trazabilidad", "GET /api/trazabilidad/{user_id}"],
            "info": ["GET /", "GET /health"]
        }
    }

@app.get("/health")
def health_check():
    """Health check completo"""
    
    # Verificar APIs
    api_status = {}
    api_status["groq"] = "✅" if os.getenv("GROQ_API_KEY") else "❌"
    api_status["huggingface"] = "✅" if HUGGINGFACE_API_KEY else "❌" 
    api_status["alphavantage"] = "✅" if os.getenv("ALPHAVANTAGE_API_KEY") else "❌"
    
    # Verificar servicios
    service_status = {}
    service_status["firebase"] = "✅" if db is not None else "❌"
    service_status["supabase"] = "✅" if supabase else "❌"
    
    return {
        "status": "healthy", 
        "message": "🤖 BUDDY API Unificada funcionando correctamente",
        "timestamp": datetime.now().isoformat(),
        "apis": api_status,
        "services": service_status,
        "architecture": "unified_server",
        "cors": "configurado para localhost:3000"
    }


#@app.get("/stats")
#def get_stats():
#    """Estadísticas del sistema"""
#    try:
#        # Contar imágenes generadas
#        num_images = 0
#        if os.path.exists(IMAGENES_PATH):
#            num_images = len([f for f in os.listdir(IMAGENES_PATH) if f.endswith('.png')])
#        
#        return {
#            "images_generated": num_images,
#            "storage_path": IMAGENES_PATH,
#            "services_active": {
#                "nlp": True,
#                "images": True,
#                "firebase": db is not None,
#                "supabase": supabase is not None
#            }
#        }
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))
    
    
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Co...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# =============================
# ENDPOINT DE PRUEBA CORS
# =============================

@app.options("/generate")
async def options_generate():
    """Handle OPTIONS request for CORS preflight"""
    return {"message": "OK"}

