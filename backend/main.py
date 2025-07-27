from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from typing import List, Dict
from app.models import (
    GenerationRequest, 
    GenerationResponse, 
    ArxivSearchRequest, 
    ArxivSearchResponse
)
from app.agents import generate_content
from app.arXiv import ArxivExtractor
from app.vector_store import ArxivVectorStore
from dotenv import load_dotenv
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 FastAPI приложение запускается...")
    print("📚 Доступные эндпоинты:")
    print("   - POST /generate - генерация контента")
    print("   - POST /arxiv/search - поиск статей (POST)")
    print("   - GET /arxiv/search - поиск статей (GET)")
    print("📖 Swagger документация: http://localhost:8001/docs")
    print("✅ Приложение готово к работе!")
    
    yield
    
    # Shutdown
    print("🛑 Приложение останавливается...")

app = FastAPI(title="AI Content Generator", lifespan=lifespan)

@app.post("/generate", response_model=GenerationResponse)
def generate(req: GenerationRequest, provider: str = Query("groq", enum=["groq", "ollama"])):
    try:
        content = generate_content(req.platform, req.topic, provider=provider)
        return GenerationResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/arxiv/search", response_model=ArxivSearchResponse)
def search_arxiv_papers(req: ArxivSearchRequest):
    """
    Поиск научных статей в arXiv по заданной теме
    
    Args:
        req: Запрос с параметрами поиска
        
    Returns:
        Список найденных статей с метаданными
    """
    print(f"🔍 POST запрос на поиск статей: тема='{req.topic}', количество={req.max_results}")
    
    try:
        # Создаем экстрактор arXiv
        extractor = ArxivExtractor()
        
        # Выполняем поиск
        results = extractor.search_and_download(
            topic=req.topic,
            max_results=req.max_results,
            download_pdfs=req.download_pdfs,
            extract_text=req.extract_text,
            output_dir="arxiv_papers"
        )
        
        print(f"✅ Найдено {results['total_found']} статей по теме '{req.topic}'")
        return ArxivSearchResponse(**results)
        
    except Exception as e:
        print(f"❌ Ошибка при поиске статей: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске статей: {str(e)}")

@app.get("/arxiv/search")
def search_arxiv_papers_get(
    topic: str = Query(..., description="Тема для поиска статей"),
    max_results: int = Query(5, ge=1, le=50, description="Максимальное количество результатов"),
    download_pdfs: bool = Query(False, description="Скачивать ли PDF файлы"),
    extract_text: bool = Query(False, description="Извлекать ли полный текст из PDF"),
    days_back: int = Query(365, ge=1, le=3650, description="Количество дней назад для поиска"),
    categories: str = Query(None, description="Категории arXiv через запятую (например: cs.AI,quant-ph)")
):
    """
    GET эндпоинт для поиска научных статей в arXiv
    
    Args:
        topic: Тема для поиска
        max_results: Максимальное количество результатов (1-50)
        download_pdfs: Скачивать ли PDF файлы
        extract_text: Извлекать ли полный текст из PDF
        days_back: Количество дней назад для поиска
        categories: Категории arXiv через запятую
        
    Returns:
        Список найденных статей с метаданными
    """
    print(f"🔍 GET запрос на поиск статей: тема='{topic}', количество={max_results}")
    
    try:
        # Парсим категории если указаны
        category_list = None
        if categories:
            category_list = [cat.strip() for cat in categories.split(",")]
            print(f"📂 Фильтр по категориям: {category_list}")
        
        # Создаем экстрактор arXiv
        extractor = ArxivExtractor()
        
        # Выполняем поиск
        results = extractor.search_and_download(
            topic=topic,
            max_results=max_results,
            download_pdfs=download_pdfs,
            extract_text=extract_text,
            output_dir="arxiv_papers"
        )
        
        print(f"✅ Найдено {results['total_found']} статей по теме '{topic}'")
        return results
        
    except Exception as e:
        print(f"❌ Ошибка при поиске статей: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске статей: {str(e)}")

