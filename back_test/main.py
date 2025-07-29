from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from openai import OpenAI
import time

# Загружаем переменные окружения
load_dotenv()

app = FastAPI(title="Simple RAG System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class SearchRequest(BaseModel):
    query: str
    max_results: int = 5

class RAGRequest(BaseModel):
    topic: str
    question: str
    max_results: int = 5

class RAGResponse(BaseModel):
    answer: str
    sources: List[Dict]
    confidence: float

# Инициализация моделей
print("🔄 Инициализация моделей...")

# Embedding модель
try:
    embedding_model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    print("✅ Embedding модель загружена")
except Exception as e:
    print(f"❌ Ошибка загрузки embedding модели: {e}")
    embedding_model = None

# LLM модель
llm_provider = os.getenv("LLM_PROVIDER", "openai")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if llm_provider == "openai":
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = OpenAI(api_key=openai_api_key)
        print(f"✅ OpenAI инициализирован: {openai_model}")
    else:
        print("❌ OPENAI_API_KEY не найден")
        openai_client = None
else:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        print("✅ Gemini инициализирован")
    else:
        print("❌ GEMINI_API_KEY не найден")
        gemini_model = None

# Хранилище документов
documents = []
document_embeddings = None

def search_arxiv(query: str, max_results: int = 5) -> List[Dict]:
    """Поиск статей в arXiv"""
    try:
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        articles = []
        
        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            try:
                title = entry.find(".//{http://www.w3.org/2005/Atom}title")
                title_text = title.text.strip() if title is not None and title.text else "No title"
                
                summary = entry.find(".//{http://www.w3.org/2005/Atom}summary")
                summary_text = summary.text.strip() if summary is not None and summary.text else "No summary"
                
                link = entry.find(".//{http://www.w3.org/2005/Atom}id")
                link_text = link.text if link is not None else ""
                
                authors = []
                for author in entry.findall(".//{http://www.w3.org/2005/Atom}author"):
                    name = author.find(".//{http://www.w3.org/2005/Atom}name")
                    if name is not None and name.text:
                        authors.append(name.text.strip())
                
                article = {
                    "title": title_text,
                    "summary": summary_text,
                    "link": link_text,
                    "authors": authors,
                    "content": f"Title: {title_text}\n\nSummary: {summary_text}"
                }
                articles.append(article)
                
            except Exception as e:
                print(f"Ошибка парсинга статьи: {e}")
                continue
                
        return articles
        
    except Exception as e:
        print(f"Ошибка поиска в arXiv: {e}")
        return []

def add_documents_to_rag(new_documents: List[Dict]):
    """Добавляет документы в RAG систему"""
    global documents, document_embeddings
    
    documents.extend(new_documents)
    
    if embedding_model and documents:
        # Создаем эмбеддинги для всех документов
        texts = [doc["content"] for doc in documents]
        document_embeddings = embedding_model.encode(texts)
        print(f"✅ Добавлено {len(new_documents)} документов. Всего: {len(documents)}")

def search_documents(query: str, top_k: int = 5) -> List[Dict]:
    """Поиск релевантных документов"""
    if not embedding_model or document_embeddings is None or not documents:
        return []
    
    # Создаем эмбеддинг для запроса
    query_embedding = embedding_model.encode([query])
    
    # Вычисляем косинусное сходство
    similarities = cosine_similarity(query_embedding, document_embeddings)[0]
    
    # Получаем топ-k документов
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.1:  # Минимальный порог релевантности
            results.append({
                "document": documents[idx],
                "similarity": float(similarities[idx])
            })
    
    return results

def generate_answer(question: str, context_docs: List[Dict]) -> str:
    """Генерирует ответ с помощью LLM"""
    if not context_docs:
        return "Извините, не удалось найти релевантную информацию для ответа на ваш вопрос."
    
    # Формируем контекст
    context = "\n\n".join([doc["document"]["content"] for doc in context_docs])
    
    # Промпт для LLM
    prompt = f"""Используя следующую информацию, ответьте на вопрос. Если информации недостаточно, скажите об этом.

Контекст:
{context}

Вопрос: {question}

Ответ:"""
    
    # Генерируем ответ
    try:
        if llm_provider == "openai" and openai_client:
            response = openai_client.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": "system", "content": "Вы - помощник, который отвечает на вопросы на основе предоставленной информации."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        
        elif llm_provider == "gemini" and gemini_model:
            response = gemini_model.generate_content(prompt)
            return response.text
        
        else:
            return "Ошибка: LLM модель не доступна"
            
    except Exception as e:
        print(f"Ошибка генерации ответа: {e}")
        return f"Ошибка при генерации ответа: {str(e)}"

# API endpoints
@app.get("/")
async def root():
    return {"message": "Simple RAG System работает!", "docs_count": len(documents)}

@app.post("/search-arxiv")
async def search_arxiv_endpoint(request: SearchRequest):
    """Поиск статей в arXiv"""
    articles = search_arxiv(request.query, request.max_results)
    return {"articles": articles, "count": len(articles)}

@app.post("/add-documents")
async def add_documents_endpoint(request: SearchRequest):
    """Добавляет статьи в RAG систему"""
    articles = search_arxiv(request.query, request.max_results)
    add_documents_to_rag(articles)
    return {"message": f"Добавлено {len(articles)} документов", "total_docs": len(documents)}

@app.post("/ask", response_model=RAGResponse)
async def ask_question_endpoint(request: RAGRequest):
    """Задает вопрос к RAG системе"""
    if not documents:
        raise HTTPException(status_code=400, detail="Нет документов в системе. Сначала добавьте документы.")
    
    # Ищем релевантные документы
    relevant_docs = search_documents(request.question, request.max_results)
    
    if not relevant_docs:
        return RAGResponse(
            answer="Извините, не удалось найти релевантную информацию для ответа на ваш вопрос.",
            sources=[],
            confidence=0.0
        )
    
    # Генерируем ответ
    answer = generate_answer(request.question, relevant_docs)
    
    # Подготавливаем источники
    sources = []
    total_confidence = 0
    for doc in relevant_docs:
        sources.append({
            "title": doc["document"]["title"],
            "authors": doc["document"]["authors"],
            "link": doc["document"]["link"],
            "similarity": doc["similarity"]
        })
        total_confidence += doc["similarity"]
    
    avg_confidence = total_confidence / len(relevant_docs) if relevant_docs else 0
    
    return RAGResponse(
        answer=answer,
        sources=sources,
        confidence=avg_confidence
    )

@app.get("/stats")
async def get_stats():
    """Статистика системы"""
    return {
        "total_documents": len(documents),
        "embedding_model": "BAAI/bge-large-en-v1.5" if embedding_model else "Не загружена",
        "llm_provider": llm_provider,
        "llm_model": openai_model if llm_provider == "openai" else "gemini-1.5-pro"
    }

@app.post("/clear")
async def clear_documents():
    """Очищает все документы"""
    global documents, document_embeddings
    documents = []
    document_embeddings = None
    return {"message": "Все документы очищены"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 