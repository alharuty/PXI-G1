import os
import json
from typing import List, Dict, Optional
from pathlib import Path
from llama_index.core import Document, StorageContext, load_index_from_storage
from llama_index.core.indices.vector_store.base import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
import logging

logger = logging.getLogger(__name__)

class ArxivVectorStore:
    """Класс для работы с векторной базой данных статей из arXiv"""
    
    def __init__(self, 
                 storage_path: str = "vector_store",
                 openai_api_key: Optional[str] = None,
                 chunk_size: int = 1024,
                 chunk_overlap: int = 20,
                 use_local_embeddings: bool = True):
        """
        Инициализация векторного хранилища
        
        Args:
            storage_path: Путь для сохранения векторной базы
            openai_api_key: API ключ OpenAI (если не указан, берется из env)
            chunk_size: Размер чанка для разбиения текста
            chunk_overlap: Перекрытие между чанками
            use_local_embeddings: Использовать локальные эмбеддинги (по умолчанию True)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Инициализация компонентов LlamaIndex
        if openai_api_key and not use_local_embeddings:
            # Настройка OpenAI
            os.environ["OPENAI_API_KEY"] = openai_api_key
            self.embed_model = OpenAIEmbedding()
            self.llm = OpenAI(model="gpt-3.5-turbo")
            logger.info("Используем OpenAI эмбеддинги")
        else:
            # Используем простые эмбеддинги для тестирования
            logger.info("Используем простые эмбеддинги для тестирования")
            
            # Создаем простой класс эмбеддингов
            try:
                from llama_index.core.embeddings import BaseEmbedding
            except ImportError:
                from llama_index.embeddings.base import BaseEmbedding
            
            class SimpleEmbedding(BaseEmbedding):
                dimension: int = 384
                
                def _get_text_embedding(self, text: str) -> List[float]:
                    # Простая реализация для тестирования
                    return [0.1] * self.dimension
                
                def _get_query_embedding(self, query: str) -> List[float]:
                    return [0.1] * self.dimension
                
                async def _aget_text_embedding(self, text: str) -> List[float]:
                    # Асинхронная версия
                    return [0.1] * self.dimension
                
                async def _aget_query_embedding(self, query: str) -> List[float]:
                    # Асинхронная версия
                    return [0.1] * self.dimension
            
            self.embed_model = SimpleEmbedding()
            self.llm = None  # LLM не нужен для создания эмбеддингов
        
        self.node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Загрузка или создание индекса
        self.index = self._load_or_create_index()
        
        logger.info(f"Векторное хранилище инициализировано: {self.storage_path}")
    
    def _load_or_create_index(self) -> VectorStoreIndex:
        """Загружает существующий индекс или создает новый"""
        try:
            if (self.storage_path / "docstore.json").exists():
                logger.info("Загружаем существующий индекс...")
                storage_context = StorageContext.from_defaults(persist_dir=str(self.storage_path))
                return load_index_from_storage(storage_context, embed_model=self.embed_model)
            else:
                logger.info("Создаем новый индекс...")
                return VectorStoreIndex([], embed_model=self.embed_model)
        except Exception as e:
            logger.warning(f"Ошибка загрузки индекса, создаем новый: {e}")
            return VectorStoreIndex([], embed_model=self.embed_model)
    
    def _create_document_from_article(self, article_data: Dict) -> Document:
        """Создает документ LlamaIndex из данных статьи"""
        # Формируем полный текст статьи
        content_parts = []
        
        # Заголовок
        content_parts.append(f"Title: {article_data.get('title', '')}")
        
        # Авторы
        authors = article_data.get('authors', [])
        if authors:
            content_parts.append(f"Authors: {', '.join(authors)}")
        
        # Аннотация
        abstract = article_data.get('abstract', '')
        if abstract:
            content_parts.append(f"Abstract: {abstract}")
        
        # Полный текст
        full_text = article_data.get('full_text', '')
        if full_text:
            content_parts.append(f"Full Text: {full_text}")
        
        # Метаданные
        metadata = {
            'arxiv_id': article_data.get('arxiv_id', ''),
            'title': article_data.get('title', ''),
            'authors': authors,
            'published_date': article_data.get('published_date', ''),
            'categories': article_data.get('categories', []),
            'pdf_url': article_data.get('pdf_url', ''),
            'browser_url': article_data.get('browser_url', ''),
            'source': 'arxiv'
        }
        
        content = "\n\n".join(content_parts)
        
        return Document(
            text=content,
            metadata=metadata
        )
    
    def add_articles(self, articles: List[Dict]) -> Dict:
        """
        Добавляет статьи в векторную базу данных
        
        Args:
            articles: Список статей с полным текстом
            
        Returns:
            Результат обработки
        """
        logger.info(f"Добавляем {len(articles)} статей в векторную базу...")
        
        results = {
            'total_articles': len(articles),
            'processed': 0,
            'errors': 0,
            'errors_details': [],
            'chunks_created': 0
        }
        
        for i, article in enumerate(articles):
            try:
                logger.info(f"Обрабатываем статью {i+1}/{len(articles)}: {article.get('title', 'Unknown')}")
                
                # Создаем документ
                document = self._create_document_from_article(article)
                logger.info(f"Создан документ с метаданными: {document.metadata}")
                
                # Разбиваем на чанки
                nodes = self.node_parser.get_nodes_from_documents([document])
                results['chunks_created'] += len(nodes)
                
                # Добавляем в индекс
                for node in nodes:
                    # Убеждаемся, что метаданные сохраняются в узле
                    node.metadata = document.metadata
                    # Устанавливаем эмбеддинг для узла
                    node.embedding = self.embed_model.get_text_embedding(node.text)
                    self.index.insert_nodes([node])
                
                results['processed'] += 1
                logger.info(f"Статья добавлена: {len(nodes)} чанков")
                
            except Exception as e:
                error_msg = f"Ошибка обработки статьи {article.get('arxiv_id', 'Unknown')}: {str(e)}"
                logger.error(error_msg)
                results['errors'] += 1
                results['errors_details'].append(error_msg)
        
        # Сохраняем индекс
        self._save_index()
        
        logger.info(f"Обработка завершена: {results['processed']} статей, {results['chunks_created']} чанков")
        return results
    
    def _save_index(self):
        """Сохраняет индекс на диск"""
        try:
            self.index.storage_context.persist(persist_dir=str(self.storage_path))
            logger.info("Индекс сохранен на диск")
        except Exception as e:
            logger.error(f"Ошибка сохранения индекса: {e}")
    
    def search_articles(self, 
                       query: str, 
                       top_k: int = 5,
                       similarity_threshold: float = 0.7) -> List[Dict]:
        """
        Поиск статей по запросу
        
        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            similarity_threshold: Порог схожести
            
        Returns:
            Список найденных статей с релевантностью
        """
        logger.info(f"Поиск по запросу: '{query}'")
        
        try:
            # Используем retriever вместо query_engine (без LLM)
            retriever = self.index.as_retriever(
                similarity_top_k=top_k
            )
            
            # Выполняем поиск
            nodes = retriever.retrieve(query)
            
            # Обрабатываем результаты
            results = []
            for node in nodes:
                metadata = node.metadata
                logger.info(f"Найден узел: {metadata.get('title', 'Unknown')} - {metadata.get('arxiv_id', 'Unknown')}")
                results.append({
                    'arxiv_id': metadata.get('arxiv_id', ''),
                    'title': metadata.get('title', ''),
                    'authors': metadata.get('authors', []),
                    'published_date': metadata.get('published_date', ''),
                    'categories': metadata.get('categories', []),
                    'pdf_url': metadata.get('pdf_url', ''),
                    'browser_url': metadata.get('browser_url', ''),
                    'score': node.score if hasattr(node, 'score') else 1.0,
                    'text_snippet': node.text[:500] + "..." if len(node.text) > 500 else node.text
                })
            
            logger.info(f"Найдено {len(results)} релевантных фрагментов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Возвращает статистику векторной базы"""
        try:
            # Подсчитываем количество документов
            docstore = self.index.docstore
            num_docs = len(docstore.docs)
            
            # Подсчитываем размер хранилища
            storage_size = sum(
                f.stat().st_size for f in self.storage_path.rglob('*') if f.is_file()
            )
            
            return {
                'total_documents': num_docs,
                'storage_size_mb': round(storage_size / (1024 * 1024), 2),
                'storage_path': str(self.storage_path),
                'embedding_model': 'SimpleEmbedding',
                'chunk_size': self.node_parser.chunk_size,
                'chunk_overlap': self.node_parser.chunk_overlap
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {'error': str(e)}
    
    def clear_index(self):
        """Очищает векторную базу данных"""
        try:
            import shutil
            shutil.rmtree(self.storage_path)
            self.storage_path.mkdir(exist_ok=True)
            self.index = VectorStoreIndex([], embed_model=self.embed_model)
            logger.info("Векторная база данных очищена")
        except Exception as e:
            logger.error(f"Ошибка очистки индекса: {e}")


# Пример использования
if __name__ == "__main__":
    # Тестирование
    vector_store = ArxivVectorStore(use_local_embeddings=True)
    print("Векторное хранилище создано успешно!") 