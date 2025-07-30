#!/usr/bin/env python3
"""
Qdrant Vector Store Integration
Cloud-based vector database for ArXiv articles
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Qdrant imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct, 
        Filter, FieldCondition, MatchValue, Range
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️ Qdrant client not installed. Install with: pip install qdrant-client")

# Embedding imports
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ SentenceTransformers not installed. Install with: pip install sentence-transformers")

logger = logging.getLogger(__name__)

class QdrantVectorStore:
    """Cloud-based vector storage using Qdrant"""
    
    def __init__(self, 
                 collection_name: str = "arxiv_articles",
                 qdrant_url: Optional[str] = None,
                 qdrant_api_key: Optional[str] = None,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 chunk_size: int = 512,
                 chunk_overlap: int = 50):
        """
        Initialize Qdrant vector store
        
        Args:
            collection_name: Name of the collection in Qdrant
            qdrant_url: Qdrant server URL (cloud or local)
            qdrant_api_key: Qdrant API key for cloud
            embedding_model: HuggingFace model name
            chunk_size: Text chunk size
            chunk_overlap: Overlap between chunks
        """
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents = []  # For compatibility with existing code
        
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant client not available. Install with: pip install qdrant-client")
        
        # Initialize Qdrant client
        if qdrant_url:
            if qdrant_api_key:
                # Cloud Qdrant
                self.client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key
                )
                logger.info(f"Connected to Qdrant cloud: {qdrant_url}")
            else:
                # Local Qdrant
                self.client = QdrantClient(url=qdrant_url)
                logger.info(f"Connected to local Qdrant: {qdrant_url}")
        else:
            # Local Qdrant with default settings
            self.client = QdrantClient("localhost", port=6333)
            logger.info("Connected to local Qdrant on localhost:6333")
        
        # Initialize embedding model
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("SentenceTransformers not available. Install with: pip install sentence-transformers")
        
        self.embedding_model = SentenceTransformer(embedding_model, use_auth_token=os.getenv("HUGGINGFACE_API_KEY"))
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Create collection if it doesn't exist
        self._create_collection()
        
        logger.info(f"Qdrant vector store initialized: {collection_name}")
    
    def _create_collection(self):
        """Create Qdrant collection with proper schema"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create new collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                
                # Create payload indexes for efficient filtering
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="arxiv_id",
                    field_schema="keyword"
                )
                
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="title",
                    field_schema="text"
                )
                
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="categories",
                    field_schema="keyword"
                )
                
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error creating Qdrant collection: {e}")
            raise
    
    def _fragment_text(self, text: str) -> List[str]:
        """Fragment text into chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        fragments = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                # Try to break at sentence boundaries
                break_chars = ['. ', '\n\n', '\n', ' ']
                best_break = end
                
                for char in break_chars:
                    pos = text.rfind(char, start, end)
                    if pos > start + self.chunk_size * 0.7:
                        best_break = pos + len(char)
                        break
                
                end = best_break
            
            fragment = text[start:end].strip()
            if fragment:
                fragments.append(fragment)
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return fragments
    
    def add_documents(self, documents: List[Dict]) -> Dict:
        """
        Add documents to Qdrant
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Processing result
        """
        logger.info(f"Adding {len(documents)} documents to Qdrant...")
        
        results = {
            'total_documents': len(documents),
            'processed': 0,
            'errors': 0,
            'errors_details': [],
            'fragments_created': 0,
            'points_added': 0
        }
        
        all_points = []
        
        for i, doc in enumerate(documents):
            try:
                logger.info(f"Processing document {i+1}/{len(documents)}: {doc.get('title', 'Unknown')}")
                
                # Store document for compatibility
                self.documents.append(doc)
                
                # Extract text content
                full_text = doc.get('full_text', '')
                if not full_text:
                    full_text = doc.get('abstract', '')
                
                # Fragment text
                fragments = self._fragment_text(full_text)
                results['fragments_created'] += len(fragments)
                
                # Create points for each fragment
                for j, fragment in enumerate(fragments):
                    # Generate embedding
                    embedding = self.embedding_model.encode(fragment).tolist()
                    
                    # Create point with valid UUID format
                    import uuid
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc.get('arxiv_id', 'unknown')}_{j}"))
                    
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            'arxiv_id': doc.get('arxiv_id', ''),
                            'title': doc.get('title', ''),
                            'authors': doc.get('authors', []),
                            'published_date': doc.get('published_date', ''),
                            'categories': doc.get('categories', []),
                            'pdf_url': doc.get('pdf_url', ''),
                            'browser_url': doc.get('browser_url', ''),
                            'fragment_text': fragment,
                            'fragment_index': j,
                            'total_fragments': len(fragments),
                            'text_length': len(fragment),
                            'source': 'arxiv',
                            'added_date': datetime.now().isoformat()
                        }
                    )
                    
                    all_points.append(point)
                
                results['processed'] += 1
                logger.info(f"Document processed: {len(fragments)} fragments")
                
            except Exception as e:
                error_msg = f"Error processing document {doc.get('arxiv_id', 'Unknown')}: {str(e)}"
                logger.error(error_msg)
                results['errors'] += 1
                results['errors_details'].append(error_msg)
        
        # Batch upload to Qdrant
        if all_points:
            try:
                batch_size = 100  # Qdrant recommended batch size
                for i in range(0, len(all_points), batch_size):
                    batch = all_points[i:i + batch_size]
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=batch
                    )
                    results['points_added'] += len(batch)
                
                logger.info(f"Successfully added {results['points_added']} points to Qdrant")
                
            except Exception as e:
                error_msg = f"Error uploading to Qdrant: {str(e)}"
                logger.error(error_msg)
                results['errors'] += 1
                results['errors_details'].append(error_msg)
        
        logger.info(f"Qdrant processing completed: {results['processed']} documents, {results['points_added']} points")
        return results
    
    def search(self, 
               query: str, 
               top_k: int = 5,
               min_score: float = 0.1,
               filter_categories: Optional[List[str]] = None) -> List[Dict]:
        """
        Search documents in Qdrant
        
        Args:
            query: Search query
            top_k: Number of results
            min_score: Minimum similarity score
            filter_categories: Filter by arXiv categories
            
        Returns:
            List of search results
        """
        logger.info(f"Searching Qdrant for: '{query}'")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Build filter
            search_filter = None
            if filter_categories:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="categories",
                            match=MatchValue(value=category)
                        ) for category in filter_categories
                    ]
                )
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k * 2,  # Get more results for filtering
                score_threshold=min_score
            )
            
            # Process results
            results = []
            for point in search_result:
                payload = point.payload
                
                result = {
                    'arxiv_id': payload.get('arxiv_id', ''),
                    'title': payload.get('title', ''),
                    'authors': payload.get('authors', []),
                    'published_date': payload.get('published_date', ''),
                    'categories': payload.get('categories', []),
                    'pdf_url': payload.get('pdf_url', ''),
                    'browser_url': payload.get('browser_url', ''),
                    'score': point.score,
                    'fragment_text': payload.get('fragment_text', ''),
                    'fragment_index': payload.get('fragment_index', 0),
                    'total_fragments': payload.get('total_fragments', 1),
                    'text_length': payload.get('text_length', 0),
                    'search_type': 'qdrant_vector'
                }
                
                results.append(result)
            
            # Sort by score and limit results
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            results = results[:top_k]
            
            logger.info(f"Qdrant search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get Qdrant collection statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                'collection_name': self.collection_name,
                'total_points': collection_info.points_count,
                'total_documents': len(self.documents),  # For compatibility
                'vector_size': collection_info.config.params.vectors.size,
                'distance_metric': str(collection_info.config.params.vectors.distance),
                'embedding_model': self.embedding_model.get_sentence_embedding_dimension(),
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'storage_type': 'qdrant_cloud' if hasattr(self.client, 'api_key') else 'qdrant_local'
            }
        except Exception as e:
            logger.error(f"Error getting Qdrant statistics: {e}")
            return {'error': str(e)}
    
    def clear(self):
        """Clear all data from Qdrant collection"""
        try:
            self.client.delete_collection(self.collection_name)
            self._create_collection()
            logger.info(f"Cleared Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing Qdrant collection: {e}")
    
    def delete_by_arxiv_id(self, arxiv_id: str):
        """Delete all fragments for a specific arXiv ID"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="arxiv_id",
                            match=MatchValue(value=arxiv_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted fragments for arXiv ID: {arxiv_id}")
        except Exception as e:
            logger.error(f"Error deleting by arXiv ID: {e}")

# Example usage and configuration
def create_qdrant_store(use_cloud: bool = False) -> QdrantVectorStore:
    """
    Create Qdrant vector store with configuration
    
    Args:
        use_cloud: Whether to use Qdrant cloud or local
        
    Returns:
        Configured QdrantVectorStore instance
    """
    if use_cloud:
        # Cloud configuration
        qdrant_url = os.getenv("QDRANT_URL", "https://your-cluster.qdrant.io")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if not qdrant_api_key:
            raise ValueError("QDRANT_API_KEY environment variable required for cloud usage")
        
        return QdrantVectorStore(
            collection_name="arxiv_articles_cloud",
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key
        )
    else:
        # Local configuration
        return QdrantVectorStore(
            collection_name="arxiv_articles_local"
        )

if __name__ == "__main__":
    # Example usage
    try:
        # Create local Qdrant store
        store = QdrantVectorStore()
        
        # Test statistics
        stats = store.get_statistics()
        print("Qdrant Statistics:", json.dumps(stats, indent=2))
        
    except Exception as e:
        print(f"Error: {e}") 