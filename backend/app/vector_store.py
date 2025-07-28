import os
import json
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from llama_index.core import Document, StorageContext, load_index_from_storage
from llama_index.core.indices.vector_store.base import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Условные импорты для API эмбеддингов
try:
    from llama_index.embeddings.groq import GroqEmbedding
except ImportError:
    GroqEmbedding = None

try:
    from llama_index.embeddings.cohere import CohereEmbedding
except ImportError:
    CohereEmbedding = None
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SentenceSplitter, HierarchicalNodeParser
from llama_index.core.schema import TextNode
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
import logging
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class EnhancedArxivVectorStore:
    """Enhanced vector storage with hybrid search and better semantic understanding"""
    
    def __init__(self, 
                 storage_path: str = "vector_store",
                 openai_api_key: Optional[str] = None,
                 groq_api_key: Optional[str] = None,
                 cohere_api_key: Optional[str] = None,
                 chunk_size: int = 512,  # Smaller chunks for better precision
                 chunk_overlap: int = 50,  # More overlap for context
                 embedding_model: str = "huggingface",  # "local", "openai", "groq", "cohere", "huggingface"
                 huggingface_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 enable_hybrid_search: bool = True):
        """
        Initialize enhanced vector storage
        
        Args:
            storage_path: Path for saving vector database
            openai_api_key: OpenAI API key
            groq_api_key: Groq API key
            cohere_api_key: Cohere API key
            chunk_size: Chunk size for text splitting
            chunk_overlap: Overlap between chunks
            embedding_model: Embedding model to use ("local", "openai", "groq", "cohere", "huggingface")
            huggingface_model: HuggingFace model name
            enable_hybrid_search: Enable hybrid search (vector + keyword)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.enable_hybrid_search = enable_hybrid_search
        self.embedding_model_name = embedding_model
        
        # Initialize embedding model
        self.embed_model = self._initialize_embedding_model(
            embedding_model, openai_api_key, groq_api_key, cohere_api_key, huggingface_model
        )
        
        # Use hierarchical node parser for better chunking
        self.node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=[chunk_size, chunk_size // 2],  # Multi-level chunking
            chunk_overlap=chunk_overlap
        )
        
        # Initialize TF-IDF for hybrid search
        if self.enable_hybrid_search:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=10000,
                ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
                stop_words='english',
                min_df=2,
                max_df=0.95
            )
            self.tfidf_matrix = None
            self.tfidf_documents = []
        
        # Load or create index
        self.index = self._load_or_create_index()
        
        logger.info(f"Enhanced vector storage initialized: {self.storage_path}")
    
    def _initialize_embedding_model(self, model_type: str, openai_key: str, groq_key: str, cohere_key: str, hf_model: str):
        """Initialize embedding model based on type"""
        
        if model_type == "openai" and openai_key:
            logger.info("Using OpenAI embeddings")
            os.environ["OPENAI_API_KEY"] = openai_key
            return OpenAIEmbedding()
            
        elif model_type == "groq" and groq_key and GroqEmbedding is not None:
            logger.info("Using Groq embeddings")
            os.environ["GROQ_API_KEY"] = groq_key
            return GroqEmbedding()
            
        elif model_type == "cohere" and cohere_key and CohereEmbedding is not None:
            logger.info("Using Cohere embeddings")
            os.environ["COHERE_API_KEY"] = cohere_key
            return CohereEmbedding()
            
        elif model_type == "huggingface":
            try:
                logger.info(f"Using HuggingFace embeddings: {hf_model}")
                # Используем более стабильную модель по умолчанию
                if not hf_model or hf_model == "BAAI/bge-small-en-v1.5":
                    hf_model = "sentence-transformers/all-MiniLM-L6-v2"
                
                return HuggingFaceEmbedding(
                    model_name=hf_model,
                    cache_folder="./huggingface_cache",
                    device="cpu"  # Принудительно использовать CPU для стабильности
                )
            except Exception as e:
                logger.warning(f"Failed to load HuggingFace model {hf_model}: {e}")
                logger.info("Falling back to local embeddings")
                return self._create_enhanced_embedding()
            
        else:
            # Fallback to local embeddings
            logger.info("Using enhanced local embeddings")
            return self._create_enhanced_embedding()
            
    def _create_enhanced_embedding(self):
        """Create enhanced local embedding model"""
            try:
                from llama_index.core.embeddings import BaseEmbedding
            except ImportError:
                from llama_index.embeddings.base import BaseEmbedding
            
        class EnhancedEmbedding(BaseEmbedding):
            dimension: int = 768  # Larger dimension for better representation
            
            def __init__(self):
                super().__init__()
                # Simple but more sophisticated embedding
                self._cache = {}
                # Pre-computed word vectors for common terms
                self._word_vectors = self._create_word_vectors()
            
            def _create_word_vectors(self):
                """Create simple word vectors for common terms"""
                vectors = {}
                
                # Common ML/AI terms
                ml_terms = [
                    'machine learning', 'neural network', 'deep learning', 
                    'artificial intelligence', 'algorithm', 'model', 'training',
                    'supervised', 'unsupervised', 'reinforcement', 'classification',
                    'regression', 'clustering', 'optimization', 'gradient', 'backpropagation'
                ]
                
                for i, term in enumerate(ml_terms):
                    # Create a simple but meaningful vector
                    vector = [0.0] * self.dimension
                    
                    # Set some dimensions based on term characteristics
                    vector[i % 100] = 0.8  # Primary feature
                    vector[(i + 50) % 100] = 0.4  # Secondary feature
                    vector[(i + 25) % 100] = 0.2  # Tertiary feature
                    
                    # Add some semantic similarity
                    if 'learning' in term:
                        vector[200] = 0.6
                    if 'neural' in term:
                        vector[201] = 0.6
                    if 'intelligence' in term:
                        vector[202] = 0.6
                    if 'algorithm' in term:
                        vector[203] = 0.6
                    
                    vectors[term.lower()] = vector
                
                return vectors
                
                def _get_text_embedding(self, text: str) -> List[float]:
                # Create more meaningful embeddings based on text content
                if text in self._cache:
                    return self._cache[text]
                
                # Start with base vector
                embedding = [0.0] * self.dimension
                
                # Convert to lowercase for matching
                text_lower = text.lower()
                
                # Check for exact matches with pre-computed vectors
                for term, vector in self._word_vectors.items():
                    if term in text_lower:
                        # Add the pre-computed vector
                        for i in range(min(len(vector), self.dimension)):
                            embedding[i] += vector[i] * 0.3
                
                # Character frequency features
                char_freq = defaultdict(int)
                for char in text_lower:
                    if char.isalpha():
                        char_freq[char] += 1
                
                # Word features
                words = text_lower.split()
                avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
                
                # Special pattern detection
                has_definition = int(re.search(r'\b(is|are|means|refers to|defined as)\b', text_lower) is not None)
                has_example = int(re.search(r'\b(for example|such as|e\.g\.|i\.e\.)\b', text_lower) is not None)
                has_formula = int(re.search(r'[=+\-*/^()\[\]]', text) is not None)
                has_numbers = int(re.search(r'\d+', text) is not None)
                
                # Fill embedding vector with meaningful features
                for i in range(min(300, self.dimension)):
                    if i < 26:  # First 26 dimensions for character frequency
                        char = chr(ord('a') + i)
                        embedding[i] += char_freq.get(char, 0) / max(len(text), 1) * 0.1
                    elif i < 50:  # Word features
                        embedding[i] += avg_word_length / 20.0 * 0.1
                    elif i < 54:  # Special patterns
                        patterns = [has_definition, has_example, has_formula, has_numbers]
                        embedding[i] += patterns[i - 50] * 0.2
                    elif i < 100:  # Content type features
                        if 'title' in text_lower:
                            embedding[i] += 0.3
                        if 'abstract' in text_lower:
                            embedding[i] += 0.2
                        if 'definition' in text_lower:
                            embedding[i] += 0.4
                    else:  # Semantic features based on content
                        if any(term in text_lower for term in ['machine learning', 'ml']):
                            embedding[i] += 0.3
                        if any(term in text_lower for term in ['neural network', 'nn']):
                            embedding[i] += 0.3
                        if any(term in text_lower for term in ['artificial intelligence', 'ai']):
                            embedding[i] += 0.3
                        if any(term in text_lower for term in ['deep learning']):
                            embedding[i] += 0.3
                
                # Normalize the embedding
                norm = sum(x*x for x in embedding) ** 0.5
                if norm > 0:
                    embedding = [x / norm for x in embedding]
                
                self._cache[text] = embedding
                return embedding
            
            def _get_query_embedding(self, query: str) -> List[float]:
                return self._get_text_embedding(query)
            
            async def _aget_text_embedding(self, text: str) -> List[float]:
                return self._get_text_embedding(text)
            
            async def _aget_query_embedding(self, query: str) -> List[float]:
                return self._get_text_embedding(query)
        
        return EnhancedEmbedding()
    
    def _load_or_create_index(self) -> VectorStoreIndex:
        """Loads existing index or creates new one"""
        try:
            if (self.storage_path / "docstore.json").exists():
                logger.info("Loading existing index...")
                storage_context = StorageContext.from_defaults(persist_dir=str(self.storage_path))
                index = load_index_from_storage(storage_context, embed_model=self.embed_model)
                
                # Rebuild TF-IDF matrix for existing index
                if self.enable_hybrid_search:
                    self._rebuild_tfidf_matrix(index)
                
                return index
            else:
                logger.info("Creating new index...")
                return VectorStoreIndex([], embed_model=self.embed_model)
        except Exception as e:
            logger.warning(f"Error loading index, creating new one: {e}")
            return VectorStoreIndex([], embed_model=self.embed_model)
    
    def _rebuild_tfidf_matrix(self, index):
        """Rebuild TF-IDF matrix from existing index"""
        try:
            logger.info("Rebuilding TF-IDF matrix from existing index...")
            
            # Extract all documents from index
            all_texts = []
            docstore = index.docstore
            
            for doc_id in docstore.docs:
                doc = docstore.docs[doc_id]
                if hasattr(doc, 'text'):
                    all_texts.append(doc.text)
            
            if all_texts:
                # Build TF-IDF matrix
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
                self.tfidf_documents = all_texts
                logger.info(f"TF-IDF matrix rebuilt with {len(all_texts)} documents")
            else:
                logger.warning("No documents found in index for TF-IDF rebuild")
                
        except Exception as e:
            logger.warning(f"Failed to rebuild TF-IDF matrix: {e}")
            self.tfidf_matrix = None
            self.tfidf_documents = []
    
    def _extract_definitions_and_key_concepts(self, text: str) -> List[str]:
        """Extract definitions and key concepts from text"""
        definitions = []
        
        # Pattern for definitions
        definition_patterns = [
            r'(\w+)\s+(?:is|are|means|refers to|defined as)\s+([^.]*)',
            r'(\w+)\s*[:=]\s*([^.]*)',
            r'(?:the|a|an)\s+(\w+)\s+(?:is|are)\s+([^.]*)',
            r'(\w+)\s+\(([^)]+)\)',  # Abbreviations
        ]
        
        for pattern in definition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                if len(term) > 2 and len(definition) > 10:  # Filter out short matches
                    definitions.append(f"{term}: {definition}")
        
        return definitions
    
    def _create_enhanced_document_from_article(self, article_data: Dict) -> Document:
        """Creates enhanced LlamaIndex document with better structure"""
        # Extract key information
        title = article_data.get('title', '')
        authors = article_data.get('authors', [])
        abstract = article_data.get('abstract', '')
        full_text = article_data.get('full_text', '')
        
        # Extract definitions and key concepts
        definitions = self._extract_definitions_and_key_concepts(full_text)
        
        # Create structured content
        content_parts = []
        
        # Title with high weight
        content_parts.append(f"TITLE: {title}")
        
        # Authors
        if authors:
            content_parts.append(f"AUTHORS: {', '.join(authors)}")
        
        # Abstract with high weight
        if abstract:
            content_parts.append(f"ABSTRACT: {abstract}")
        
        # Key definitions and concepts (high priority)
        if definitions:
            content_parts.append(f"KEY DEFINITIONS: {' | '.join(definitions[:10])}")  # Limit to top 10
        
        # Full text
        if full_text:
            content_parts.append(f"FULL TEXT: {full_text}")
        
        # Enhanced metadata
        metadata = {
            'arxiv_id': article_data.get('arxiv_id', ''),
            'title': title,
            'authors': authors,
            'published_date': article_data.get('published_date', ''),
            'categories': article_data.get('categories', []),
            'pdf_url': article_data.get('pdf_url', ''),
            'browser_url': article_data.get('browser_url', ''),
            'source': 'arxiv',
            'definitions_count': len(definitions),
            'has_definitions': len(definitions) > 0,
            'text_length': len(full_text),
            'abstract_length': len(abstract)
        }
        
        content = "\n\n".join(content_parts)
        
        return Document(
            text=content,
            metadata=metadata
        )
    
    def add_articles(self, articles: List[Dict]) -> Dict:
        """
        Adds articles to vector database with enhanced processing
        
        Args:
            articles: List of articles with full text
            
        Returns:
            Processing result
        """
        logger.info(f"Adding {len(articles)} articles to enhanced vector database...")
        
        results = {
            'total_articles': len(articles),
            'processed': 0,
            'errors': 0,
            'errors_details': [],
            'chunks_created': 0,
            'definitions_found': 0
        }
        
        all_texts = []  # For TF-IDF
        
        for i, article in enumerate(articles):
            try:
                logger.info(f"Processing article {i+1}/{len(articles)}: {article.get('title', 'Unknown')}")
                
                # Create enhanced document
                document = self._create_enhanced_document_from_article(article)
                
                # Count definitions
                definitions = self._extract_definitions_and_key_concepts(article.get('full_text', ''))
                results['definitions_found'] += len(definitions)
                
                # Split into hierarchical chunks
                nodes = self.node_parser.get_nodes_from_documents([document])
                results['chunks_created'] += len(nodes)
                
                # Add to index with enhanced processing
                for node in nodes:
                    # Preserve metadata
                    node.metadata = document.metadata
                    
                    # Set embedding
                    node.embedding = self.embed_model.get_text_embedding(node.text)
                    
                    # Add to index
                    self.index.insert_nodes([node])
                    
                    # Add to TF-IDF corpus
                    if self.enable_hybrid_search:
                        all_texts.append(node.text)
                
                results['processed'] += 1
                logger.info(f"Article added: {len(nodes)} chunks, {len(definitions)} definitions")
                
            except Exception as e:
                error_msg = f"Error processing article {article.get('arxiv_id', 'Unknown')}: {str(e)}"
                logger.error(error_msg)
                results['errors'] += 1
                results['errors_details'].append(error_msg)
        
        # Build TF-IDF matrix for hybrid search
        if self.enable_hybrid_search and all_texts:
            try:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
                self.tfidf_documents = all_texts
                logger.info(f"TF-IDF matrix built with {len(all_texts)} documents")
            except Exception as e:
                logger.warning(f"Failed to build TF-IDF matrix: {e}")
        
        # Save index
        self._save_index()
        
        logger.info(f"Processing completed: {results['processed']} articles, {results['chunks_created']} chunks, {results['definitions_found']} definitions")
        return results
    
    def _hybrid_search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """Perform hybrid search combining vector and keyword search"""
        if not self.enable_hybrid_search or self.tfidf_matrix is None:
            return []
        
        try:
            # Clean and limit query for TF-IDF
            clean_query = self._clean_query_for_tfidf(query)
            
            # TF-IDF search
            query_vector = self.tfidf_vectorizer.transform([clean_query])
            tfidf_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top TF-IDF results
            tfidf_indices = np.argsort(tfidf_scores)[::-1][:top_k * 3]  # Get more candidates
            
            # Combine with vector search scores
            hybrid_results = []
            for idx in tfidf_indices:
                if tfidf_scores[idx] > 0.01:  # Much lower minimum TF-IDF score
                    hybrid_results.append((idx, tfidf_scores[idx]))
            
            return hybrid_results[:top_k]
            
        except Exception as e:
            logger.warning(f"Hybrid search failed: {e}")
            return []
    
    def _clean_query_for_tfidf(self, query: str) -> str:
        """Clean query for TF-IDF processing"""
        # Remove extra spaces and limit length
        clean_query = ' '.join(query.split())
        
        # Limit to reasonable length for TF-IDF
        if len(clean_query) > 200:
            # Take first 200 characters and complete the last word
            clean_query = clean_query[:200]
            last_space = clean_query.rfind(' ')
            if last_space > 0:
                clean_query = clean_query[:last_space]
        
        return clean_query
    
    def _expand_query(self, query: str) -> str:
        """Expand query with related terms and synonyms"""
        # Limit expansion to avoid overly long queries
        if len(query) > 100:
            return query  # Don't expand already long queries
        
        # Simple query expansion
        expansions = {
            'definition': ['define', 'meaning', 'explanation', 'what is', 'refers to'],
            'example': ['instance', 'case', 'illustration', 'for example', 'such as'],
            'method': ['approach', 'technique', 'procedure', 'algorithm', 'methodology'],
            'result': ['outcome', 'finding', 'conclusion', 'result', 'effect'],
            'problem': ['issue', 'challenge', 'difficulty', 'limitation', 'drawback']
        }
        
        expanded_terms = [query]
        
        # Add related terms (limit to avoid too long queries)
        for category, terms in expansions.items():
            if any(term in query.lower() for term in terms):
                # Add only first 2 terms to avoid excessive expansion
                expanded_terms.extend(terms[:2])
                break  # Only expand for one category
        
        expanded = ' '.join(expanded_terms)
        
        # Limit total length
        if len(expanded) > 150:
            return query  # Return original if expanded is too long
        
        return expanded
    
    def search_articles(self, 
                       query: str, 
                       top_k: int = 5,
                       similarity_threshold: float = 0.1,  # Much lower threshold for better recall
                       use_hybrid_search: bool = True) -> List[Dict]:
        """
        Enhanced search with hybrid approach
        
        Args:
            query: Search query
            top_k: Number of results
            similarity_threshold: Similarity threshold
            use_hybrid_search: Use hybrid search
            
        Returns:
            List of found articles with relevance
        """
        logger.info(f"Enhanced search for query: '{query}'")
        
        try:
            # Query expansion for better semantic understanding
            expanded_query = self._expand_query(query)
            logger.info(f"Expanded query: '{expanded_query}'")
            
            # Vector search
            retriever = self.index.as_retriever(
                similarity_top_k=top_k * 3  # Get more candidates
            )
            
            vector_nodes = retriever.retrieve(expanded_query)
            logger.info(f"Vector search found {len(vector_nodes)} nodes")
            
            # Hybrid search if enabled
            hybrid_results = []
            if use_hybrid_search and self.enable_hybrid_search:
                try:
                    hybrid_indices = self._hybrid_search(query, top_k)
                    hybrid_results = [(self.tfidf_documents[idx], score) for idx, score in hybrid_indices]
                    logger.info(f"Hybrid search found {len(hybrid_results)} results")
                except Exception as e:
                    logger.warning(f"Hybrid search failed, continuing with vector search only: {e}")
                    hybrid_results = []
            
            # Combine and rank results
            combined_results = self._combine_search_results(vector_nodes, hybrid_results, top_k)
            logger.info(f"Combined results: {len(combined_results)}")
            
            # Process final results
            results = []
            for result in combined_results:
                if isinstance(result, dict):
                    # Vector search result
                    metadata = result.get('metadata', {})
                results.append({
                    'arxiv_id': metadata.get('arxiv_id', ''),
                    'title': metadata.get('title', ''),
                    'authors': metadata.get('authors', []),
                    'published_date': metadata.get('published_date', ''),
                    'categories': metadata.get('categories', []),
                    'pdf_url': metadata.get('pdf_url', ''),
                    'browser_url': metadata.get('browser_url', ''),
                        'score': result.get('score', 1.0),
                        'text_snippet': result.get('text', '')[:500] + "..." if len(result.get('text', '')) > 500 else result.get('text', ''),
                        'search_type': 'vector',
                        'has_definitions': metadata.get('has_definitions', False),
                        'definitions_count': metadata.get('definitions_count', 0)
                    })
                else:
                    # Hybrid search result
                    text, score = result
                    results.append({
                        'arxiv_id': '',
                        'title': '',
                        'authors': [],
                        'published_date': '',
                        'categories': [],
                        'pdf_url': '',
                        'browser_url': '',
                        'score': score,
                        'text_snippet': text[:500] + "..." if len(text) > 500 else text,
                        'search_type': 'hybrid',
                        'has_definitions': False,
                        'definitions_count': 0
                    })
            
            # Sort by score and filter by threshold
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            
            # Use very low threshold for filtering
            filtered_results = [r for r in results if r['score'] >= similarity_threshold]
            
            # If no results with threshold, return top results anyway
            if not filtered_results and results:
                logger.info(f"No results above threshold {similarity_threshold}, returning top {top_k} results")
                filtered_results = results[:top_k]
            
            logger.info(f"Found {len(filtered_results)} relevant fragments after filtering")
            return filtered_results[:top_k]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            # Return empty results instead of failing completely
            return []
    
    def _combine_search_results(self, vector_results: List, hybrid_results: List, top_k: int) -> List:
        """Combine and rank search results from different methods"""
        combined = []
        
        # Add vector results
        for node in vector_results:
            combined.append({
                'metadata': node.metadata,
                'text': node.text,
                'score': node.score if hasattr(node, 'score') else 1.0
            })
        
        # Add hybrid results with adjusted scoring
        for text, score in hybrid_results:
            combined.append((text, score * 0.8))  # Slightly lower weight for hybrid
        
        # Sort by score and return top results
        combined.sort(key=lambda x: x[1] if isinstance(x, tuple) else x['score'], reverse=True)
        return combined[:top_k]
    
    def _save_index(self):
        """Saves index to disk"""
        try:
            self.index.storage_context.persist(persist_dir=str(self.storage_path))
            logger.info("Index saved to disk")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def get_statistics(self) -> Dict:
        """Returns enhanced vector database statistics"""
        try:
            # Count documents
            docstore = self.index.docstore
            num_docs = len(docstore.docs)
            
            # Calculate storage size
            storage_size = sum(
                f.stat().st_size for f in self.storage_path.rglob('*') if f.is_file()
            )
            
            return {
                'total_documents': num_docs,
                'storage_size_mb': round(storage_size / (1024 * 1024), 2),
                'storage_path': str(self.storage_path),
                'embedding_model': self.embedding_model_name,
                'chunk_size': '512/256',  # Hierarchical chunking
                'chunk_overlap': 50,
                'hybrid_search_enabled': self.enable_hybrid_search,
                'tfidf_documents': len(self.tfidf_documents) if self.tfidf_documents else 0
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'error': str(e)}
    
    def clear_index(self):
        """Clears vector database"""
        try:
            import shutil
            shutil.rmtree(self.storage_path)
            self.storage_path.mkdir(exist_ok=True)
            self.index = VectorStoreIndex([], embed_model=self.embed_model)
            self.tfidf_matrix = None
            self.tfidf_documents = []
            logger.info("Vector database cleared")
        except Exception as e:
            logger.error(f"Error clearing index: {e}")


# Backward compatibility
class ArxivVectorStore(EnhancedArxivVectorStore):
    """Backward compatibility wrapper"""
    pass 