#!/usr/bin/env python3
"""
Simple HuggingFace embedding without LlamaIndex (enhanced with fragmentation)
"""

import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleHuggingFaceStore:
    """Simple storage with HuggingFace embeddings (enhanced ranking with fragmentation)"""
    
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2", cache_dir="./huggingface_cache", 
                 chunk_size=512, chunk_overlap=50):
        """Initialize storage"""
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents = []  # Original documents
        self.fragments = []  # Document fragments
        self.embeddings = []  # Fragment embeddings
        self.tfidf_vectorizer = TfidfVectorizer(max_features=2000, stop_words='english', ngram_range=(1, 2))
        self.tfidf_matrix = None
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load model
        logger.info(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name, cache_folder=cache_dir, use_auth_token=os.getenv("HUGGINGFACE_API_KEY"))
        logger.info("Model loaded successfully")
    
    def _fragment_text(self, text, chunk_size=None, chunk_overlap=None):
        """Fragments text into chunks"""
        if chunk_size is None:
            chunk_size = self.chunk_size
        if chunk_overlap is None:
            chunk_overlap = self.chunk_overlap
            
        if len(text) <= chunk_size:
            return [text]
        
        fragments = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this is not the last fragment, find a good break point
            if end < len(text):
                # Find the nearest sentence or paragraph end
                break_chars = ['. ', '\n\n', '\n', ' ']
                best_break = end
                
                for char in break_chars:
                    pos = text.rfind(char, start, end)
                    if pos > start + chunk_size * 0.7:  # Don't break too early
                        best_break = pos + len(char)
                        break
                
                end = best_break
            
            fragment = text[start:end].strip()
            if fragment:
                fragments.append(fragment)
            
            # Next fragment with overlap
            start = end - chunk_overlap
            if start >= len(text):
                break
        
        return fragments
    
    def add_documents(self, documents):
        """Adds documents to storage with fragmentation"""
        logger.info(f"Adding {len(documents)} documents")
        
        original_count = len(self.documents)
        
        for doc in documents:
            # Save original document
            self.documents.append(doc)
            
            # Extract text
            text = self._extract_text(doc)
            if not text:
                continue
            
            # Fragment text
            fragments = self._fragment_text(text)
            logger.info(f"Document '{doc.get('title', 'Unknown')}' split into {len(fragments)} fragments")
            
            # Create fragments with metadata
            for i, fragment in enumerate(fragments):
                fragment_doc = {
                    'original_doc_index': len(self.documents) - 1,
                    'fragment_index': i,
                    'fragment_text': fragment,
                    'title': doc.get('title', ''),
                    'authors': doc.get('authors', []),
                    'arxiv_id': doc.get('arxiv_id', ''),
                    'published_date': doc.get('published_date', ''),
                    'categories': doc.get('categories', []),
                    'fragment_length': len(fragment),
                    'total_fragments': len(fragments)
                }
                
                self.fragments.append(fragment_doc)
                
                # Generate embedding for fragment
                embedding = self.model.encode(fragment, convert_to_tensor=False)
                self.embeddings.append(embedding)
        
        # Update TF-IDF based on fragments
        if self.fragments:
            fragment_texts = [frag['fragment_text'] for frag in self.fragments]
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(fragment_texts)
        
        added_fragments = len(self.fragments) - (original_count * self.chunk_size // self.chunk_size)
        logger.info(f"Added {len(self.documents)} documents, {len(self.fragments)} fragments")
        return len(self.documents)
    
    def search(self, query, top_k=5, use_hybrid=True, min_score=0.1):
        """Search document fragments with enhanced ranking"""
        logger.info(f"Search: '{query}'")
        
        if not self.fragments:
            logger.warning("No fragments to search")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode(query, convert_to_tensor=False)
        
        results = []
        
        if use_hybrid and self.tfidf_matrix is not None:
            # Hybrid search (embeddings + TF-IDF)
            results = self._hybrid_search(query, query_embedding, top_k, min_score)
        else:
            # Only embeddings
            results = self._vector_search(query_embedding, top_k, min_score)
        
        logger.info(f"Found {len(results)} results")
        return results
    
    def _extract_text(self, doc):
        """Extracts text from document"""
        if isinstance(doc, dict):
            # Priority: full_text > abstract > title
            text = doc.get('full_text', '')
            if not text:
                text = doc.get('abstract', '')
            if not text:
                text = doc.get('title', '')
            return text
        elif isinstance(doc, str):
            return doc
        else:
            return str(doc)
    
    def _vector_search(self, query_embedding, top_k, min_score):
        """Enhanced search by fragment embeddings"""
        similarities = []
        
        for i, embedding in enumerate(self.embeddings):
            # Normalize embeddings for better comparison
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            doc_norm = embedding / np.linalg.norm(embedding)
            
            # Cosine similarity
            similarity = np.dot(query_norm, doc_norm)
            
            # Enhance score with additional metrics
            enhanced_score = self._enhance_similarity_score(similarity, query_embedding, embedding, i)
            
            similarities.append((i, enhanced_score))
        
        # Sort by enhanced score
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for i, (frag_idx, score) in enumerate(similarities[:top_k * 2]):  # Take more candidates
            if score >= min_score:  # Filter by minimum score
                fragment = self.fragments[frag_idx].copy()
                fragment['score'] = float(score)
                fragment['rank'] = i + 1
                
                # Add original document information
                if fragment['original_doc_index'] < len(self.documents):
                    original_doc = self.documents[fragment['original_doc_index']]
                    fragment['original_title'] = original_doc.get('title', '')
                    fragment['original_authors'] = original_doc.get('authors', [])
                    fragment['original_arxiv_id'] = original_doc.get('arxiv_id', '')
                
                results.append(fragment)
        
        return results[:top_k]  # Return only top_k
    
    def _hybrid_search(self, query, query_embedding, top_k, min_score):
        """Enhanced hybrid search by fragments"""
        # TF-IDF search with enhanced parameters
        query_tfidf = self.tfidf_vectorizer.transform([query])
        tfidf_scores = cosine_similarity(query_tfidf, self.tfidf_matrix).flatten()
        
        # Embedding search
        vector_scores = []
        for embedding in self.embeddings:
            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            doc_norm = embedding / np.linalg.norm(embedding)
            similarity = np.dot(query_norm, doc_norm)
            vector_scores.append(similarity)
        
        # Combine results with enhanced weights
        combined_scores = []
        for i in range(len(self.fragments)):
            # Normalize scores
            tfidf_score = tfidf_scores[i] if i < len(tfidf_scores) else 0
            vector_score = vector_scores[i] if i < len(vector_scores) else 0
            
            # Enhanced combination with dynamic weights
            if tfidf_score > 0.5:  # If TF-IDF found good matches
                combined_score = 0.4 * tfidf_score + 0.6 * vector_score
            else:
                combined_score = 0.2 * tfidf_score + 0.8 * vector_score
            
            # Additional score enhancement
            enhanced_score = self._enhance_similarity_score(combined_score, query_embedding, self.embeddings[i], i)
            
            combined_scores.append((i, enhanced_score))
        
        # Sort by enhanced score
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for i, (frag_idx, score) in enumerate(combined_scores[:top_k * 2]):
            if score >= min_score:
                fragment = self.fragments[frag_idx].copy()
                fragment['score'] = float(score)
                fragment['rank'] = i + 1
                
                # Add original document information
                if fragment['original_doc_index'] < len(self.documents):
                    original_doc = self.documents[fragment['original_doc_index']]
                    fragment['original_title'] = original_doc.get('title', '')
                    fragment['original_authors'] = original_doc.get('authors', [])
                    fragment['original_arxiv_id'] = original_doc.get('arxiv_id', '')
                
                results.append(fragment)
        
        return results[:top_k]
    
    def _enhance_similarity_score(self, base_score, query_embedding, doc_embedding, frag_index=None):
        """Enhances base score with additional metrics"""
        enhanced_score = base_score
        
        # 1. Normalize to range [0, 1]
        enhanced_score = max(0, min(1, enhanced_score))
        
        # 2. Non-linear transformation to enhance differences
        if enhanced_score > 0.5:
            # Enhance high scores
            enhanced_score = 0.5 + (enhanced_score - 0.5) * 1.5
        else:
            # Reduce low scores
            enhanced_score = enhanced_score * 0.8
        
        # 3. Additional enhancement based on fragment length
        if frag_index is not None and frag_index < len(self.fragments):
            fragment = self.fragments[frag_index]
            text_length = fragment.get('fragment_length', 0)
            
            # Prefer medium-length fragments
            if 100 < text_length < 1000:
                enhanced_score *= 1.1
            elif text_length > 2000:
                enhanced_score *= 0.9
            
            # Bonus for first fragments (usually contain introduction)
            if fragment.get('fragment_index', 0) == 0:
                enhanced_score *= 1.05
        
        # 4. Consider semantic proximity through Euclidean distance
        euclidean_dist = np.linalg.norm(query_embedding - doc_embedding)
        euclidean_similarity = 1 / (1 + euclidean_dist / 100)  # Normalize
        enhanced_score = 0.7 * enhanced_score + 0.3 * euclidean_similarity
        
        return min(1.0, enhanced_score)  # Limit maximum to 1.0
    
    def get_statistics(self):
        """Gets storage statistics"""
        return {
            'total_documents': len(self.documents),
            'total_fragments': len(self.fragments),
            'embedding_model': self.model_name,
            'embedding_dimension': len(self.embeddings[0]) if self.embeddings else 0,
            'tfidf_features': self.tfidf_vectorizer.get_feature_names_out().shape[0] if self.tfidf_matrix is not None else 0,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'avg_fragments_per_doc': len(self.fragments) / len(self.documents) if self.documents else 0
        }
    
    def clear(self):
        """Clears storage"""
        self.documents = []
        self.fragments = []
        self.embeddings = []
        self.tfidf_matrix = None
        logger.info("Storage cleared")
    
    def save(self, filepath):
        """Saves storage"""
        data = {
            'documents': self.documents,
            'fragments': self.fragments,
            'embeddings': self.embeddings,
            'model_name': self.model_name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'tfidf_matrix': self.tfidf_matrix
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Storage saved to {filepath}")
    
    def load(self, filepath):
        """Loads storage"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.documents = data['documents']
        self.fragments = data.get('fragments', [])  # Backward compatibility
        self.embeddings = data['embeddings']
        self.model_name = data['model_name']
        self.chunk_size = data.get('chunk_size', 512)
        self.chunk_overlap = data.get('chunk_overlap', 50)
        self.tfidf_vectorizer = data['tfidf_vectorizer']
        self.tfidf_matrix = data['tfidf_matrix']
        
        # Reload model
        self.model = SentenceTransformer(self.model_name, cache_folder=self.cache_dir, use_auth_token=os.getenv("HUGGINGFACE_API_KEY"))
        
        logger.info(f"Storage loaded from {filepath}")
        logger.info(f"Loaded {len(self.documents)} documents, {len(self.fragments)} fragments")

def test_simple_huggingface():
    """Tests simple HuggingFace storage with fragmentation"""
    print("🧪 Testing SimpleHuggingFaceStore with fragmentation...")
    
    try:
        # Create storage
        store = SimpleHuggingFaceStore(chunk_size=200, chunk_overlap=20)
        print("✅ Storage created")
        
        # Test documents
        test_docs = [
            {
                'title': 'Machine Learning Basics',
                'abstract': 'Machine learning is a subset of artificial intelligence.',
                'full_text': 'Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves. This approach allows systems to automatically improve their performance through experience.'
            },
            {
                'title': 'Deep Learning Introduction',
                'abstract': 'Deep learning uses neural networks with multiple layers.',
                'full_text': 'Deep learning is a subset of machine learning that uses neural networks with multiple layers. These neural networks are designed to mimic the human brain and can process large amounts of data. They have been particularly successful in image recognition, natural language processing, and speech recognition tasks.'
            }
        ]
        
        # Add documents
        store.add_documents(test_docs)
        print("✅ Documents added")
        
        # Statistics
        stats = store.get_statistics()
        print(f"✅ Statistics: {stats}")
        
        # Test search
        results = store.search("machine learning", top_k=3, min_score=0.1)
        print(f"✅ Search completed, found {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"  {i+1}. Fragment {result.get('fragment_index', 0)} from '{result.get('title', 'Unknown')}' (score: {result.get('score', 0):.3f})")
            print(f"     Text: {result.get('fragment_text', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_huggingface() 