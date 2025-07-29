import requests
import streamlit as st

class APIClient:
    def __init__(self):
        #self.base_url = "http://backend:8000"  # Docker service name
        # Para desarrollo local: 
        self.base_url = "http://localhost:8000"
    
    def generate_content(self, params):
        try:
            response = requests.post(
                f"{self.base_url}/generate-content",
                json=params,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con la API: {str(e)}")
    
    def generate_popular_science_rag(self, params):
        try:
            # Подготавливаем параметры для нового API
            rag_params = {
                "topic": params.get("topic", ""),
                "language": params.get("language", "en"),
                "search_type": params.get("search_type", "hybrid"),
                "top_k": params.get("top_k", 8)
            }
            
            response = requests.post(
                f"{self.base_url}/generate-popular-science-rag",
                json=rag_params,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con la API: {str(e)}")
        
    def search_arxiv(self, params):
        try:
            response = requests.post(
                "http://localhost:8000/search-arxiv",
                json=params,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con la API: {str(e)}")
        
    def upsert_documents(self, docs):
        try:
            response = requests.post(
                f"{self.base_url}/upsert-documents",
                json={"docs": docs},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con la API: {str(e)}")

    def ask_rag(self, params):
        try:
            # Подготавливаем параметры для нового API
            question_params = {
                "question": params.get("question", ""),
                "search_type": params.get("search_type", "hybrid"),
                "top_k": params.get("top_k", 5)
            }
            
            response = requests.post(
                f"{self.base_url}/ask-rag",
                json=question_params,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con la API: {str(e)}")
    
    def get_rag_stats(self):
        """Получить статистику RAG системы"""
        try:
            response = requests.get(
                f"{self.base_url}/rag-stats",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con la API: {str(e)}")
    
    def clear_rag(self):
        """Очистить все документы из RAG"""
        try:
            response = requests.post(
                f"{self.base_url}/clear-rag",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con la API: {str(e)}")
    
    def load_arxiv_to_rag(self, params):
        """Загрузить статьи из arXiv в RAG"""
        try:
            response = requests.post(
                f"{self.base_url}/load-arxiv-to-rag",
                json=params,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión con la API: {str(e)}")