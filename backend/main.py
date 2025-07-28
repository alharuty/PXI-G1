from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from typing import List, Dict
from app.models import (
    GenerationRequest, 
    GenerationResponse, 
    ArxivSearchResponse
)
from app.agents import generate_content
from app.arXiv import ArxivExtractor
from app.huggingface_embedding import SimpleHuggingFaceStore
from app.rag_generator import RAGGenerator
from dotenv import load_dotenv
import os
import logging
import re

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 FastAPI application starting...")
    print("📚 Available endpoints:")
    print("   - POST /generate - content generation")
    print("   - POST /arxiv/search - article search (POST)")
    print("   - GET /arxiv/search - article search (GET)")
    print("   - POST /rag/generate - RAG generation with Groq")
    print("   - GET /rag/compare - Compare RAG vs simple generation")
    print("📖 Swagger documentation: http://localhost:8001/docs")
    print("✅ Application ready to work!")
    
    yield
    
    # Shutdown
    print("🛑 Application stopping...")

app = FastAPI(title="AI Content Generator", lifespan=lifespan)
# Vector database (simple solution without LlamaIndex with fragmentation)
vector_store = SimpleHuggingFaceStore(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    chunk_size=512,  # Fragment size
    chunk_overlap=50  # Overlap between fragments
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


    
@app.post("/generate", response_model=GenerationResponse)
def generate(req: GenerationRequest, provider: str = Query("groq", enum=["groq", "ollama"])):
    try:
        content = generate_content(req.platform, req.topic, provider=provider)
        return GenerationResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# POST endpoint removed - using GET only for simplicity

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
    Returns vector database statistics
    
    Returns:
        Vector database statistics
    """
    print("📊 Getting vector database statistics...")
    
    try:
        stats = vector_store.get_statistics()
        print(f"✅ Statistics received: {stats.get('total_documents', 0)} documents")
        return stats
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

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Content Generator API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
