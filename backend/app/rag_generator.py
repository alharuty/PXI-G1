from groq import Groq
from typing import List, Dict, Optional
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class RAGGenerator:
    """RAG (Retrieval-Augmented Generation) system using Groq LLM"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize RAG generator with Groq client
        
        Args:
            api_key: Groq API key (if not provided, will use environment variable)
        """
        self.client = Groq(api_key=api_key)
        self.model = "gemma2-9b-it"
        
    def create_rag_prompt(self, query: str, retrieved_documents: List[Dict]) -> str:
        """
        Creates a RAG prompt combining user query with retrieved documents
        
        Args:
            query: User's original query
            retrieved_documents: List of retrieved document fragments
            
        Returns:
            Formatted prompt for LLM
        """
        # Start with system instruction
        prompt = """You are a helpful AI assistant that answers questions based on scientific articles from arXiv. 
Use the provided document fragments to answer the user's question accurately and comprehensively.

IMPORTANT: These are text fragments from scientific papers. Even if a fragment seems incomplete, 
if it contains relevant information that answers the user's question, use it to provide a complete answer.

If the documents don't contain enough information to answer the question, say so clearly.
Always cite the source articles when providing information.

Document fragments:
"""
        
        # Add retrieved documents
        for i, doc in enumerate(retrieved_documents, 1):
            prompt += f"\n--- Document {i} ---\n"
            prompt += f"Title: {doc.get('title', 'Unknown')}\n"
            prompt += f"Authors: {', '.join(doc.get('authors', []))}\n"
            prompt += f"arXiv ID: {doc.get('arxiv_id', 'Unknown')}\n"
            # Используем fragment_text для новых фрагментов или text_snippet для старых
            text_content = doc.get('fragment_text', doc.get('text_snippet', ''))
            prompt += f"Text: {text_content}\n"
        
        # Add user query
        prompt += f"\n\nUser Question: {query}\n\n"
        prompt += "Please provide a comprehensive answer based on the above documents:"
        
        return prompt
    
    def generate_rag_response(self, 
                            query: str, 
                            retrieved_documents: List[Dict],
                            temperature: float = 0.7,
                            max_tokens: int = 1024,
                            stream: bool = False) -> Dict:
        """
        Generates RAG response using Groq LLM
        
        Args:
            query: User's query
            retrieved_documents: Retrieved document fragments
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Create RAG prompt
            prompt = self.create_rag_prompt(query, retrieved_documents)
            
            logger.info(f"Generating RAG response for query: '{query}'")
            logger.info(f"Using {len(retrieved_documents)} document fragments")
            
            # Log retrieved documents for debugging
            print(f"\n📚 Retrieved documents for query '{query}':")
            for i, doc in enumerate(retrieved_documents, 1):
                print(f"  {i}. Title: {doc.get('title', 'Unknown')}")
                print(f"     Authors: {', '.join(doc.get('authors', []))}")
                print(f"     arXiv ID: {doc.get('arxiv_id', 'Unknown')}")
                print(f"     Score: {doc.get('score', 'N/A')}")
                # Используем fragment_text для новых фрагментов или text_snippet для старых
                text_content = doc.get('fragment_text', doc.get('text_snippet', ''))
                print(f"     Text: {text_content[:100]}...")
                print()
            
            # Generate response with Groq
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=stream,
                stop=None,
            )
            
            if stream:
                # Handle streaming response
                response_text = ""
                for chunk in completion:
                    content = chunk.choices[0].delta.content or ""
                    response_text += content
                
                return {
                    "response": response_text,
                    "query": query,
                    "documents_used": len(retrieved_documents),
                    "model": self.model,
                    "streamed": True
                }
            else:
                # Handle non-streaming response
                response_text = completion.choices[0].message.content
                
                return {
                    "response": response_text,
                    "query": query,
                    "documents_used": len(retrieved_documents),
                    "model": self.model,
                    "streamed": False,
                    "usage": {
                        "prompt_tokens": completion.usage.prompt_tokens,
                        "completion_tokens": completion.usage.completion_tokens,
                        "total_tokens": completion.usage.total_tokens
                    } if hasattr(completion, 'usage') else None
                }
                
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return {
                "error": str(e),
                "query": query,
                "documents_used": len(retrieved_documents),
                "model": self.model
            }
    
    def generate_rag_response_stream(self, 
                                   query: str, 
                                   retrieved_documents: List[Dict],
                                   temperature: float = 0.7,
                                   max_tokens: int = 1024):
        """
        Generates streaming RAG response using Groq LLM
        
        Args:
            query: User's query
            retrieved_documents: Retrieved document fragments
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Content chunks as they are generated
        """
        try:
            # Create RAG prompt
            prompt = self.create_rag_prompt(query, retrieved_documents)
            
            logger.info(f"Generating streaming RAG response for query: '{query}'")
            logger.info(f"Using {len(retrieved_documents)} document fragments")
            
            # Log retrieved documents for debugging
            print(f"\n📚 Retrieved documents for streaming query '{query}':")
            for i, doc in enumerate(retrieved_documents, 1):
                print(f"  {i}. Title: {doc.get('title', 'Unknown')}")
                print(f"     Authors: {', '.join(doc.get('authors', []))}")
                print(f"     arXiv ID: {doc.get('arxiv_id', 'Unknown')}")
                print(f"     Score: {doc.get('score', 'N/A')}")
                print(f"     Text snippet: {doc.get('text_snippet', '')[:100]}...")
                print()
            
            # Generate response with Groq
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=True,
                stop=None,
            )
            
            # Stream response
            for chunk in completion:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content
                    
        except Exception as e:
            logger.error(f"Error generating streaming RAG response: {e}")
            yield f"Error: {str(e)}"
    
    def analyze_retrieved_documents(self, query: str, retrieved_documents: List[Dict]) -> Dict:
        """
        Analyze retrieved documents for debugging
        
        Args:
            query: Original query
            retrieved_documents: List of retrieved documents
            
        Returns:
            Analysis of retrieved documents
        """
        analysis = {
            "query": query,
            "total_documents": len(retrieved_documents),
            "documents": [],
            "summary": {
                "avg_score": 0,
                "has_relevant_content": False,
                "topics_found": []
            }
        }
        
        if not retrieved_documents:
            analysis["summary"]["has_relevant_content"] = False
            return analysis
        
        scores = []
        topics = set()
        
        for i, doc in enumerate(retrieved_documents):
            # Используем fragment_text для новых фрагментов или text_snippet для старых
            text_content = doc.get('fragment_text', doc.get('text_snippet', ''))
            
            doc_analysis = {
                "index": i + 1,
                "title": doc.get('title', 'Unknown'),
                "authors": doc.get('authors', []),
                "arxiv_id": doc.get('arxiv_id', 'Unknown'),
                "score": doc.get('score', 0),
                "text_length": len(text_content),
                "text_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content,
                "relevance_to_query": "low"  # Will be updated based on content analysis
            }
            
            # Analyze relevance
            text_lower = text_content.lower()
            query_lower = query.lower()
            query_words = query_lower.split()
            
            # Check if query words appear in document
            matching_words = [word for word in query_words if word in text_lower]
            if matching_words:
                doc_analysis["relevance_to_query"] = "medium"
                if len(matching_words) >= len(query_words) * 0.5:
                    doc_analysis["relevance_to_query"] = "high"
            
            # Extract potential topics
            if "coulomb" in text_lower:
                topics.add("coulomb")
            if "branch" in text_lower:
                topics.add("branch")
            if "physics" in text_lower or "mathematical" in text_lower:
                topics.add("physics/mathematics")
            
            scores.append(doc.get('score', 0))
            analysis["documents"].append(doc_analysis)
        
        # Calculate summary
        analysis["summary"]["avg_score"] = sum(scores) / len(scores) if scores else 0
        analysis["summary"]["has_relevant_content"] = any(doc["relevance_to_query"] in ["medium", "high"] for doc in analysis["documents"])
        analysis["summary"]["topics_found"] = list(topics)
        
        return analysis
    
    def generate_simple_response(self, 
                               query: str,
                               temperature: float = 0.7,
                               max_tokens: int = 1024) -> Dict:
        """
        Generates simple response without RAG (for comparison)
        
        Args:
            query: User's query
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with response
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=False,
                stop=None,
            )
            
            response_text = completion.choices[0].message.content
            
            return {
                "response": response_text,
                "query": query,
                "model": self.model,
                "rag_enabled": False,
                "usage": {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens
                } if hasattr(completion, 'usage') else None
            }
            
        except Exception as e:
            logger.error(f"Error generating simple response: {e}")
            return {
                "error": str(e),
                "query": query,
                "model": self.model
            }


# Example usage
if __name__ == "__main__":
    import os
    
    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment variables")
        print("Please set your GROQ_API_KEY environment variable")
        exit(1)
    
    # Test RAG generator
    rag_gen = RAGGenerator(api_key=api_key)
    
    # Example query and documents
    query = "What is quantum computing?"
    documents = [
        {
            "title": "Introduction to Quantum Computing",
            "authors": ["John Doe"],
            "arxiv_id": "1234.5678",
            "text_snippet": "Quantum computing is a type of computation that harnesses the collective properties of quantum states to perform calculations."
        }
    ]
    
    print("🧪 Testing RAG Generator...")
    print(f"Query: {query}")
    print(f"Documents: {len(documents)}")
    
    # Generate RAG response
    response = rag_gen.generate_rag_response(query, documents)
    print("\n✅ RAG Response:")
    print(response.get('response', 'No response'))
    print(f"\n📊 Metadata:")
    print(f"  - Documents used: {response.get('documents_used', 0)}")
    print(f"  - Model: {response.get('model', 'Unknown')}")
    print(f"  - Streamed: {response.get('streamed', False)}") 