@app.get("/")
def root():
    """Корневой эндпоинт для проверки статуса сервера"""
    return {
        "message": "AI Content Generator API работает!",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate",
            "arxiv_search_post": "/arxiv/search (POST)",
            "arxiv_search_get": "/arxiv/search (GET)",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
def health_check():
    """Проверка здоровья сервера"""
    return {"status": "healthy", "message": "Сервер работает нормально"}

# Векторная база данных
vector_store = ArxivVectorStore(use_local_embeddings=True)

@app.post("/vector/add_articles")
def add_articles_to_vector_store(articles: List[Dict]):
    """
    Добавляет статьи в векторную базу данных
    
    Args:
        articles: Список статей с полным текстом
        
    Returns:
        Результат обработки
    """
    print(f"🔍 Добавляем {len(articles)} статей в векторную базу...")
    
    try:
        # Очищаем и валидируем данные
        cleaned_articles = []
        for article in articles:
            cleaned_article = {}
            for key, value in article.items():
                if isinstance(value, str):
                    # Ограничиваем размер текста и очищаем специальные символы
                    if key == 'full_text':
                        cleaned_article[key] = value[:50000]  # Ограничиваем до 50KB
                    else:
                        cleaned_article[key] = value[:1000]   # Ограничиваем остальные поля
                else:
                    cleaned_article[key] = value
            cleaned_articles.append(cleaned_article)
        
        results = vector_store.add_articles(cleaned_articles)
        print(f"✅ Обработано {results['processed']} статей, создано {results['chunks_created']} чанков")
        return results
    except Exception as e:
        print(f"❌ Ошибка добавления статей: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка добавления статей: {str(e)}")

@app.get("/vector/search")
def search_vector_store(
    query: str = Query(..., description="Поисковый запрос"),
    top_k: int = Query(5, ge=1, le=20, description="Количество результатов"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Порог схожести")
):
    """
    Поиск статей в векторной базе данных
    
    Args:
        query: Поисковый запрос
        top_k: Количество результатов
        similarity_threshold: Порог схожести
        
    Returns:
        Список найденных статей с релевантностью
    """
    print(f"🔍 Поиск в векторной базе: '{query}'")
    
    try:
        results = vector_store.search_articles(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        print(f"✅ Найдено {len(results)} релевантных фрагментов")
        return {
            "query": query,
            "total_found": len(results),
            "results": results
        }
    except Exception as e:
        print(f"❌ Ошибка поиска: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {str(e)}")

@app.get("/vector/statistics")
def get_vector_store_statistics():
    """
    Возвращает статистику векторной базы данных
    
    Returns:
        Статистика векторной базы
    """
    print("📊 Получение статистики векторной базы...")
    
    try:
        stats = vector_store.get_statistics()
        print(f"✅ Статистика получена: {stats.get('total_documents', 0)} документов")
        return stats
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@app.delete("/vector/clear")
def clear_vector_store():
    """
    Очищает векторную базу данных
    
    Returns:
        Результат очистки
    """
    print("🗑️ Очистка векторной базы данных...")
    
    try:
        vector_store.clear_index()
        print("✅ Векторная база данных очищена")
        return {"message": "Векторная база данных очищена", "status": "success"}
    except Exception as e:
        print(f"❌ Ошибка очистки: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки: {str(e)}")

@app.post("/arxiv/search_and_vectorize")
def search_and_vectorize(
    topic: str = Query(..., description="Тема для поиска статей"),
    max_results: int = Query(5, ge=1, le=20, description="Максимальное количество результатов"),
    download_pdfs: bool = Query(True, description="Скачивать ли PDF файлы"),
    extract_text: bool = Query(True, description="Извлекать ли полный текст из PDF"),
    add_to_vector_store: bool = Query(True, description="Добавлять ли статьи в векторную базу")
):
    """
    Комбинированный эндпоинт: поиск статей и добавление в векторную базу
    
    Args:
        topic: Тема для поиска
        max_results: Количество результатов
        download_pdfs: Скачивать PDF
        extract_text: Извлекать текст
        add_to_vector_store: Добавлять в векторную базу
        
    Returns:
        Результаты поиска и обработки
    """
    print(f"🔍 Комбинированный поиск и векторизация: '{topic}'")
    
    try:
        # Поиск статей
        extractor = ArxivExtractor()
        search_results = extractor.search_and_download(
            topic=topic,
            max_results=max_results,
            download_pdfs=download_pdfs,
            extract_text=extract_text,
            output_dir="arxiv_papers"
        )
        
        vector_results = None
        if add_to_vector_store and search_results['documents']:
            # Очищаем данные перед добавлением в векторную базу
            cleaned_documents = []
            for doc in search_results['documents']:
                cleaned_doc = {}
                for key, value in doc.items():
                    if isinstance(value, str):
                        if key == 'full_text':
                            cleaned_doc[key] = value[:50000]  # Ограничиваем до 50KB
                        else:
                            cleaned_doc[key] = value[:1000]   # Ограничиваем остальные поля
                    else:
                        cleaned_doc[key] = value
                cleaned_documents.append(cleaned_doc)
            
            # Добавление в векторную базу
            vector_results = vector_store.add_articles(cleaned_documents)
        
        return {
            "search_results": search_results,
            "vector_results": vector_results,
            "topic": topic,
            "total_articles_found": search_results['total_found']
        }
        
    except Exception as e:
        print(f"❌ Ошибка комбинированной обработки: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Запускаем AI Content Generator API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
